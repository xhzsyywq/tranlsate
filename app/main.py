"""GUI entry point.

Run with::

    python -m app.main
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .core.config import AppConfig
from .core.engine import TranslationEngine
from .core.logging_setup import get_logger, setup_logging
from .ui.hotkeys import GlobalHotkeys
from .ui.main_window import MainWindow
from .ui.tray import create_tray


def main() -> int:
    setup_logging()
    log = get_logger(__name__)
    log.info("AutoTranslate starting")

    app = QApplication(sys.argv)
    app.setApplicationName("AutoTranslate")
    app.setQuitOnLastWindowClosed(False)

    engine = TranslationEngine(AppConfig.load())
    window = MainWindow(engine)
    window.tray = create_tray(window)
    window.show()

    hotkeys = GlobalHotkeys()
    hotkeys.screen_translate_triggered.connect(window.start_screen_translate)
    hotkeys.solve_triggered.connect(window.start_solve)
    hotkeys.input_translate_triggered.connect(window.start_input_translate)
    hotkeys.start("ctrl+alt+z", "ctrl+alt+x", "ctrl+alt+t")
    window.hotkeys = hotkeys

    # Auto-start the local server for browser extension integration.
    from .server import start_server

    start_server(engine, engine.config.server_port)
    window._server_running = True
    window.tray.retranslate()

    log.info("AutoTranslate ready")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
