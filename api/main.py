"""Backend FastAPI — site de démos Qualité & Sécurité.

  GET /              → page de garde (catalogue d'outils)
  GET /qualitycrew   → démo d'audit ASPICE / ISO 26262
  GET /sentinelscan  → démo de veille de fuite d'information
  GET /audit/stream  → SSE : progression des agents + rapport final
  GET /scan/stream   → SSE : progression du scan + rapport final
  GET /static/*      → assets CSS

Enveloppe mince : aucune logique métier ici, tout est dans src/.

Une exécution à la fois par outil (Semaphore). L'audit tourne toujours sur
data/sample_project/ ; le scan prend des mots-clés fournis par l'utilisateur.
"""

import asyncio
import hashlib
import json
import logging
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from qualitycrew.config import require_llm_key  # noqa: E402
from qualitycrew.core import run_audit  # noqa: E402
from sentinelscan.config import require_github_token  # noqa: E402
from sentinelscan.queries import InvalidKeyword, normalize_keywords  # noqa: E402
from sentinelscan.report import build_excel, build_markdown  # noqa: E402
from sentinelscan.scanner import run_scan  # noqa: E402
from safetyscope.asil import full_matrix  # noqa: E402

_DOCUMENTS_DIR = _ROOT / "data" / "sample_project"
_SITE_DIR = _ROOT / "site"

app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(_SITE_DIR)), name="static")


class _RedactScanKeywords(logging.Filter):
    """Retire la query string de /scan/stream du journal d'accès.

    Les mots-clés ne transitent plus par l'URL (ils passent en POST), mais on
    garde ce filtre pour que le jeton de session n'apparaisse pas non plus.
    Le journal garde la trace de l'appel, pas de son contenu.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) >= 3:
            path = args[2]
            if isinstance(path, str) and path.startswith("/scan/stream"):
                record.args = args[:2] + ("/scan/stream",) + args[3:]
        return True


logging.getLogger("uvicorn.access").addFilter(_RedactScanKeywords())

_audit_semaphore = asyncio.Semaphore(1)
_scan_semaphore = asyncio.Semaphore(1)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

@app.get("/")
async def index():
    return FileResponse(_SITE_DIR / "index.html")


@app.get("/qualitycrew")
async def qualitycrew_page():
    return FileResponse(_SITE_DIR / "qualitycrew.html")


@app.get("/sentinelscan")
async def sentinelscan_page():
    return FileResponse(_SITE_DIR / "sentinelscan.html")


@app.get("/hara")
async def hara_page():
    return FileResponse(_SITE_DIR / "hara.html")


@app.get("/hara/matrix")
async def hara_matrix():
    """Table ASIL complète — source de vérité unique.

    La page la charge une fois puis fait ses lookups en local : la cotation
    reste instantanée sans que la logique soit dupliquée en JavaScript.
    """
    return full_matrix()


# --------------------------------------------------------------------------
# Plomberie SSE commune
# --------------------------------------------------------------------------

def _sse_response(request: Request, queue: "asyncio.Queue[str | None]", timeout: float):
    """Transforme une file d'événements JSON en flux SSE.

    `None` dans la file signale la fin du traitement.
    """

    async def event_gen():
        while True:
            if await request.is_disconnected():
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                yield 'data: {"type":"error","message":"Délai dépassé."}\n\n'
                break
            if item is None:
                yield 'data: {"type":"close"}\n\n'
                break
            yield f"data: {item}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --------------------------------------------------------------------------
# QualityCrew — audit
# --------------------------------------------------------------------------

@app.get("/audit/stream")
async def audit_stream(request: Request):
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()
    task_index = [0]

    def task_callback(task_output):
        idx = task_index[0]
        task_index[0] += 1
        loop.call_soon_threadsafe(queue.put_nowait, json.dumps({
            "type": "task_done",
            "index": idx,
            "agent": task_output.agent,
            "output": task_output.raw,
        }))

    async def run():
        if _audit_semaphore.locked():
            await queue.put(json.dumps({
                "type": "error",
                "message": "Un audit est déjà en cours. Réessayez dans quelques instants.",
            }))
            await queue.put(None)
            return

        async with _audit_semaphore:
            try:
                await queue.put(json.dumps({"type": "start"}))
                require_llm_key()
                report = await asyncio.to_thread(
                    run_audit, _DOCUMENTS_DIR, None, task_callback
                )
                await queue.put(json.dumps({"type": "done", "report": report}))
            except Exception:
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "L'audit a échoué. Vérifiez la clé API et relancez.",
                }))
            finally:
                await queue.put(None)

    asyncio.create_task(run())
    return _sse_response(request, queue, timeout=180.0)


# --------------------------------------------------------------------------
# SentinelScan — rate limiting
# --------------------------------------------------------------------------

_SCAN_COOLDOWN_SECONDS = 180
_MAX_SCANS_PER_DAY = 50

# Les IP ne sont jamais conservées en clair : on n'indexe que leur empreinte,
# suffisante pour limiter la cadence. Rien n'est persisté sur disque, et les
# mots-clés recherchés ne sont jamais journalisés.
_last_scan_by_client: dict[str, float] = {}
_daily_usage = {"day": None, "count": 0}


def _client_key(request: Request) -> str:
    header = request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for")
    raw = header.split(",")[0].strip() if header else (
        request.client.host if request.client else "unknown"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _rate_limit_message(client: str) -> str | None:
    """Retourne le motif de refus, ou None si le scan peut démarrer."""
    now = time.time()

    today = datetime.now(timezone.utc).date()
    if _daily_usage["day"] != today:
        _daily_usage["day"] = today
        _daily_usage["count"] = 0

    if _daily_usage["count"] >= _MAX_SCANS_PER_DAY:
        return (
            "Quota quotidien de la démonstration atteint — l'API GitHub est "
            "limitée. Réessayez demain."
        )

    # Purge des entrées expirées : la table ne grossit pas indéfiniment.
    for key, stamp in list(_last_scan_by_client.items()):
        if now - stamp > _SCAN_COOLDOWN_SECONDS:
            del _last_scan_by_client[key]

    last = _last_scan_by_client.get(client)
    if last is not None:
        wait = int(_SCAN_COOLDOWN_SECONDS - (now - last))
        return f"Un scan toutes les 3 minutes. Réessayez dans {wait} s."

    return None


def _register_scan(client: str) -> None:
    _last_scan_by_client[client] = time.time()
    _daily_usage["count"] += 1


# --------------------------------------------------------------------------
# SentinelScan — jeton de session
#
# Les mots-clés ne transitent JAMAIS par une URL : ils sont postés, échangés
# contre un jeton opaque à usage unique, et c'est ce jeton qui ouvre le flux
# SSE. Un terme recherché est potentiellement un nom d'entreprise — il n'a
# donc rien à faire dans les journaux nginx, l'historique du navigateur ou
# l'en-tête Referer.
# --------------------------------------------------------------------------

_SCAN_TOKEN_TTL_SECONDS = 60
_scan_tokens: dict[str, dict] = {}


def _prune_tokens(now: float) -> None:
    for token, entry in list(_scan_tokens.items()):
        if now - entry["created"] > _SCAN_TOKEN_TTL_SECONDS:
            del _scan_tokens[token]


class ScanRequest(BaseModel):
    keywords: list[str] = []


@app.post("/scan/prepare")
async def scan_prepare(request: Request, payload: ScanRequest):
    """Valide les mots-clés et rend un jeton à usage unique."""
    client = _client_key(request)

    refusal = _rate_limit_message(client)
    if refusal:
        return JSONResponse({"error": refusal}, status_code=429)

    try:
        keywords = normalize_keywords(payload.keywords)
    except InvalidKeyword as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    now = time.time()
    _prune_tokens(now)

    token = secrets.token_urlsafe(18)
    _scan_tokens[token] = {"client": client, "keywords": keywords, "created": now}
    return {"token": token, "keywords": keywords}


# --------------------------------------------------------------------------
# SentinelScan — rapports Excel
#
# Le classeur contient les termes recherchés et les URL détectées : il est
# gardé en mémoire seulement, avec une durée de vie courte, et n'est servi
# qu'au client qui a lancé le scan. Rien n'est écrit sur disque.
# --------------------------------------------------------------------------

_REPORT_TTL_SECONDS = 1800
_MAX_STORED_REPORTS = 20
_XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

_scan_reports: dict[str, dict] = {}


def _prune_reports(now: float) -> None:
    for report_id, entry in list(_scan_reports.items()):
        if now - entry["created"] > _REPORT_TTL_SECONDS:
            del _scan_reports[report_id]

    excess = len(_scan_reports) - _MAX_STORED_REPORTS
    if excess > 0:
        oldest = sorted(_scan_reports.items(), key=lambda kv: kv[1]["created"])
        for report_id, _ in oldest[:excess]:
            del _scan_reports[report_id]


@app.get("/scan/report/{report_id}.xlsx")
async def scan_report(request: Request, report_id: str):
    _prune_reports(time.time())

    entry = _scan_reports.get(report_id)
    if entry is None or entry["client"] != _client_key(request):
        return JSONResponse(
            {"error": "Rapport expiré ou introuvable. Relancez un scan."},
            status_code=404,
        )

    return Response(
        content=entry["data"],
        media_type=_XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": f'attachment; filename="{entry["filename"]}"',
            "Cache-Control": "no-store",
        },
    )


# --------------------------------------------------------------------------
# SentinelScan — scan
# --------------------------------------------------------------------------

@app.get("/scan/stream")
async def scan_stream(request: Request, t: str = ""):
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def progress_callback(event: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, json.dumps(event))

    client = _client_key(request)

    async def run():
        try:
            _prune_tokens(time.time())
            # Jeton à usage unique : consommé dès la première lecture.
            entry = _scan_tokens.pop(t, None)
            if entry is None or entry["client"] != client:
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "Session de scan expirée. Relancez depuis la page.",
                }))
                return

            keywords = entry["keywords"]

            refusal = _rate_limit_message(client)
            if refusal:
                await queue.put(json.dumps({"type": "error", "message": refusal}))
                return

            if _scan_semaphore.locked():
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "Un scan est déjà en cours. Réessayez dans un instant.",
                }))
                return

            async with _scan_semaphore:
                _register_scan(client)
                require_github_token()

                await queue.put(json.dumps({"type": "start", "keywords": keywords}))
                result = await asyncio.to_thread(run_scan, keywords, progress_callback)

                excel = await asyncio.to_thread(build_excel, result)
                now = time.time()
                _prune_reports(now)
                report_id = secrets.token_urlsafe(18)
                _scan_reports[report_id] = {
                    "client": client,
                    "data": excel,
                    "filename": (
                        "sentinelscan_"
                        + result.started_at.strftime("%Y%m%d_%H%M")
                        + ".xlsx"
                    ),
                    "created": now,
                }

                await queue.put(json.dumps({
                    "type": "done",
                    "counts": result.count_by_criticality(),
                    "findings": len(result.findings),
                    "duration": round(result.duration_seconds),
                    "report": build_markdown(result),
                    "report_id": report_id,
                }))
        except RuntimeError as exc:
            # Jeton GitHub absent : message explicite, pas de trace technique.
            await queue.put(json.dumps({"type": "error", "message": str(exc)}))
        except Exception:
            await queue.put(json.dumps({
                "type": "error",
                "message": "Le scan a échoué. Réessayez dans quelques instants.",
            }))
        finally:
            await queue.put(None)

    asyncio.create_task(run())
    return _sse_response(request, queue, timeout=240.0)
