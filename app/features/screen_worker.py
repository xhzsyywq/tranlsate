"""Background worker for the capture -> OCR -> translate pipeline."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from ..core.engine import TranslationEngine
from ..core.ocr import OCREngine


class ScreenTranslateWorker(QObject):
    """Runs OCR then translation on a captured PIL image off the UI thread."""

    recognized = Signal(str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        engine: TranslationEngine,
        ocr: OCREngine,
        image,
        source: str,
        target: str,
    ):
        super().__init__()
        self._engine = engine
        self._ocr = ocr
        self._image = image
        self._source = source
        self._target = target

    def run(self) -> None:
        try:
            text = self._ocr.image_to_text(self._image)
            self.recognized.emit(text)
            if not text.strip():
                self.finished.emit("")
                return
            result = self._engine.translate(text, self._source, self._target)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class ScreenTranslateTask:
    """Owns a QThread + worker pair for one screen-translation run."""

    def __init__(
        self,
        engine: TranslationEngine,
        ocr: OCREngine,
        image,
        source: str,
        target: str,
    ):
        self.thread = QThread()
        self.worker = ScreenTranslateWorker(engine, ocr, image, source, target)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

    def start(self) -> None:
        self.thread.start()
