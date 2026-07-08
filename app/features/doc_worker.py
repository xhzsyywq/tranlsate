"""Background worker for batch document translation.

Translates segments concurrently (thread pool) for higher throughput, honours
user-chosen output directory and format, and logs per-segment and total timing
so translation efficiency can be tracked via the log file.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from ..core.documents import get_parser
from ..core.documents.writers import resolve_output_path, write_output
from ..core.engine import TranslationEngine
from ..core.logging_setup import get_logger

log = get_logger(__name__)


class DocTranslateWorker(QObject):
    """Extracts, translates concurrently, and writes a document."""

    progress = Signal(int, int)  # (done, total)
    finished = Signal(str)  # output path
    failed = Signal(str)

    def __init__(
        self,
        engine: TranslationEngine,
        input_path: str,
        source: str,
        target: str,
        output_dir: str = "",
        output_format: str = "same",
        max_workers: int = 4,
    ):
        super().__init__()
        self._engine = engine
        self._input = input_path
        self._source = source
        self._target = target
        self._output_dir = output_dir
        self._output_format = output_format
        self._max_workers = max(1, int(max_workers))
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _translate_one(self, index: int, segment: str) -> tuple[int, str]:
        if not segment.strip():
            return index, segment
        started = time.perf_counter()
        result = self._engine.translate(segment, self._source, self._target)
        elapsed = time.perf_counter() - started
        log.debug(
            "Segment %d translated in %.2fs (%d chars)", index, elapsed, len(segment)
        )
        return index, result

    def run(self) -> None:
        try:
            overall_start = time.perf_counter()
            parser = get_parser(self._input)
            segments = parser.extract()
            total = len(segments)
            log.info(
                "Doc translate: %d segments from %s (workers=%d, format=%s)",
                total,
                self._input,
                self._max_workers,
                self._output_format,
            )
            self.progress.emit(0, total)

            translations: list[str] = [""] * total
            done = 0

            with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                futures = {
                    pool.submit(self._translate_one, i, seg): i
                    for i, seg in enumerate(segments)
                }
                for future in as_completed(futures):
                    if self._cancelled:
                        log.info("Doc translate cancelled at %d/%d", done, total)
                        pool.shutdown(wait=False, cancel_futures=True)
                        self.failed.emit("cancelled")
                        return
                    idx, text = future.result()
                    translations[idx] = text
                    done += 1
                    self.progress.emit(done, total)

            source = Path(self._input)
            output_path = resolve_output_path(
                source,
                total,
                self._target,
                self._output_dir,
                self._output_format,
                parser,
            )
            actual = write_output(
                parser, segments, translations, output_path, self._output_format
            )

            elapsed = time.perf_counter() - overall_start
            rate = total / elapsed if elapsed > 0 else 0
            log.info(
                "Doc translate finished -> %s in %.2fs (%.1f segments/s)",
                actual,
                elapsed,
                rate,
            )
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
        source: str,
        target: str,
        output_dir: str = "",
        output_format: str = "same",
        max_workers: int = 4,
    ):
        self.thread = QThread()
        self.worker = DocTranslateWorker(
            engine,
            input_path,
            source,
            target,
            output_dir,
            output_format,
            max_workers,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

    def start(self) -> None:
        self.thread.start()
