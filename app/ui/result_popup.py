"""Floating popup that shows the recognized text and its translation."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from .i18n import tr


class ResultPopup(QFrame):
    """Small always-on-top window with source text and translation panes."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle(tr("screen_result_title"))
        self.resize(460, 320)

        self.source_label = QLabel(tr("screen_recognized"))
        self.source_view = QTextEdit()
        self.source_view.setReadOnly(True)
        self.source_view.setMaximumHeight(110)

        self.result_label = QLabel(tr("screen_translation"))
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)

        self.copy_btn = QPushButton(tr("screen_copy"))
        self.copy_btn.clicked.connect(self._copy_result)

        layout = QVBoxLayout(self)
        layout.addWidget(self.source_label)
        layout.addWidget(self.source_view)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_view, 1)
        layout.addWidget(self.copy_btn)

    def _copy_result(self) -> None:
        QApplication.clipboard().setText(self.result_view.toPlainText())

    def set_source(self, text: str) -> None:
        self.source_view.setPlainText(text)

    def set_result(self, text: str) -> None:
        self.result_view.setPlainText(text)

    def set_status(self, text: str) -> None:
        self.result_view.setPlainText(text)

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
