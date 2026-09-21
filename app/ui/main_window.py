"""
Main application window with Snapdragon Signature sidebar navigation.
"""
from __future__ import annotations

import logging
import platform
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QSizePolicy,
    QFrame
)

from app.core.app_context import AppContext
from app.ui.styles.theme import (
    get_stylesheet, SNAPDRAGON_RED, QUALCOMM_CYAN, TEXT_SECONDARY,
    BG_SURFACE, BORDER_SUBTLE, TEXT_PRIMARY, TEXT_MUTED, STATUS_GREEN,
    STATUS_AMBER, BG_ELEVATED
)

logger = logging.getLogger("edge_scholar.ui.main")

NAV_ITEMS = [
    ("📖", "Study Desk", "desk", "1"),
    ("📊", "Overview", "dashboard", "2"),
    ("🎙️", "Lecture Tapes", "audio", "3"),
    ("⚡", "Speed & Health", "benchmark", "4"),
    ("⚙️", "Preferences", "settings", "5"),
]


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("EdgeScholar — Private On-Device AI Study Studio")
        self.setMinimumSize(1150, 750)
        self.resize(1300, 840)
        self.setStyleSheet(get_stylesheet())

        self._current_view = "desk"
        self._nav_buttons: dict[str, QPushButton] = {}
        self._views: dict[str, QWidget] = {}

        self._build_ui()
        self._setup_shortcuts()
        self._navigate("desk")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self._sidebar = self._build_sidebar()
        root_layout.addWidget(self._sidebar)

        # Content area
        self._content_stack = QStackedWidget()
        root_layout.addWidget(self._content_stack, 1)

        # Build all views
        self._init_views()

        # Status bar
        self._status_bar = self.statusBar()
        self._status_bar.setStyleSheet(
            f"background-color: {BG_SURFACE}; color: {TEXT_MUTED}; "
            f"border-top: 1px solid {BORDER_SUBTLE}; padding: 4px 12px; font-size: 11px;"
        )
        self._update_status_bar()

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(225)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(6)

        # Brand header
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(3)

        logo_label = QLabel("EdgeScholar")
        logo_label.setObjectName("sidebar_brand")
        brand_layout.addWidget(logo_label)

        # Snapdragon pill tag
        tag_row = QHBoxLayout()
        tag_row.setSpacing(6)

        badge_snap = QLabel("SNAPDRAGON AI")
        badge_snap.setObjectName("badge_snapdragon")
        tag_row.addWidget(badge_snap)

        tag_row.addStretch()
        brand_layout.addLayout(tag_row)

        sub_label = QLabel("Private Edge Copilot")
        sub_label.setObjectName("sidebar_subtitle")
        brand_layout.addWidget(sub_label)

        layout.addLayout(brand_layout)
        layout.addSpacing(14)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {BORDER_SUBTLE}; max-height: 1px;")
        layout.addWidget(sep)
        layout.addSpacing(10)

        # Navigation section header
        nav_header = QLabel("WORKSPACE")
        nav_header.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; "
            f"letter-spacing: 1.2px; padding-left: 6px; padding-bottom: 2px;"
        )
        layout.addWidget(nav_header)

        # Nav buttons
        is_mac = platform.system() == "Darwin"
        mod_key = "⌘" if is_mac else "Ctrl+"

        for icon, label, view_id, key in NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("nav_btn")
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"{label} ({mod_key}{key})")
            btn.clicked.connect(lambda checked=False, v=view_id: self._navigate(v))
            self._nav_buttons[view_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Hardware & Engine Footer Card
        hw_card = QFrame()
        hw_card.setStyleSheet(
            f"background-color: {BG_ELEVATED}; border: 1px solid {BORDER_SUBTLE}; "
            f"border-radius: 10px; padding: 10px;"
        )
        hw_layout = QVBoxLayout(hw_card)
        hw_layout.setContentsMargins(10, 8, 10, 8)
        hw_layout.setSpacing(4)

        hw_title = QLabel("INFERENCE ENGINE")
        hw_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; font-weight: 800; letter-spacing: 0.8px;")
        hw_layout.addWidget(hw_title)

        self._hw_status_lbl = QLabel("● Snapdragon Ready")
        self._hw_status_lbl.setStyleSheet(f"color: {QUALCOMM_CYAN}; font-size: 11px; font-weight: 700;")
        hw_layout.addWidget(self._hw_status_lbl)

        self._offline_badge = QLabel("🔒 100% Local / Offline")
        self._offline_badge.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 11px; font-weight: 600;")
        hw_layout.addWidget(self._offline_badge)

        layout.addWidget(hw_card)

        return sidebar

    def _setup_shortcuts(self) -> None:
        """Register global navigation shortcuts (1-7)."""
        is_mac = platform.system() == "Darwin"
        mod = "Ctrl" if not is_mac else "Meta"

        for _, _, view_id, key in NAV_ITEMS:
            shortcut = QShortcut(QKeySequence(f"{mod}+{key}"), self)
            shortcut.activated.connect(lambda v=view_id: self._navigate(v))

    def _init_views(self) -> None:
        from app.ui.study_desk_view import StudyDeskView
        from app.ui.dashboard import DashboardView
        from app.ui.library_view import LibraryView
        from app.ui.chat_view import ChatView
        from app.ui.study_tools_view import StudyToolsView
        from app.ui.audio_view import AudioView
        from app.ui.benchmark_view import BenchmarkView
        from app.ui.settings_view import SettingsView

        view_map = {
            "desk": StudyDeskView(self.ctx, self),
            "dashboard": DashboardView(self.ctx, self),
            "library": LibraryView(self.ctx, self),
            "chat": ChatView(self.ctx, self),
            "study": StudyToolsView(self.ctx, self),
            "audio": AudioView(self.ctx, self),
            "benchmark": BenchmarkView(self.ctx, self),
            "settings": SettingsView(self.ctx, self),
        }
        for view_id, view in view_map.items():
            self._views[view_id] = view
            self._content_stack.addWidget(view)

    def _navigate(self, view_id: str) -> None:
        if view_id not in self._views:
            return
        self._current_view = view_id

        # Update sidebar highlights
        for vid, btn in self._nav_buttons.items():
            btn.setProperty("active", str(vid == view_id).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Switch content
        self._content_stack.setCurrentWidget(self._views[view_id])

        # Notify view
        view = self._views[view_id]
        if hasattr(view, "on_enter"):
            view.on_enter()

    def _update_status_bar(self) -> None:
        offline = self.ctx.settings.offline_mode
        if offline:
            self._status_bar.showMessage("OFFLINE AIRPLANE MODE ACTIVE  •  Network completely gated  •  All AI inference executes on-device")
            self._offline_badge.setText("✈️ Strict Offline Mode")
            self._offline_badge.setStyleSheet(f"color: {STATUS_AMBER}; font-size: 11px; font-weight: 700;")
        else:
            self._status_bar.showMessage("EdgeScholar v0.1.0  •  Snapdragon AI Lab Build & Present Challenge  •  Local QNN & FAISS Active")
            self._offline_badge.setText("🔒 100% Local / Offline")
            self._offline_badge.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 11px; font-weight: 600;")

    def navigate_to(self, view_id: str) -> None:
        self._navigate(view_id)

    def refresh_status(self) -> None:
        self._update_status_bar()
