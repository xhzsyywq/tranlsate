"""Local HTTP server for browser extension integration."""

from __future__ import annotations

import threading

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.engine import TranslationEngine
from ..core.logging_setup import get_logger

log = get_logger(__name__)

app = FastAPI(title="AutoTranslate Server", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine: TranslationEngine | None = None


def set_engine(engine: TranslationEngine) -> None:
    global _engine
    _engine = engine


class TranslateRequest(BaseModel):
    text: str
    source_lang: str | None = None
    target_lang: str | None = None


class SolveRequest(BaseModel):
    question: str


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/languages")
async def languages():
    from ..core.providers.base import LANG_NAMES
    from ..ui.i18n import lang_label

    return {
        code: {"code": code, "label": lang_label(code), "name": name}
        for code, name in LANG_NAMES.items()
    }


@app.post("/translate")
async def translate(req: TranslateRequest):
    if not _engine:
        return JSONResponse({"error": "Engine not initialized"}, 503)
    try:
        result = _engine.translate(req.text, req.source_lang, req.target_lang)
        return {"result": result}
    except Exception as e:
        return JSONResponse({"error": str(e)}, 500)


@app.post("/solve")
async def solve(req: SolveRequest):
    if not _engine:
        return JSONResponse({"error": "Engine not initialized"}, 503)
    try:
        from ..features.solve_worker import parse_answer

        reply = _engine.solve(req.question)
        answer, explanation = parse_answer(reply)
        return {"answer": answer, "explanation": explanation}
    except Exception as e:
        return JSONResponse({"error": str(e)}, 500)


class UvicornThread(threading.Thread):
    def __init__(self, host: str = "127.0.0.1", port: int = 18190):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self._server: uvicorn.Server | None = None

    def run(self) -> None:
        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="info")
        self._server = uvicorn.Server(config)
        self._server.run()

    def shutdown(self) -> None:
        if self._server:
            self._server.should_exit = True


_server_thread: UvicornThread | None = None


def start_server(engine: TranslationEngine, port: int = 18190) -> bool:
    global _server_thread
    if _server_thread is not None:
        return False
    set_engine(engine)
    _server_thread = UvicornThread(port=port)
    _server_thread.start()
    log.info("Server started on http://127.0.0.1:%d", port)
    return True


def stop_server() -> None:
    global _server_thread
    if _server_thread:
        _server_thread.shutdown()
        _server_thread = None
