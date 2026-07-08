"""System tray icon: show/hide the main window and quit."""

from __future__ import annotations

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


def create_tray(window) -> QSystemTrayIcon:
    """Create and attach a system tray icon to ``window``."""
    icon = window.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    tray = QSystemTrayIcon(QIcon(icon), window)
    tray.setToolTip("AutoTranslate")

    menu = QMenu()

    show_action = QAction("Show", window)
    show_action.triggered.connect(lambda: (window.showNormal(), window.activateWindow()))
    menu.addAction(show_action)

    settings_action = QAction("Settings", window)
    settings_action.triggered.connect(window.open_settings)
    menu.addAction(settings_action)

    menu.addSeparator()

    quit_action = QAction("Quit", window)
    quit_action.triggered.connect(QApplication.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)

    def on_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if window.isVisible():
                window.hide()
            else:
                window.showNormal()
                window.activateWindow()

    tray.activated.connect(on_activated)
    tray.show()
    return tray
