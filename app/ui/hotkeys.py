"""Global hotkey manager.

Wraps the ``keyboard`` library, which invokes callbacks on its own thread, and
re-emits them as a Qt signal so slots run safely on the GUI thread.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class GlobalHotkeys(QObject):
    """Registers system-wide hotkeys and forwards them to the GUI thread."""

    screen_translate_triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = False

    def start(self, screen_hotkey: str = "ctrl+alt+z") -> bool:
        """Register hotkeys. Returns False if the backend is unavailable."""
        try:
            import keyboard
        except Exception:  # noqa: BLE001
            return False

        try:
            keyboard.add_hotkey(
                screen_hotkey, self.screen_translate_triggered.emit
            )
        except Exception:  # noqa: BLE001 - e.g. insufficient privileges
            return False

        self._enabled = True
        return True

    def stop(self) -> None:
        if not self._enabled:
            return
        try:
            import keyboard

            keyboard.unhook_all_hotkeys()
        except Exception:  # noqa: BLE001
            pass
        self._enabled = False
