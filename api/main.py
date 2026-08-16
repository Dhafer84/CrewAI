"""Backend FastAPI — site de démos Qualité & Sécurité.

  GET /              → page de garde (catalogue d'outils)
  GET /qualitycrew   → démo d'audit ASPICE / ISO 26262
  GET /sentinelscan  → démo de veille de fuite d'information
  GET /hara          → SafetyScope, analyse HARA / ASIL
  GET /tara          → ThreatScope, analyse TARA / risque cybersécurité
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
from safetyscope.analysis import InvalidAnalysis, build_analysis  # noqa: E402
from safetyscope.asil import full_matrix  # noqa: E402
from safetyscope.core import suggest_hazards  # noqa: E402
from safetyscope.report import build_excel as build_hara_excel  # noqa: E402
from threatscope.analysis import InvalidAnalysis as InvalidTaraAnalysis  # noqa: E402
from threatscope.analysis import analysis_limits  # noqa: E402
from threatscope.analysis import build_analysis as build_tara_analysis  # noqa: E402
from threatscope.bridge import bridge_rule  # noqa: E402
from threatscope.core import suggest_threats  # noqa: E402
from threatscope.rating import full_scales  # noqa: E402
from threatscope.report import build_excel as build_tara_excel  # noqa: E402
from threatscope.treatment import treatment_scales  # noqa: E402

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


@app.get("/tara")
async def tara_page():
    return FileResponse(_SITE_DIR / "tara.html")


@app.get("/tara/scales")
async def tara_scales():
    """Barème de potentiel d'attaque + matrice de risque — source de vérité unique.

    Même contrat que /hara/matrix : la page charge une fois, puis fait ses
    lookups en local. `feasibilityByPotential` couvre chaque total possible
    pour qu'aucun seuil ne soit réécrit en JavaScript.

    La règle du pont HARA → TARA y est jointe pour la même raison : la page
    n'écrit nulle part que la sévérité se transfère et que l'exposition et la
    contrôlabilité ne se transfèrent pas — elle lit la règle et l'affiche.
    Simple composition : les deux moteurs restent indépendants.
    """
    scales = full_scales()
    scales["haraBridge"] = bridge_rule()
    scales["treatment"] = treatment_scales()
    scales["limits"] = analysis_limits()
    return scales


class TaraThreatPayload(BaseModel):
    description: str = ""
    path: str = ""
    time: int
    expertise: int
    knowledge: int
    window: int
    equipment: int
    decision: str = ""
    goal: str = ""
    rationale: str = ""


class TaraDamagePayload(BaseModel):
    asset: str = ""
    description: str = ""
    safety: int
    financial: int
    operational: int
    privacy: int
    threats: list[TaraThreatPayload] = []
    origin: str = ""
    origin_severity: int = -1
    origin_asil: str = ""


class TaraReportRequest(BaseModel):
    item: str = ""
    damages: list[TaraDamagePayload] = []


@app.post("/tara/report")
async def tara_report_create(request: Request, payload: TaraReportRequest):
    """Reconstruit le dossier côté serveur, puis prépare le classeur.

    Le tableau vient du navigateur : cotations revalidées, et complétude des
    traitements **recalculée** — l'indicateur de la page est une commodité
    d'affichage, pas une source de vérité. Un dossier incomplet n'est pas
    refusé pour autant : le classeur dit ce qui manque.
    """
    try:
        analysis = build_tara_analysis(payload.item, payload.damages)
    except InvalidTaraAnalysis as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    excel = await asyncio.to_thread(build_tara_excel, analysis)
    report_id = _store_report(
        _client_key(request),
        "tara",
        excel,
        "threatscope_" + analysis.created_at.strftime("%Y%m%d_%H%M") + ".xlsx",
    )
    return {"report_id": report_id}


@app.get("/tara/report/{report_id}.xlsx")
async def tara_report_download(request: Request, report_id: str):
    return _serve_report(
        request, report_id, "tara",
        "Rapport expiré ou introuvable. Relancez l'export.",
    )


class HaraEventPayload(BaseModel):
    malfunction: str = ""
    situation: str = ""
    severity: int
    exposure: int
    controllability: int


class HaraReportRequest(BaseModel):
    item: str = ""
    events: list[HaraEventPayload] = []


@app.post("/hara/report")
async def hara_report_create(request: Request, payload: HaraReportRequest):
    """Reconstruit l'analyse côté serveur, puis prépare le classeur.

    Le tableau vient du navigateur : il est revalidé intégralement avant
    d'être écrit.
    """
    try:
        analysis = build_analysis(payload.item, payload.events)
    except InvalidAnalysis as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    excel = await asyncio.to_thread(build_hara_excel, analysis)
    report_id = _store_report(
        _client_key(request),
        "hara",
        excel,
        "safetyscope_" + analysis.created_at.strftime("%Y%m%d_%H%M") + ".xlsx",
    )
    return {"report_id": report_id}


@app.get("/hara/report/{report_id}.xlsx")
async def hara_report_download(request: Request, report_id: str):
    return _serve_report(
        request, report_id, "hara",
        "Rapport expiré ou introuvable. Relancez l'export.",
    )


# --------------------------------------------------------------------------
# SafetyScope — proposition d'événements redoutés (optionnelle)
#
# Seule partie de l'outil qui appelle un LLM. Elle amorce la réflexion ;
# elle ne cote jamais S, E ni C.
# --------------------------------------------------------------------------

_suggest_semaphore = asyncio.Semaphore(1)
_SUGGEST_COOLDOWN_SECONDS = 60
_MAX_SUGGESTIONS_PER_DAY = 100
_last_suggest_by_client: dict[str, float] = {}
_suggest_daily_usage = {"day": None, "count": 0}


class HaraSuggestRequest(BaseModel):
    item: str = ""


def _suggest_refusal(client: str) -> str | None:
    now = time.time()

    today = datetime.now(timezone.utc).date()
    if _suggest_daily_usage["day"] != today:
        _suggest_daily_usage["day"] = today
        _suggest_daily_usage["count"] = 0

    if _suggest_daily_usage["count"] >= _MAX_SUGGESTIONS_PER_DAY:
        return "Quota quotidien de la démonstration atteint. Réessayez demain."

    for key, stamp in list(_last_suggest_by_client.items()):
        if now - stamp > _SUGGEST_COOLDOWN_SECONDS:
            del _last_suggest_by_client[key]

    last = _last_suggest_by_client.get(client)
    if last is not None:
        wait = int(_SUGGEST_COOLDOWN_SECONDS - (now - last))
        return f"Une proposition par minute. Réessayez dans {wait} s."

    return None


@app.post("/hara/suggest")
async def hara_suggest_prepare(request: Request, payload: HaraSuggestRequest):
    """Valide l'item et rend un jeton — l'intitulé ne passe pas par une URL."""
    client = _client_key(request)

    refusal = _suggest_refusal(client)
    if refusal:
        return JSONResponse({"error": refusal}, status_code=429)

    item = payload.item.strip()[:120]
    if len(item) < 3:
        return JSONResponse(
            {"error": "Décrivez l'item étudié en quelques mots avant de lancer la proposition."},
            status_code=400,
        )

    return {"token": _issue_token(client, "suggest", {"item": item})}


@app.get("/hara/suggest/stream")
async def hara_suggest_stream(request: Request, t: str = ""):
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()
    client = _client_key(request)
    step = [0]

    def task_callback(_task_output):
        step[0] += 1
        loop.call_soon_threadsafe(queue.put_nowait, json.dumps({
            "type": "step_done", "index": step[0] - 1, "total": 2,
        }))

    async def run():
        try:
            payload = _consume_token(t, client, "suggest")
            if payload is None:
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "Session expirée. Relancez depuis la page.",
                }))
                return

            refusal = _suggest_refusal(client)
            if refusal:
                await queue.put(json.dumps({"type": "error", "message": refusal}))
                return

            if _suggest_semaphore.locked():
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "Une proposition est déjà en cours. Réessayez dans un instant.",
                }))
                return

            async with _suggest_semaphore:
                _last_suggest_by_client[client] = time.time()
                _suggest_daily_usage["count"] += 1
                require_llm_key()

                await queue.put(json.dumps({"type": "start"}))
                suggestions = await asyncio.to_thread(
                    suggest_hazards, payload["item"], task_callback
                )
                await queue.put(json.dumps({
                    "type": "done",
                    "suggestions": [
                        {"malfunction": s.malfunction, "situation": s.situation}
                        for s in suggestions
                    ],
                }))
        except Exception:
            await queue.put(json.dumps({
                "type": "error",
                "message": "La proposition a échoué. Vous pouvez saisir les événements à la main.",
            }))
        finally:
            await queue.put(None)

    asyncio.create_task(run())
    return _sse_response(request, queue, timeout=180.0)


# --------------------------------------------------------------------------
# ThreatScope — proposition de scénarios de menace (optionnelle)
#
# Même limiteur que SafetyScope, délibérément : les deux puisent dans le
# **même quota Groq gratuit**. Deux compteurs séparés donneraient le double
# d'appels sur une seule enveloppe.
#
# La proposition est contextuelle — un actif et une conséquence redoutée
# précis — parce qu'un balayage STRIDE hors contexte ne produit que des
# généralités.
# --------------------------------------------------------------------------

class TaraSuggestRequest(BaseModel):
    item: str = ""
    asset: str = ""
    damage: str = ""


@app.post("/tara/suggest")
async def tara_suggest_prepare(request: Request, payload: TaraSuggestRequest):
    """Valide le contexte et rend un jeton — rien ne passe par une URL."""
    client = _client_key(request)

    refusal = _suggest_refusal(client)
    if refusal:
        return JSONResponse({"error": refusal}, status_code=429)

    contexte = {
        "item": payload.item.strip()[:120],
        "asset": payload.asset.strip()[:300],
        "damage": payload.damage.strip()[:300],
    }
    if len(contexte["asset"]) < 3 and len(contexte["damage"]) < 3:
        return JSONResponse(
            {"error": "Décrivez l'actif ou la conséquence redoutée avant de lancer "
                      "la proposition."},
            status_code=400,
        )

    return {"token": _issue_token(client, "tara-suggest", contexte)}


@app.get("/tara/suggest/stream")
async def tara_suggest_stream(request: Request, t: str = ""):
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()
    client = _client_key(request)
    step = [0]

    def task_callback(_task_output):
        step[0] += 1
        loop.call_soon_threadsafe(queue.put_nowait, json.dumps({
            "type": "step_done", "index": step[0] - 1, "total": 2,
        }))

    async def run():
        try:
            payload = _consume_token(t, client, "tara-suggest")
            if payload is None:
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "Session expirée. Relancez depuis la page.",
                }))
                return

            refusal = _suggest_refusal(client)
            if refusal:
                await queue.put(json.dumps({"type": "error", "message": refusal}))
                return

            if _suggest_semaphore.locked():
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "Une proposition est déjà en cours. Réessayez dans un instant.",
                }))
                return

            async with _suggest_semaphore:
                _last_suggest_by_client[client] = time.time()
                _suggest_daily_usage["count"] += 1
                require_llm_key()

                await queue.put(json.dumps({"type": "start"}))
                suggestions = await asyncio.to_thread(
                    suggest_threats,
                    payload["item"], payload["asset"], payload["damage"], task_callback,
                )
                await queue.put(json.dumps({
                    "type": "done",
                    "suggestions": [
                        {"threat": s.threat, "path": s.path} for s in suggestions
                    ],
                }))
        except Exception:
            await queue.put(json.dumps({
                "type": "error",
                "message": "La proposition a échoué. Vous pouvez saisir les menaces à la main.",
            }))
        finally:
            await queue.put(None)

    asyncio.create_task(run())
    return _sse_response(request, queue, timeout=180.0)


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

_TOKEN_TTL_SECONDS = 60
_tokens: dict[str, dict] = {}


def _prune_tokens(now: float) -> None:
    for token, entry in list(_tokens.items()):
        if now - entry["created"] > _TOKEN_TTL_SECONDS:
            del _tokens[token]


def _issue_token(client: str, kind: str, payload: dict) -> str:
    now = time.time()
    _prune_tokens(now)
    token = secrets.token_urlsafe(18)
    _tokens[token] = {
        "client": client, "kind": kind, "payload": payload, "created": now,
    }
    return token


def _consume_token(token: str, client: str, kind: str) -> dict | None:
    """Retire le jeton et rend sa charge utile, ou None s'il est invalide.

    Usage unique : un rejeu emprunte la même branche qu'un jeton inconnu.
    """
    _prune_tokens(time.time())
    entry = _tokens.pop(token, None)
    if entry is None or entry["client"] != client or entry["kind"] != kind:
        return None
    return entry["payload"]


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

    token = _issue_token(client, "scan", {"keywords": keywords})
    return {"token": token, "keywords": keywords}


# --------------------------------------------------------------------------
# Rapports Excel — stockage commun aux outils
#
# Un classeur porte des données de travail (termes recherchés, URL détectées,
# cotation d'une analyse). Il est gardé en mémoire seulement, avec une durée
# de vie courte, et n'est servi qu'au client qui l'a produit. Rien n'est
# écrit sur disque.
# --------------------------------------------------------------------------

_REPORT_TTL_SECONDS = 1800
_MAX_STORED_REPORTS = 20
_XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

_reports: dict[str, dict] = {}


def _prune_reports(now: float) -> None:
    for report_id, entry in list(_reports.items()):
        if now - entry["created"] > _REPORT_TTL_SECONDS:
            del _reports[report_id]

    excess = len(_reports) - _MAX_STORED_REPORTS
    if excess > 0:
        oldest = sorted(_reports.items(), key=lambda kv: kv[1]["created"])
        for report_id, _ in oldest[:excess]:
            del _reports[report_id]


def _store_report(client: str, kind: str, data: bytes, filename: str) -> str:
    now = time.time()
    _prune_reports(now)
    report_id = secrets.token_urlsafe(18)
    _reports[report_id] = {
        "client": client,
        "kind": kind,
        "data": data,
        "filename": filename,
        "created": now,
    }
    return report_id


def _serve_report(request: Request, report_id: str, kind: str, missing_message: str):
    """Sert un rapport à son propriétaire.

    `kind` cloisonne les outils : une route ne rend que les rapports qu'elle
    est censée produire, même si le stockage est commun.
    """
    _prune_reports(time.time())

    entry = _reports.get(report_id)
    if (
        entry is None
        or entry["client"] != _client_key(request)
        or entry["kind"] != kind
    ):
        return JSONResponse({"error": missing_message}, status_code=404)

    return Response(
        content=entry["data"],
        media_type=_XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": f'attachment; filename="{entry["filename"]}"',
            "Cache-Control": "no-store",
        },
    )


@app.get("/scan/report/{report_id}.xlsx")
async def scan_report(request: Request, report_id: str):
    return _serve_report(
        request, report_id, "scan",
        "Rapport expiré ou introuvable. Relancez un scan.",
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
            payload = _consume_token(t, client, "scan")
            if payload is None:
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "Session de scan expirée. Relancez depuis la page.",
                }))
                return

            keywords = payload["keywords"]

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
                report_id = _store_report(
                    client,
                    "scan",
                    excel,
                    "sentinelscan_"
                    + result.started_at.strftime("%Y%m%d_%H%M")
                    + ".xlsx",
                )

                await queue.put(json.dumps({
                    "type": "done",
                    "counts": result.count_by_criticality(),
                    "findings": len(result.findings),
                    "duration": round(result.duration_seconds),
                    "report": build_markdown(result),
                    "report_id": report_id,
                    "incomplete": len(result.incomplete_queries),
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
