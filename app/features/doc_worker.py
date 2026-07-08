"""Background worker for batch document translation."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from ..core.documents import get_parser
from ..core.engine import TranslationEngine
from ..core.logging_setup import get_logger

log = get_logger(__name__)


class DocTranslateWorker(QObject):
    """Extracts, translates segment-by-segment, and rebuilds a document."""

    progress = Signal(int, int)  # (done, total)
    finished = Signal(str)  # output path
    failed = Signal(str)

    def __init__(
        self,
        engine: TranslationEngine,
        input_path: str,
        output_path: str,
        source: str,
        target: str,
    ):
        super().__init__()
        self._engine = engine
        self._input = input_path
        self._output = output_path
        self._source = source
        self._target = target
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            parser = get_parser(self._input)
            segments = parser.extract()
            total = len(segments)
            log.info("Doc translate: %d segments from %s", total, self._input)
            self.progress.emit(0, total)

            translations: list[str] = []
            for i, segment in enumerate(segments, start=1):
                if self._cancelled:
                    log.info("Doc translate cancelled at %d/%d", i, total)
                    self.failed.emit("cancelled")
                    return
                if segment.strip():
                    translated = self._engine.translate(
                        segment, self._source, self._target
                    )
                else:
                    translated = segment
                translations.append(translated)
                self.progress.emit(i, total)

            parser.rebuild(translations, self._output)
            actual = self._output
            # PDF parser forces .txt output; reflect the real path.
            if not Path(actual).exists():
                alt = Path(actual).with_suffix(".txt")
                if alt.exists():
                    actual = str(alt)
            log.info("Doc translate finished -> %s", actual)
            self.finished.emit(str(actual))
        except Exception as exc:  # noqa: BLE001
            log.exception("Doc translate error")
            self.failed.emit(str(exc))


class DocTranslateTask:
    """Owns a QThread + worker pair for one document translation."""

    def __init__(
        self,
        engine: TranslationEngine,
        input_path: str,
        output_path: str,
        source: str,
        target: str,
    ):
        self.thread = QThread()
        self.worker = DocTranslateWorker(
            engine, input_path, output_path, source, target
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

    def start(self) -> None:
        self.thread.start()
