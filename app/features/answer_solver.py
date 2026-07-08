"""Answer solver controller.

Flow: show region selector (returns a cropped image) -> OCR + LLM solve on a
worker thread -> show a popup with the question, answer, and explanation, with
copy and auto-fill actions.
"""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QObject

from ..core.engine import TranslationEngine
from ..core.logging_setup import get_logger
from ..core.ocr import OCREngine
from ..ui.i18n import tr
from ..ui.region_selector import RegionSelector
from ..ui.solver_popup import SolverPopup
from .autofill import type_text
from .solve_worker import SolveTask

log = get_logger(__name__)


class AnswerSolver(QObject):
    def __init__(self, engine: TranslationEngine):
        super().__init__()
        self.engine = engine
        self.ocr = OCREngine()
        self._selector: RegionSelector | None = None
        self._popup: SolverPopup | None = None
        self._task: SolveTask | None = None

    def start(self) -> None:
        """Begin a solve session by showing the region selector."""
        log.info("Answer solver started; showing region selector")
        self._selector = RegionSelector()
        self._selector.selected.connect(self._on_region_selected)
        self._selector.cancelled.connect(self._on_cancelled)
        self._selector.show()
        self._selector.activateWindow()
        self._selector.raise_()

    def _on_cancelled(self) -> None:
        log.info("Solver region selection cancelled")
        self._selector = None

    def _on_region_selected(self, image: Image.Image) -> None:
        log.info("Solver region selected: size=%s", getattr(image, "size", None))
        self._selector = None

        self._popup = SolverPopup()
        self._popup.fill_requested.connect(self._on_fill_requested)
        self._popup.set_question("")
        self._popup.set_status(tr("solve_solving"))
        self._popup.show_near_cursor()

        self._task = SolveTask(
            self.engine, self.ocr, image, self.engine.config.ui_lang
        )
        self._task.worker.recognized.connect(self._on_recognized)
        self._task.worker.finished.connect(self._on_finished)
        self._task.worker.failed.connect(self._on_failed)
        self._task.thread.finished.connect(self._on_thread_done)
        self._task.start()

    def _on_recognized(self, text: str) -> None:
        if self._popup is not None:
            self._popup.set_question(text or tr("screen_no_text"))

    def _on_finished(self, answer: str, explanation: str) -> None:
        if self._popup is not None:
            if answer:
                self._popup.set_answer(answer, explanation)
            else:
                self._popup.set_status(tr("screen_no_text"))

    def _on_failed(self, message: str) -> None:
        if self._popup is not None:
            self._popup.set_status(f"{tr('status_failed')}: {message}")

    def _on_fill_requested(self, answer: str) -> None:
        log.info("Auto-fill requested")
        if self._popup is not None:
            self._popup.hide()
        type_text(answer, delay=0.6)

    def _on_thread_done(self) -> None:
        self._task = None
