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
