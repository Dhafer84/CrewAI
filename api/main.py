"""Backend FastAPI — site de démos Qualité & Sécurité.

  GET /              → page de garde (catalogue d'outils)
  GET /qualitycrew   → démo d'audit ASPICE / ISO 26262
  GET /sentinelscan  → veille de fuite d'information
  GET /audit/stream  → SSE : progression des agents + rapport final
  GET /static/*      → assets CSS

Enveloppe mince : aucune logique métier ici, tout est dans src/.

Un seul audit à la fois (Semaphore). Pas d'input utilisateur :
l'audit tourne toujours sur data/sample_project/.
"""

import asyncio
import json
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from qualitycrew.config import require_llm_key  # noqa: E402
from qualitycrew.core import run_audit  # noqa: E402

_DOCUMENTS_DIR = _ROOT / "data" / "sample_project"
_SITE_DIR = _ROOT / "site"

app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(_SITE_DIR)), name="static")

_audit_semaphore = asyncio.Semaphore(1)


# Catalogue des pages. Ajouter un outil = ajouter une entrée ici et sa carte
# dans site/index.html — rien d'autre à toucher.
_PAGES = {
    "/": "index.html",
    "/qualitycrew": "qualitycrew.html",
    "/sentinelscan": "sentinelscan.html",
}


def _serve(filename: str):
    return FileResponse(_SITE_DIR / filename)


@app.get("/")
async def index():
    return _serve(_PAGES["/"])


@app.get("/qualitycrew")
async def qualitycrew_page():
    return _serve(_PAGES["/qualitycrew"])


@app.get("/sentinelscan")
async def sentinelscan_page():
    return _serve(_PAGES["/sentinelscan"])


@app.get("/audit/stream")
async def audit_stream(request: Request):
    if _audit_semaphore.locked():
        return JSONResponse(
            {"error": "Un audit est déjà en cours. Réessayez dans quelques instants."},
            status_code=429,
        )

    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()
    task_index = [0]

    def task_callback(task_output):
        idx = task_index[0]
        task_index[0] += 1
        event = {
            "type": "task_done",
            "index": idx,
            "agent": task_output.agent,
            "output": task_output.raw,
        }
        loop.call_soon_threadsafe(queue.put_nowait, json.dumps(event))

    async def run():
        async with _audit_semaphore:
            try:
                await queue.put(json.dumps({"type": "start"}))
                require_llm_key()
                report = await asyncio.to_thread(
                    run_audit, _DOCUMENTS_DIR, None, task_callback
                )
                await queue.put(json.dumps({"type": "done", "report": report}))
            except Exception as exc:
                await queue.put(json.dumps({
                    "type": "error",
                    "message": "L'audit a échoué. Vérifiez la clé API et relancez.",
                }))
            finally:
                await queue.put(None)

    asyncio.create_task(run())

    async def event_gen():
        while True:
            if await request.is_disconnected():
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=180.0)
            except asyncio.TimeoutError:
                yield 'data: {"type":"error","message":"Timeout"}\n\n'
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
