"""Backend FastAPI — site de démos Qualité & Sécurité.

  GET /              → page de garde (catalogue d'outils)
  GET /qualitycrew   → démo d'audit ASPICE / ISO 26262
  GET /sentinelscan  → démo de veille de fuite d'information
  GET /hara          → SafetyScope, analyse HARA / ASIL
  GET /tara          → ThreatScope, analyse TARA / risque cybersécurité
  GET /regwatch      → RegWatch, veille de signaux publics autour des normes
  GET /audit/stream  → SSE : progression des agents + rapport final
  GET /watch/stream  → SSE : progression de la veille + signaux retenus
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
from datetime import date, datetime, timezone
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

from qualitycrew.config import is_daily_quota, require_llm_key  # noqa: E402
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
from regwatch.core import WatchItem, WatchResult, run_watch  # noqa: E402
from regwatch.explain import explain_items  # noqa: E402
from regwatch.report import build_excel as build_watch_excel  # noqa: E402
from regwatch.norms import InvalidSelection, parse_selection  # noqa: E402
from regwatch.sources import source_catalog  # noqa: E402

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

# Les flux SSE rendent un message neutre au visiteur ; la cause réelle doit
# rester quelque part, sinon une panne est indiagnosticable (vécu le
# 20/08/2026 : Groq avait retiré le modèle, le site disait « vérifiez la clé »).
_log = logging.getLogger("qualitycrew")

# Un quota quotidien épuisé n'est pas une panne : le dire franchement vaut mieux
# qu'un « réessayez » qui ne marchera pas avant demain. Et c'est l'occasion de
# rappeler que deux outils du site ne dépendent d'aucune IA.
_QUOTA_MESSAGE = (
    "Le quota quotidien de l'API gratuite est atteint — la démonstration "
    "repartira demain. SafetyScope et ThreatScope, eux, ne font appel à aucune "
    "IA pour coter : ils restent pleinement utilisables."
)


def _failure_message(exc: BaseException, defaut: str) -> str:
    """Nommer le quota quand c'est lui, rester sobre sinon."""
    return _QUOTA_MESSAGE if is_daily_quota(exc) else defaut

_audit_semaphore = asyncio.Semaphore(1)
_scan_semaphore = asyncio.Semaphore(1)
_watch_semaphore = asyncio.Semaphore(1)


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


@app.get("/regwatch")
async def regwatch_page():
    return FileResponse(_SITE_DIR / "regwatch.html")


@app.get("/regwatch/sources")
async def regwatch_sources():
    """Catalogue des normes et des sources — source de vérité unique.

    Même contrat que `/hara/matrix` et `/tara/scales` : la page lit ce
    catalogue et l'affiche. Elle ne réécrit ni les libellés de normes, ni les
    paliers de fiabilité, ni la fenêtre de veille — ajouter une source la
    rend visible sans toucher au HTML.
    """
    return source_catalog()


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
        except Exception as exc:
            _log.exception("Proposition HARA interrompue")
            await queue.put(json.dumps({
                "type": "error",
                "message": _failure_message(
                    exc, "La proposition a échoué. Vous pouvez saisir les événements à la main."),
            }))
        finally:
            await queue.put(None)

    tache = asyncio.create_task(run())
    return _sse_response(request, queue, timeout=180.0, task=tache)


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
        except Exception as exc:
            _log.exception("Proposition TARA interrompue")
            await queue.put(json.dumps({
                "type": "error",
                "message": _failure_message(
                    exc, "La proposition a échoué. Vous pouvez saisir les menaces à la main."),
            }))
        finally:
            await queue.put(None)

    tache = asyncio.create_task(run())
    return _sse_response(request, queue, timeout=180.0, task=tache)


# --------------------------------------------------------------------------
# Plomberie SSE commune
# --------------------------------------------------------------------------

# ⚠️ Un battement régulier est indispensable, pas décoratif.
#
# Le délai passé à `_sse_response` n'est pas un budget total : c'est l'attente
# **entre deux événements**. Une tâche longue ne produit rien pendant qu'elle
# travaille, et ce silence casse la chaîne à deux endroits :
#   - nginx coupe une connexion inactive (`proxy_read_timeout`, 60 s par défaut)
#   - le navigateur reste figé sur l'agent en cours, sans erreur nulle part
#
# Vécu le 20/08/2026 : l'audit semblait « bloqué au détecteur de risques »,
# et le journal du service était vide — parce qu'il n'y avait aucune exception.
# Un commentaire SSE (`: ligne`) ne déclenche aucun événement côté client mais
# garde le tuyau vivant.
_HEARTBEAT_SECONDS = 15.0


def _sse_response(
    request: Request,
    queue: "asyncio.Queue[str | None]",
    timeout: float,
    task: "asyncio.Task | None" = None,
):
    """Transforme une file d'événements JSON en flux SSE.

    `None` dans la file signale la fin du traitement. `timeout` est le silence
    **total** toléré ; le battement, lui, part toutes les `_HEARTBEAT_SECONDS`.

    `task` est le traitement de fond : on l'annule si le client s'en va, sinon
    il continue de tourner pour un résultat que plus personne n'attend — et sur
    une API à quota, ça se paie.
    """

    async def event_gen():
        silence = 0.0
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), _HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    silence += _HEARTBEAT_SECONDS
                    if silence >= timeout:
                        yield 'data: {"type":"error","message":"Délai dépassé."}\n\n'
                        break
                    yield ": battement\n\n"
                    continue
                silence = 0.0
                if item is None:
                    yield 'data: {"type":"close"}\n\n'
                    break
                yield f"data: {item}\n\n"
        finally:
            if task is not None and not task.done():
                task.cancel()

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
            except Exception as exc:
                _log.exception("Audit interrompu")
                await queue.put(json.dumps({
                    "type": "error",
                    "message": _failure_message(
                        exc, "L'audit n'a pas abouti. Réessayez dans un instant."),
                }))
            finally:
                await queue.put(None)

    tache = asyncio.create_task(run())
    return _sse_response(request, queue, timeout=420.0, task=tache)


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
            _log.exception("Scan interrompu")
            await queue.put(json.dumps({
                "type": "error",
                "message": "Le scan a échoué. Réessayez dans quelques instants.",
            }))
        finally:
            await queue.put(None)

    tache = asyncio.create_task(run())
    return _sse_response(request, queue, timeout=240.0, task=tache)

# --------------------------------------------------------------------------
# RegWatch — veille de signaux publics autour des normes
#
# ⚠️ **Pas de POST + jeton ici, et c'est délibéré.** SentinelScan échange ses
# mots-clés contre un jeton opaque parce qu'un terme recherché est
# potentiellement un nom d'entreprise, qui n'a rien à faire dans un journal
# nginx. Les normes surveillées, elles, sont un énumérable fermé de cinq
# référentiels publics : il n'y a rien à protéger. Recopier le mécanisme
# serait du culte du cargo.
#
# La cadence est plus souple que celle du scan (1/min contre 1/3 min) parce
# que le moteur garde 30 min de cache par URL : une seconde veille dans la
# demi-heure ne touche pas le réseau du tout. Le limiteur sert à empêcher
# qu'un visiteur monopolise l'unique exécution, et à borner le trafic sortant
# d'une IP de datacenter unique.
# --------------------------------------------------------------------------

_WATCH_COOLDOWN_SECONDS = 60
_MAX_WATCHES_PER_DAY = 200
_last_watch_by_client: dict[str, float] = {}
_watch_daily_usage = {"day": None, "count": 0}


def _watch_refusal(client: str) -> str | None:
    now = time.time()

    today = datetime.now(timezone.utc).date()
    if _watch_daily_usage["day"] != today:
        _watch_daily_usage["day"] = today
        _watch_daily_usage["count"] = 0

    if _watch_daily_usage["count"] >= _MAX_WATCHES_PER_DAY:
        return "Quota quotidien de la démonstration atteint. Réessayez demain."

    for key, stamp in list(_last_watch_by_client.items()):
        if now - stamp > _WATCH_COOLDOWN_SECONDS:
            del _last_watch_by_client[key]

    last = _last_watch_by_client.get(client)
    if last is not None:
        wait = int(_WATCH_COOLDOWN_SECONDS - (now - last))
        return f"Une veille par minute. Réessayez dans {wait} s."

    return None


def _watch_payload(result) -> dict:
    """Charge utile de l'événement `done`, servie à site/regwatch.html.

    Extrait de la route **pour être testable sans réseau** : ouvrir le flux
    lancerait une vraie veille sur sept sites tiers, ce qu'aucun test ne doit
    faire. Un oubli de clé ici casse la page sans qu'aucun test de moteur ne
    bouge — c'est arrivé avec `norms`, absent de cette charge utile alors que
    la page en fait ses sections et ses filtres.
    """
    return {
        "type": "done",
        # La sélection, dans l'ordre du catalogue : la page en tire ses
        # sections et ses filtres, y compris pour une norme sans aucun signal.
        "norms": result.norms,
        "duration": round(result.duration_seconds),
        "lookbackDays": result.lookback_days,
        "sourcesRead": result.sources_read,
        "sourcesTotal": result.sources_total,
        "countsByNorm": result.count_by_norm(),
        "countsBySignal": result.count_by_signal(),
        # ⚠️ La couverture fait partie du résultat, pas des notes de bas de
        # page : une source muette ne doit jamais se présenter comme une
        # source calme.
        "unreachable": result.unreachable,
        "degraded": result.degraded,
        "undated": result.undated,
        "errors": result.errors,
        "items": [
            {
                "norm": item.norm_key,
                "normLabel": item.norm_label,
                "signal": item.signal,
                "title": item.title,
                "published": item.published.isoformat(),
                "source": item.source_label,
                "tier": item.source_tier,
                "url": item.url,
            }
            for item in result.items
        ],
    }


@app.get("/watch/stream")
async def watch_stream(request: Request, norms: str = ""):
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()
    client = _client_key(request)

    def progress_callback(event: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, json.dumps(event))

    async def run():
        try:
            try:
                selection = parse_selection(
                    [key for key in norms.split(",") if key.strip()]
                )
            except InvalidSelection as exc:
                await queue.put(json.dumps({"type": "error", "message": str(exc)}))
                return

            refusal = _watch_refusal(client)
            if refusal:
                await queue.put(json.dumps({"type": "error", "message": refusal}))
                return

            if _watch_semaphore.locked():
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "Une veille est déjà en cours. Réessayez dans un instant.",
                }))
                return

            async with _watch_semaphore:
                _last_watch_by_client[client] = time.time()
                _watch_daily_usage["count"] += 1

                await queue.put(json.dumps({
                    "type": "start",
                    "norms": [norm.key for norm in selection],
                }))
                result = await asyncio.to_thread(
                    run_watch, selection, progress_callback
                )

                await queue.put(json.dumps(_watch_payload(result)))
        except Exception:
            _log.exception("Veille interrompue")
            await queue.put(json.dumps({
                "type": "error",
                "message": "La veille a échoué. Réessayez dans quelques instants.",
            }))
        finally:
            await queue.put(None)

    tache = asyncio.create_task(run())
    return _sse_response(request, queue, timeout=180.0, task=tache)

# --------------------------------------------------------------------------
# RegWatch — phrase « pourquoi ça compte » (optionnelle)
#
# ⚠️ **L'IA arrive en dernier et ne filtre jamais.** Ce qui est retenu a été
# décidé par la classification déterministe, hors ligne. Cette étape ajoute
# une phrase à des lignes **déjà retenues** — elle ne peut ni en écarter une,
# ni changer un niveau de signal.
#
# ⚠️ **Même limiteur que SafetyScope et ThreatScope, délibérément** : les
# trois puisent dans le même quota Groq gratuit. Un troisième compteur
# donnerait une fois et demie plus d'appels sur une seule enveloppe.
#
# Le tableau revient du navigateur, comme pour les exports HARA et TARA : il
# est donc revalidé intégralement ici. Un jeton est nécessaire — non pas pour
# la confidentialité (les titres sont publics), mais parce qu'une liste de
# signaux ne tient pas dans une query string.
# --------------------------------------------------------------------------

_MAX_EXPLAIN_ITEMS = 40


class RegwatchExplainItem(BaseModel):
    norm: str = ""
    normLabel: str = ""
    signal: str = ""
    title: str = ""
    published: str = ""
    source: str = ""
    tier: str = ""


class RegwatchExplainRequest(BaseModel):
    items: list[RegwatchExplainItem] = []


def _rebuild_watch_items(payload: list[dict]) -> list[WatchItem]:
    """Reconstruit les signaux venus du navigateur, en les revalidant.

    Une date illisible écarte la ligne plutôt que de faire échouer l'appel
    entier : le reste du tableau mérite quand même son explication.
    """
    items: list[WatchItem] = []
    for brut in payload[:_MAX_EXPLAIN_ITEMS]:
        titre = (brut.get("title") or "").strip()[:300]
        if not titre:
            continue
        try:
            publiee = date.fromisoformat((brut.get("published") or "")[:10])
        except ValueError:
            continue
        items.append(WatchItem(
            norm_key=(brut.get("norm") or "")[:40],
            norm_label=(brut.get("normLabel") or "")[:80],
            signal=(brut.get("signal") or "")[:60],
            title=titre,
            published=publiee,
            # La clé interne de source ne circule pas : le navigateur ne
            # l'a pas, et personne n'en a besoin ici.
            source_key="",
            source_label=(brut.get("source") or "")[:120],
            source_tier=(brut.get("tier") or "")[:20],
            # ⚠️ Lien et phrase ne sont lus que s'ils sont fournis. Ce qui
            # garantit qu'ils ne partent JAMAIS au modèle, ce n'est pas
            # cette fonction — c'est `RegwatchExplainItem`, qui ne les
            # déclare pas : un champ absent du modèle de requête ne peut
            # pas arriver. L'export, lui, en a besoin.
            url=(brut.get("url") or "")[:500],
            why=(brut.get("why") or "")[:400],
        ))
    return items


@app.post("/regwatch/explain")
async def regwatch_explain_prepare(request: Request, payload: RegwatchExplainRequest):
    """Valide le lot et rend un jeton — une liste ne tient pas dans une URL."""
    client = _client_key(request)

    refusal = _suggest_refusal(client)
    if refusal:
        return JSONResponse({"error": refusal}, status_code=429)

    items = [item.model_dump() for item in payload.items]
    if not _rebuild_watch_items(items):
        return JSONResponse(
            {"error": "Aucun signal exploitable à expliquer. Relancez une veille."},
            status_code=400,
        )

    return {"token": _issue_token(client, "regwatch-explain", {"items": items})}


@app.get("/regwatch/explain/stream")
async def regwatch_explain_stream(request: Request, t: str = ""):
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()
    client = _client_key(request)

    def task_callback(_task_output):
        loop.call_soon_threadsafe(queue.put_nowait, json.dumps({
            "type": "step_done", "index": 0, "total": 1,
        }))

    async def run():
        try:
            payload = _consume_token(t, client, "regwatch-explain")
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

                items = _rebuild_watch_items(payload["items"])
                await queue.put(json.dumps({"type": "start", "items": len(items)}))
                explique = await asyncio.to_thread(explain_items, items, task_callback)

                # Aligné sur l'ordre posté : `explain_items` ne réordonne
                # jamais, et un test du moteur le verrouille.
                await queue.put(json.dumps({
                    "type": "done",
                    "explanations": [item.why for item in explique],
                }))
        except Exception as exc:
            _log.exception("Explication RegWatch interrompue")
            await queue.put(json.dumps({
                "type": "error",
                "message": _failure_message(
                    exc, "L'explication a échoué. Le tableau reste utilisable tel quel."),
            }))
        finally:
            await queue.put(None)

    tache = asyncio.create_task(run())
    return _sse_response(request, queue, timeout=180.0, task=tache)

# --------------------------------------------------------------------------
# RegWatch — export Excel
#
# Même magasin mémoire que les trois autres outils, avec `kind="regwatch"`.
# Le tableau revient du navigateur et est revalidé ligne par ligne, comme
# pour les exports HARA et TARA.
# --------------------------------------------------------------------------

class RegwatchReportItem(BaseModel):
    norm: str = ""
    normLabel: str = ""
    signal: str = ""
    title: str = ""
    published: str = ""
    source: str = ""
    tier: str = ""
    url: str = ""
    why: str = ""


class RegwatchReportRequest(BaseModel):
    norms: list[str] = []
    lookbackDays: int = 0
    sourcesRead: int = 0
    sourcesTotal: int = 0
    unreachable: list[str] = []
    degraded: list[str] = []
    undated: list[str] = []
    errors: list[str] = []
    items: list[RegwatchReportItem] = []


@app.post("/regwatch/report")
async def regwatch_report_create(request: Request, payload: RegwatchReportRequest):
    """Reconstruit la veille côté serveur, puis prépare le classeur.

    ⚠️ La couverture est reprise telle que le navigateur la rapporte, mais
    les **référentiels** sont revalidés : une clé inventée ne doit pas se
    retrouver imprimée dans un classeur. Un export sans aucun signal reste
    permis — un classeur qui ne dit que « rien de neuf, et voici les sources
    muettes » est précisément ce qu'un veilleur doit pouvoir archiver.
    """
    try:
        selection = parse_selection(payload.norms)
    except InvalidSelection as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    items = _rebuild_watch_items([item.model_dump() for item in payload.items])

    maintenant = datetime.now(timezone.utc)
    result = WatchResult(
        norms=[norm.key for norm in selection],
        lookback_days=payload.lookbackDays or 90,
        started_at=maintenant,
        finished_at=maintenant,
        items=items,
        unreachable=[label[:160] for label in payload.unreachable[:20]],
        degraded=[label[:160] for label in payload.degraded[:20]],
        undated=[label[:300] for label in payload.undated[:40]],
        errors=[message[:300] for message in payload.errors[:40]],
        sources_read=payload.sourcesRead,
        sources_total=payload.sourcesTotal,
    )

    excel = await asyncio.to_thread(build_watch_excel, result)
    report_id = _store_report(
        _client_key(request),
        "regwatch",
        excel,
        "regwatch_" + result.started_at.strftime("%Y%m%d_%H%M") + ".xlsx",
    )
    return {"report_id": report_id}


@app.get("/regwatch/report/{report_id}.xlsx")
async def regwatch_report_download(request: Request, report_id: str):
    return _serve_report(
        request, report_id, "regwatch",
        "Rapport expiré ou introuvable. Relancez l'export.",
    )
