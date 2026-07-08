"""Background translation worker so the UI stays responsive."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from ..core.engine import TranslationEngine


class TranslationWorker(QObject):
    """Runs a single translation on a worker thread."""

    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, engine: TranslationEngine, text: str, source: str, target: str):
        super().__init__()
        self._engine = engine
        self._text = text
        self._source = source
        self._target = target

    def run(self) -> None:
        try:
            result = self._engine.translate(self._text, self._source, self._target)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 - report any backend error to UI
            self.failed.emit(str(exc))


class TranslationTask:
    """Owns a QThread + worker pair and keeps them alive for the run."""

    def __init__(self, engine: TranslationEngine, text: str, source: str, target: str):
        self.thread = QThread()
        self.worker = TranslationWorker(engine, text, source, target)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

    def start(self) -> None:
        self.thread.start()
