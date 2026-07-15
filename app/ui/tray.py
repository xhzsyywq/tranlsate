"""System tray icon: show/hide the main window and quit."""

from __future__ import annotations

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from .i18n import tr


class AppTrayIcon(QSystemTrayIcon):
    """Tray icon whose menu can be re-localized at runtime."""

    def __init__(self, window):
        icon = window.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        super().__init__(QIcon(icon), window)
        self._window = window

        menu = QMenu()
        self.show_action = QAction(window)
        self.show_action.triggered.connect(self._show_window)
        menu.addAction(self.show_action)

        self.screen_action = QAction(window)
        self.screen_action.triggered.connect(window.start_screen_translate)
        menu.addAction(self.screen_action)

        self.doc_action = QAction(window)
        self.doc_action.triggered.connect(window.open_document_dialog)
        menu.addAction(self.doc_action)

        self.solve_action = QAction(window)
        self.solve_action.triggered.connect(window.start_solve)
        menu.addAction(self.solve_action)

        self.input_action = QAction(window)
        self.input_action.triggered.connect(window.start_input_translate)
        menu.addAction(self.input_action)

        menu.addSeparator()

        self.server_action = QAction(window)
        self.server_action.triggered.connect(window.toggle_server)
        menu.addAction(self.server_action)

        self.settings_action = QAction(window)
        self.settings_action.triggered.connect(window.open_settings)
        menu.addAction(self.settings_action)

        menu.addSeparator()

        self.quit_action = QAction(window)
        self.quit_action.triggered.connect(QApplication.quit)
        menu.addAction(self.quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)
        self.retranslate()

    def retranslate(self) -> None:
        self.setToolTip(tr("tray_tooltip"))
        self.show_action.setText(tr("tray_show"))
        self.screen_action.setText(tr("screen_translate"))
        self.doc_action.setText(tr("doc_translate"))
        self.solve_action.setText(tr("solve"))
        self.input_action.setText(tr("input_translate"))
        running = getattr(self._window, "_server_running", False)
        self.server_action.setText(tr("server_stop") if running else tr("server_start"))
        self.settings_action.setText(tr("menu_settings"))
        self.quit_action.setText(tr("menu_quit"))

    def _show_window(self) -> None:
        self._window.showNormal()
        self._window.activateWindow()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._window.isVisible():
                self._window.hide()
            else:
                self._show_window()


def create_tray(window) -> AppTrayIcon:
    """Create, show, and attach a system tray icon to ``window``."""
    tray = AppTrayIcon(window)
    tray.show()
    return tray
