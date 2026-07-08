"""Background worker for OCR on a captured image (off the UI thread)."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from ..core.logging_setup import get_logger
from ..core.ocr import OCREngine

log = get_logger(__name__)


class OCRWorker(QObject):
    """Runs OCR on a captured PIL image and returns the recognized text."""

    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, ocr: OCREngine, image):
        super().__init__()
        self._ocr = ocr
        self._image = image

    def run(self) -> None:
        try:
            log.info("OCR worker running on image size=%s", getattr(self._image, "size", None))
            text = self._ocr.image_to_text(self._image)
            log.info("OCR worker recognized %d chars", len(text))
            self.finished.emit(text)
        except Exception as exc:  # noqa: BLE001
            log.exception("OCR worker error")
            self.failed.emit(str(exc))


class OCRTask:
    """Owns a QThread + worker pair for one OCR run."""

    def __init__(self, ocr: OCREngine, image):
        self.thread = QThread()
        self.worker = OCRWorker(ocr, image)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

    def start(self) -> None:
        self.thread.start()
