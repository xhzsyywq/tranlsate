"""Fullscreen region-selection overlay (Snipping-Tool style).

Presents a dimmed, borderless, always-on-top window covering the full virtual
desktop. The user drags a rectangle; on release the geometry (in global screen
coordinates) is emitted via :pyattr:`selected`. Pressing Escape cancels.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget


class RegionSelector(QWidget):
    """Transparent overlay that lets the user drag-select a screen region."""

    selected = Signal(QRect)
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        # Cover the entire virtual desktop (all monitors).
        geo = QRect()
        for screen in QGuiApplication.screens():
            geo = geo.united(screen.geometry())
        self._virtual_geo = geo
        self.setGeometry(geo)

        self._origin: QPoint | None = None
        self._current: QPoint | None = None

    # ------------------------------------------------------------- painting
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

        if self._origin and self._current:
            rect = QRect(self._origin, self._current).normalized()
            # Clear the selection area (show the live screen through the dim).
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            pen = QPen(QColor(0, 160, 255), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

    # -------------------------------------------------------------- events
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._current = self._origin
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._origin is not None:
            self._current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self._origin is None:
            return
        rect = QRect(self._origin, event.position().toPoint()).normalized()
        self.close()
        if rect.width() >= 5 and rect.height() >= 5:
            # Translate widget-local coords to global screen coords.
            global_rect = QRect(
                rect.topLeft() + self._virtual_geo.topLeft(), rect.size()
            )
            self.selected.emit(global_rect)
        else:
            self.cancelled.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.cancelled.emit()
