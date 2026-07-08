"""Fullscreen region-selection overlay (Snipping-Tool style).

On construction it grabs a frozen screenshot of the whole virtual desktop and
displays it as an opaque background, dimming everything except the region the
user drags out. This means the user always sees the real content while
selecting. On release the cropped screenshot (a PIL image) is emitted via
:pyattr:`selected`; pressing Escape or a tiny selection cancels.
"""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QWidget

from ..core.logging_setup import get_logger

log = get_logger(__name__)


class RegionSelector(QWidget):
    """Transparent overlay that lets the user drag-select a screen region."""

    selected = Signal(object)  # emits a PIL.Image.Image
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        # Compute the full virtual desktop geometry (all monitors, logical px).
        geo = QRect()
        for screen in QGuiApplication.screens():
            geo = geo.united(screen.geometry())
        self._virtual_geo = geo

        # Freeze a screenshot of the whole desktop before we show the overlay.
        self._pixmap = self._capture_desktop(geo)
        self.setGeometry(geo)

        self._origin: QPoint | None = None
        self._current: QPoint | None = None

    # ------------------------------------------------------------- capture
    @staticmethod
    def _capture_desktop(virtual: QRect) -> QPixmap:
        screens = QGuiApplication.screens()
        dpr = QGuiApplication.primaryScreen().devicePixelRatio() or 1.0
        full = QPixmap(
            int(virtual.width() * dpr), int(virtual.height() * dpr)
        )
        full.setDevicePixelRatio(dpr)
        full.fill(Qt.GlobalColor.black)

        painter = QPainter(full)
        for screen in screens:
            shot = screen.grabWindow(0)
            offset = screen.geometry().topLeft() - virtual.topLeft()
            painter.drawPixmap(offset, shot)
        painter.end()
        return full

    # ------------------------------------------------------------- painting
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        if self._origin and self._current:
            rect = QRect(self._origin, self._current).normalized()
            painter.save()
            painter.setClipRect(rect)
            painter.drawPixmap(0, 0, self._pixmap)
            painter.restore()
            painter.setPen(QPen(QColor(0, 160, 255), 2))
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
        self.hide()
        if rect.width() >= 5 and rect.height() >= 5:
            try:
                image = self._crop(rect)
            except Exception:  # noqa: BLE001
                log.exception("Region crop failed")
                image = None
            self.close()
            if image is not None:
                log.info("Region selected, emitting image size=%s", image.size)
                self.selected.emit(image)
                return
        self.close()
        log.info("Region selection too small or failed; cancelling")
        self.cancelled.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.cancelled.emit()

    # ---------------------------------------------------------------- crop
    def _crop(self, rect: QRect) -> Image.Image | None:
        dpr = self._pixmap.devicePixelRatio() or 1.0
        phys = QRect(
            int(rect.x() * dpr),
            int(rect.y() * dpr),
            int(rect.width() * dpr),
            int(rect.height() * dpr),
        )
        cropped = self._pixmap.copy(phys)
        image = cropped.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        width, height = image.width(), image.height()
        if width == 0 or height == 0:
            return None
        # In PySide6 constBits() returns a correctly-sized memoryview; convert
        # via QByteArray to be robust across versions and row-stride padding.
        ptr = image.constBits()
        buffer = bytes(ptr)
        bytes_per_line = image.bytesPerLine()
        expected = width * 4
        if bytes_per_line == expected:
            pil = Image.frombytes("RGBA", (width, height), buffer)
        else:
            # Strip row padding.
            rows = [
                buffer[i * bytes_per_line : i * bytes_per_line + expected]
                for i in range(height)
            ]
            pil = Image.frombytes("RGBA", (width, height), b"".join(rows))
        return pil.convert("RGB")
