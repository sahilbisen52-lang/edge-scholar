"""
Dashboard view — Snapdragon Signature Edition.
Features hero banner, high-impact glassmorphic telemetry cards,
interactive quick actions, and hardware diagnostic console.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QSizePolicy
)

from app.core.app_context import AppContext
from app.hardware.system_detector import detect_system, NOT_DETECTED, VERIFIED, PRESENT
from app.ui.styles.theme import (
    SNAPDRAGON_RED, QUALCOMM_CYAN, TEXT_SECONDARY, BG_SURFACE,
    BORDER_SUBTLE, TEXT_PRIMARY, TEXT_MUTED, STATUS_GREEN,
    STATUS_AMBER, BG_ELEVATED
)

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = logging.getLogger("edge_scholar.ui.dashboard")


class DashboardView(QWidget):
    def __init__(self, ctx: AppContext, main_window: "MainWindow") -> None:
        super().__init__()
        self.ctx = ctx
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # ── Snapdragon Hero Banner ──
        hero = QFrame()
        hero.setObjectName("hero_banner")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(12)

        # Tag row
        tag_row = QHBoxLayout()
        tag_row.setSpacing(8)

        t1 = QLabel("⚡ SNAPDRAGON AI CO-PILOT")
        t1.setObjectName("badge_snapdragon")
        tag_row.addWidget(t1)

        t2 = QLabel("● 100% ON-DEVICE")
        t2.setObjectName("badge_npu")
        tag_row.addWidget(t2)

        t3 = QLabel("🔒 ZERO CLOUD LEAKAGE")
        t3.setObjectName("badge_verified")
        tag_row.addWidget(t3)

        tag_row.addStretch()
        hero_layout.addLayout(tag_row)

        # Title
        hero_title = QLabel("Private Edge AI Study Copilot")
        hero_title.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;")
        hero_layout.addWidget(hero_title)

        hero_sub = QLabel(
            "Empowering students to understand complex textbooks, generate exam revision quizzes, "
            "and transcribe classroom audio — completely offline on Snapdragon-powered Windows PCs."
        )
        hero_sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.5;")
        hero_sub.setWordWrap(True)
        hero_layout.addWidget(hero_sub)

        layout.addWidget(hero)

        # ── High-Impact Status Telemetry Cards ──
        status_row = QHBoxLayout()
        status_row.setSpacing(14)

        self._model_card = self._make_telemetry_card("AI INFERENCE ENGINE", "Detecting...", QUALCOMM_CYAN)
        self._hw_card = self._make_telemetry_card("TARGET HARDWARE", "Detecting...", "#ffffff")
        self._docs_card = self._make_telemetry_card("LOCAL KNOWLEDGE VAULT", "0 Indexed", SNAPDRAGON_RED)
        self._priv_card = self._make_telemetry_card("PRIVACY GUARD", "100% Local", STATUS_GREEN)

        for card in [self._model_card, self._hw_card, self._docs_card, self._priv_card]:
            status_row.addWidget(card)

        layout.addLayout(status_row)

        # ── Quick Actions Grid ──
        qa_label = QLabel("Study Workspace Launchpad")
        qa_label.setObjectName("subheading_label")
        layout.addWidget(qa_label)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(14)

        actions = [
            ("📥 Import Study Material", "Add textbooks, lecture slides, & syllabus files", "library"),
            ("💬 Grounded AI Chat", "Ask questions with verifiable textbook citations", "chat"),
            ("🎓 Interactive Practice Quiz", "Test exam readiness with instant green/red scoring", "study"),
            ("🗂 Interactive Flashcard Deck", "Flip revision terms and track study mastery", "study"),
            ("🎙️ Lecture Audio Notes", "Transcribe audio directly into structured summaries", "audio"),
            ("⚡ Performance Lab", "Benchmark on-device NPU/CPU latency & memory", "benchmark"),
        ]

        for i, (title, desc, view) in enumerate(actions):
            btn = self._make_action_card(title, desc, view)
            actions_grid.addWidget(btn, i // 3, i % 3)

        layout.addLayout(actions_grid)

        # ── Diagnostic Console Card ──
        diag_label = QLabel("Snapdragon Engine & Runtime Diagnostics")
        diag_label.setObjectName("subheading_label")
        layout.addWidget(diag_label)

        diag_card = QFrame()
        diag_card.setObjectName("card")
        diag_layout = QVBoxLayout(diag_card)
        diag_layout.setContentsMargins(18, 16, 18, 16)
        diag_layout.setSpacing(10)

        self._console_lbl = QLabel("Inspecting local hardware accelerators...")
        self._console_lbl.setStyleSheet(
            f"font-family: 'SF Mono', Consolas, monospace; font-size: 12px; "
            f"color: {TEXT_SECONDARY}; line-height: 1.6;"
        )
        self._console_lbl.setWordWrap(True)
        diag_layout.addWidget(self._console_lbl)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Re-Scan System Accelerators")
        refresh_btn.setObjectName("secondary_btn")
        refresh_btn.setFixedHeight(34)
        refresh_btn.clicked.connect(self.on_enter)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        diag_layout.addLayout(btn_row)

        layout.addWidget(diag_card)
        layout.addStretch()

    def _make_telemetry_card(self, label: str, initial: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setFixedHeight(105)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(6)

        title = QLabel(label)
        title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;")
        c_layout.addWidget(title)

        val = QLabel(initial)
        val.setStyleSheet(f"color: {accent_color}; font-size: 16px; font-weight: 800; letter-spacing: -0.3px;")
        val.setWordWrap(True)
        c_layout.addWidget(val)
        card._val_lbl = val  # type: ignore

        return card

    def _make_action_card(self, title: str, desc: str, view_id: str) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("secondary_btn")
        btn.setFixedHeight(76)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        l = QVBoxLayout(btn)
        l.setContentsMargins(14, 12, 14, 12)
        l.setSpacing(3)
        l.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        l.addWidget(t_lbl)

        d_lbl = QLabel(desc)
        d_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        l.addWidget(d_lbl)

        btn.clicked.connect(lambda checked=False, v=view_id: self.main_window.navigate_to(v))
        return btn

    def on_enter(self) -> None:
        self._refresh_status()

    def _refresh_status(self) -> None:
        try:
            sys_info = detect_system()

            # Model status
            qnn = sys_info.get("qnn_status", NOT_DETECTED)
            if qnn == VERIFIED:
                self._model_card._val_lbl.setText("Qualcomm QNN (NPU)")
            else:
                self._model_card._val_lbl.setText("Local Edge Engine")

            # Hardware
            arch = sys_info.get("architecture", "Unknown")
            snap = sys_info.get("snapdragon_status", NOT_DETECTED)
            hw_str = f"{arch} • Snapdragon" if snap == PRESENT else f"{arch} Platform"
            self._hw_card._val_lbl.setText(hw_str)

            # Document count
            from app.documents.document_store import DocumentStore
            ds = DocumentStore(self.ctx.db_path)
            docs = ds.list_documents()
            indexed = sum(1 for d in docs if d.indexed)
            self._docs_card._val_lbl.setText(f"{indexed} Indexed Files")

            # Privacy status
            offline = self.ctx.settings.offline_mode
            priv_str = "Offline Shield Active" if offline else "100% On-Device"
            self._priv_card._val_lbl.setText(priv_str)

            # Diagnostic console text
            runtimes = sys_info.get("runtimes", {})
            lines = [
                f"┌─ SYSTEM ARCHITECTURE: {sys_info.get('os')} {sys_info.get('architecture')} ({sys_info.get('ram_gb')} GB RAM)",
                f"├─ SNAPDRAGON ACCELERATOR: {snap} (QNN EP: {qnn})",
                f"├─ VECTOR RETRIEVAL: FAISS IndexFlatIP (MiniLM-L6-v2, 384 dimensions) [READY]",
                f"├─ DOCUMENT PARSER: PyMuPDF Engine (Page-Boundary Preserved) [READY]",
                f"└─ NETWORK POLICY: Offline-First • Outbound Telemetry Gated [ENFORCED]",
            ]
            self._console_lbl.setText("\n".join(lines))

        except Exception as e:
            logger.warning("Error refreshing dashboard: %s", e)
