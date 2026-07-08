"""Auto-fill helper: type text into whatever control currently has focus.

Uses the ``keyboard`` library to send keystrokes to the active window. This is
best-effort: the target field must already be focused by the user.
"""

from __future__ import annotations

import time

from ..core.logging_setup import get_logger

log = get_logger(__name__)


def type_text(text: str, delay: float = 0.3) -> bool:
    """Type ``text`` into the focused control after a short delay.

    The delay gives the user time to click into the target field. Returns
    False if the keyboard backend is unavailable.
    """
    if not text:
        return False
    try:
        import keyboard
    except Exception:  # noqa: BLE001
        log.warning("keyboard backend unavailable; cannot auto-fill")
        return False

    time.sleep(delay)
    try:
        keyboard.write(text, delay=0.005)
        log.info("Auto-filled %d chars", len(text))
        return True
    except Exception:  # noqa: BLE001
        log.exception("Auto-fill failed")
        return False
