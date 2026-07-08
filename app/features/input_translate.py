"""Input-box real-time translation.

Workflow (triggered by a global hotkey while the user has text selected in any
application):

1. Save the current clipboard.
2. Simulate Ctrl+C to copy the selected text.
3. Translate the copied text on a worker thread.
4. In replace mode, put the translation on the clipboard and simulate Ctrl+V to
   paste over the selection; otherwise show a small popup.
5. Restore the original clipboard.

This clipboard approach works across virtually any Windows input field without
per-application integration.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from ..core.engine import TranslationEngine
from ..core.logging_setup import get_logger
from ..ui.i18n import tr
from ..ui.worker import TranslationTask

log = get_logger(__name__)


class InputTranslator(QObject):
    """Translate the currently selected text in any input field in place."""

    def __init__(self, engine: TranslationEngine):
        super().__init__()
        self.engine = engine
        self._task: TranslationTask | None = None
        self._saved_clipboard: str = ""
        self._popup = None

    def start(self) -> None:
        """Entry point (call on the GUI thread, e.g. from a hotkey signal)."""
        try:
            import keyboard
        except Exception:  # noqa: BLE001
            log.warning("keyboard backend unavailable; input translate disabled")
            return

        clipboard = QApplication.clipboard()
        self._saved_clipboard = clipboard.text()
        log.info("Input translate: copying selection")

        # Release the hotkey modifiers, then copy the current selection.
        for key in ("alt", "ctrl", "shift"):
            try:
                keyboard.release(key)
            except Exception:  # noqa: BLE001
                pass
        keyboard.send("ctrl+c")

        # Give the OS a moment to populate the clipboard before reading it.
        QTimer.singleShot(150, self._after_copy)

    def _after_copy(self) -> None:
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text.strip() or text == self._saved_clipboard:
            log.info("Input translate: no new selection captured")
            self._restore_clipboard()
            return

        log.info("Input translate: translating %d chars", len(text))
        self._task = TranslationTask(
            self.engine,
            text,
            self.engine.config.source_lang,
            self.engine.config.target_lang,
        )
        self._task.worker.finished.connect(self._on_finished)
        self._task.worker.failed.connect(self._on_failed)
        self._task.thread.finished.connect(self._on_thread_done)
        self._task.start()

    def _on_finished(self, result: str) -> None:
        if not result:
            self._restore_clipboard()
            return
        if self.engine.config.input_replace:
            self._paste(result)
        else:
            self._show_popup(result)
            self._restore_clipboard()

    def _paste(self, result: str) -> None:
        try:
            import keyboard
        except Exception:  # noqa: BLE001
            self._restore_clipboard()
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(result)
        log.info("Input translate: pasting result")
        keyboard.send("ctrl+v")
        # Restore the user's original clipboard shortly after pasting.
        QTimer.singleShot(200, self._restore_clipboard)

    def _show_popup(self, result: str) -> None:
        from ..ui.result_popup import SimplePopup

        self._popup = SimplePopup(tr("input_result_title"), result)
        self._popup.show_near_cursor()

    def _restore_clipboard(self) -> None:
        QApplication.clipboard().setText(self._saved_clipboard)

    def _on_failed(self, message: str) -> None:
        log.error("Input translate failed: %s", message)
        self._restore_clipboard()

    def _on_thread_done(self) -> None:
        self._task = None
