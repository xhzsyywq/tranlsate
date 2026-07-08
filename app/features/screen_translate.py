"""Screen translation controller.

Orchestrates the flow: show region selector -> grab pixels with mss -> run OCR
and translation on a worker thread -> display the result popup.
"""

from __future__ import annotations

import mss
from PIL import Image
from PySide6.QtCore import QObject, QRect

from ..core.engine import TranslationEngine
from ..core.ocr import OCREngine
from ..ui.i18n import tr
from ..ui.region_selector import RegionSelector
from ..ui.result_popup import ResultPopup
from .screen_worker import ScreenTranslateTask


class ScreenTranslator(QObject):
    def __init__(self, engine: TranslationEngine):
        super().__init__()
        self.engine = engine
        self.ocr = OCREngine()
        self._selector: RegionSelector | None = None
        self._popup: ResultPopup | None = None
        self._task: ScreenTranslateTask | None = None

    def start(self) -> None:
        """Begin a screen-translation session by showing the region selector."""
        self._selector = RegionSelector()
        self._selector.selected.connect(self._on_region_selected)
        self._selector.cancelled.connect(self._on_cancelled)
        self._selector.show()
        self._selector.activateWindow()
        self._selector.raise_()

    def _on_cancelled(self) -> None:
        self._selector = None

    def _on_region_selected(self, rect: QRect) -> None:
        self._selector = None
        image = self._grab(rect)
        if image is None:
            return

        self._popup = ResultPopup()
        self._popup.set_source("")
        self._popup.set_status(tr("screen_recognizing"))
        self._popup.show_near_cursor()

        self._task = ScreenTranslateTask(
            self.engine,
            self.ocr,
            image,
            self.engine.config.source_lang,
            self.engine.config.target_lang,
        )
        self._task.worker.recognized.connect(self._on_recognized)
        self._task.worker.finished.connect(self._on_finished)
        self._task.worker.failed.connect(self._on_failed)
        self._task.thread.finished.connect(self._on_thread_done)
        self._task.start()

    @staticmethod
    def _grab(rect: QRect) -> Image.Image | None:
        if rect.width() <= 0 or rect.height() <= 0:
            return None
        region = {
            "left": rect.left(),
            "top": rect.top(),
            "width": rect.width(),
            "height": rect.height(),
        }
        with mss.mss() as sct:
            shot = sct.grab(region)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    def _on_recognized(self, text: str) -> None:
        if self._popup is not None:
            self._popup.set_source(text or tr("screen_no_text"))
            if text.strip():
                self._popup.set_status(tr("status_translating"))

    def _on_finished(self, result: str) -> None:
        if self._popup is not None:
            if result:
                self._popup.set_result(result)
            else:
                self._popup.set_result(tr("screen_no_text"))

    def _on_failed(self, message: str) -> None:
        if self._popup is not None:
            self._popup.set_result(f"{tr('status_failed')}: {message}")

    def _on_thread_done(self) -> None:
        self._task = None
