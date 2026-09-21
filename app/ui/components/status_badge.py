"""Status badge widget."""
from __future__ import annotations
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class StatusBadge(QLabel):
    """Small badge widget with semantic colours."""

    STYLES = {
        "default": "badge",
        "accent": "badge_accent",
        "success": "badge_success",
        "warning": "badge_warning",
    }

    def __init__(self, text: str = "", variant: str = "default", parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName(self.STYLES.get(variant, "badge"))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_variant(self, variant: str) -> None:
        self.setObjectName(self.STYLES.get(variant, "badge"))
        self.style().unpolish(self)
        self.style().polish(self)
