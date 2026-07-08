"""Screen translation controller.

Flow: show region selector (returns a cropped image) -> run OCR on a worker
thread -> emit the recognized text so the main window can fill its source box
and translate it there.
"""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QObject, Signal

from ..core.engine import TranslationEngine
from ..core.logging_setup import get_logger
from ..core.ocr import OCREngine
from ..ui.region_selector import RegionSelector
from .screen_worker import OCRTask

log = get_logger(__name__)


class ScreenTranslator(QObject):
    """Captures a screen region, OCRs it, and emits the recognized text."""

    recognizing = Signal()
    recognized = Signal(str)
    failed = Signal(str)

    def __init__(self, engine: TranslationEngine):
        super().__init__()
        self.engine = engine
        self.ocr = OCREngine()
        self._selector: RegionSelector | None = None
        self._task: OCRTask | None = None

    def start(self) -> None:
        """Begin a screen-translation session by showing the region selector."""
        log.info("Screen translate started; showing region selector")
        self._selector = RegionSelector()
        self._selector.selected.connect(self._on_region_selected)
        self._selector.cancelled.connect(self._on_cancelled)
        self._selector.show()
        self._selector.activateWindow()
        self._selector.raise_()

    def _on_cancelled(self) -> None:
        log.info("Region selection cancelled")
        self._selector = None

    def _on_region_selected(self, image: Image.Image) -> None:
        log.info("Region selected: image size=%s", getattr(image, "size", None))
        self._selector = None
        self.recognizing.emit()
        self._task = OCRTask(self.ocr, image)
        self._task.worker.finished.connect(self._on_ocr_finished)
        self._task.worker.failed.connect(self._on_ocr_failed)
        self._task.thread.finished.connect(self._on_thread_done)
        self._task.start()
        log.info("OCR task started")

    def _on_ocr_finished(self, text: str) -> None:
        log.info("OCR finished: %d chars recognized", len(text))
        self.recognized.emit(text)

    def _on_ocr_failed(self, message: str) -> None:
        log.error("OCR failed: %s", message)
        self.failed.emit(message)

    def _on_thread_done(self) -> None:
        log.debug("OCR thread finished")
        self._task = None
