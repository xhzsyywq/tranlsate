"""A small, reusable floating popup for showing a single block of text."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from .i18n import tr


class SimplePopup(QFrame):
    """Always-on-top popup showing text with a copy button."""

    def __init__(self, title: str, text: str) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle(title)
        self.resize(360, 200)

        self.view = QTextEdit()
        self.view.setReadOnly(True)
        self.view.setPlainText(text)

        self.copy_btn = QPushButton(tr("screen_copy"))
        self.copy_btn.clicked.connect(self._copy)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.copy_btn)

    def _copy(self) -> None:
        QApplication.clipboard().setText(self.view.toPlainText())

    def show_near_cursor(self) -> None:
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        x = min(pos.x(), area.right() - self.width())
        y = min(pos.y(), area.bottom() - self.height())
        self.move(max(area.left(), x), max(area.top(), y))
        self.show()
        self.raise_()
        self.activateWindow()
