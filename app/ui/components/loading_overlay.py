"""Animated loading overlay widget."""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with status message."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(15, 17, 23, 0.80);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel("Loading...", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "color: #e8eaf6; font-size: 18px; font-weight: 600; background: transparent;"
        )
        layout.addWidget(self._label)

        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self.hide()

    def show_with_message(self, message: str) -> None:
        base = message.rstrip(".")
        self._base_message = base
        self._label.setText(base)
        self.resize(self.parent().size())
        self._timer.start(400)
        self.show()
        self.raise_()

    def hide_overlay(self) -> None:
        self._timer.stop()
        self.hide()

    def _animate(self) -> None:
        self._dots = (self._dots + 1) % 4
        self._label.setText(self._base_message + "." * self._dots)
