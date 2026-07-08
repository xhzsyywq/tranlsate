"""GUI entry point.

Run with::

    python -m app.main
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .core.config import AppConfig
from .core.engine import TranslationEngine
from .ui.main_window import MainWindow
from .ui.tray import create_tray


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AutoTranslate")
    app.setQuitOnLastWindowClosed(False)

    engine = TranslationEngine(AppConfig.load())
    window = MainWindow(engine)
    window.tray = create_tray(window)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
