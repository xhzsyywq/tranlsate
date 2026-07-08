"""Floating popup showing the recognized question, answer, and explanation."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from .i18n import tr


class SolverPopup(QFrame):
    """Always-on-top window with question, answer, and auto-fill action."""

    fill_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle(tr("solve_result_title"))
        self.resize(480, 380)

        self.question_label = QLabel(tr("solve_question"))
        self.question_view = QTextEdit()
        self.question_view.setReadOnly(True)
        self.question_view.setMaximumHeight(110)

        self.answer_label = QLabel(tr("solve_answer"))
        self.answer_edit = QLineEdit()

        self.explanation_label = QLabel(tr("solve_explanation"))
        self.explanation_view = QTextEdit()
        self.explanation_view.setReadOnly(True)

        self.copy_btn = QPushButton(tr("solve_copy_answer"))
        self.copy_btn.clicked.connect(self._copy_answer)
        self.fill_btn = QPushButton(tr("solve_autofill"))
        self.fill_btn.clicked.connect(self._emit_fill)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.fill_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.question_label)
        layout.addWidget(self.question_view)
        layout.addWidget(self.answer_label)
        layout.addWidget(self.answer_edit)
        layout.addWidget(self.explanation_label)
        layout.addWidget(self.explanation_view, 1)
        layout.addLayout(btn_row)

    def _copy_answer(self) -> None:
        QApplication.clipboard().setText(self.answer_edit.text())

    def _emit_fill(self) -> None:
        self.fill_requested.emit(self.answer_edit.text())

    def set_question(self, text: str) -> None:
        self.question_view.setPlainText(text)

    def set_status(self, text: str) -> None:
        self.answer_edit.setText(text)

    def set_answer(self, answer: str, explanation: str) -> None:
        self.answer_edit.setText(answer)
        self.explanation_view.setPlainText(explanation)

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
