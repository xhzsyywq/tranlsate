"""Background worker for the capture -> OCR -> LLM-solve pipeline."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from ..core.engine import TranslationEngine
from ..core.logging_setup import get_logger
from ..core.ocr import OCREngine

log = get_logger(__name__)


def parse_answer(reply: str) -> tuple[str, str]:
    """Split a solver reply into (answer, explanation).

    Falls back gracefully if the model didn't follow the exact format.
    """
    answer = ""
    explanation = ""
    for line in reply.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("ANSWER:") or upper.startswith("ANSWER："):
            answer = stripped.split(":", 1)[-1].split("：", 1)[-1].strip()
        elif upper.startswith("EXPLANATION:") or upper.startswith("EXPLANATION："):
            explanation = stripped.split(":", 1)[-1].split("：", 1)[-1].strip()
    if not answer:
        answer = reply.strip()
    return answer, explanation


class SolveWorker(QObject):
    """Runs OCR then LLM solving on a captured image off the UI thread."""

    recognized = Signal(str)
    finished = Signal(str, str)  # (answer, explanation)
    failed = Signal(str)

    def __init__(self, engine: TranslationEngine, ocr: OCREngine, image, answer_lang: str):
        super().__init__()
        self._engine = engine
        self._ocr = ocr
        self._image = image
        self._answer_lang = answer_lang

    def run(self) -> None:
        try:
            text = self._ocr.image_to_text(self._image)
            log.info("Solver OCR recognized %d chars", len(text))
            self.recognized.emit(text)
            if not text.strip():
                self.finished.emit("", "")
                return
            reply = self._engine.solve(text, self._answer_lang)
            answer, explanation = parse_answer(reply)
            log.info("Solver produced answer (%d chars)", len(answer))
            self.finished.emit(answer, explanation)
        except Exception as exc:  # noqa: BLE001
            log.exception("Solver error")
            self.failed.emit(str(exc))


class SolveTask:
    """Owns a QThread + worker pair for one solve run."""

    def __init__(self, engine: TranslationEngine, ocr: OCREngine, image, answer_lang: str):
        self.thread = QThread()
        self.worker = SolveWorker(engine, ocr, image, answer_lang)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

    def start(self) -> None:
        self.thread.start()
