"""
Settings view — Configuration for AI runtime, privacy controls, storage, and model management.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QMessageBox, QGroupBox, QScrollArea,
    QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame
)

from app.core.app_context import AppContext
from app.privacy.local_storage import LocalStorageInfo
from app.privacy.deletion import DeletionManager
from app.hardware.system_detector import detect_system, VERIFIED, PRESENT, NOT_DETECTED
from app.ai.model_manager import ModelManager
from app.ui.styles.theme import (
    ACCENT, TEXT_SECONDARY, BG_SURFACE, BORDER, TEXT_PRIMARY,
    TEXT_MUTED, SUCCESS, WARNING, ERROR, BG_ELEVATED, BG_DARK
)

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = logging.getLogger("edge_scholar.ui.settings")


class SettingsView(QWidget):
    def __init__(self, ctx: AppContext, main_window: "MainWindow") -> None:
        super().__init__()
        self.ctx = ctx
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header
        top_row = QHBoxLayout()
        header = QLabel("Settings & Diagnostics")
        header.setObjectName("heading_label")
        top_row.addWidget(header)
        top_row.addStretch()

        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.setFixedHeight(36)
        self.save_btn.clicked.connect(self._save_settings)
        top_row.addWidget(self.save_btn)
        layout.addLayout(top_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        s_layout = QVBoxLayout(container)
        s_layout.setContentsMargins(0, 0, 16, 0)
        s_layout.setSpacing(16)

        # ── Group 1: AI Runtime & Models ──
        gb_ai = QGroupBox("AI Inference Runtime")
        gb_ai.setStyleSheet(f"font-weight: 600; color: {TEXT_PRIMARY};")
        ai_layout = QVBoxLayout(gb_ai)
        ai_layout.setSpacing(12)

        p_row = QHBoxLayout()
        p_row.addWidget(QLabel("Preferred Runtime Backend:"))
        self.provider_cb = QComboBox()
        self.provider_cb.addItem("Auto-Detect Best Available", "auto")
        self.provider_cb.addItem("Qualcomm QNN (Snapdragon NPU)", "qnn")
        self.provider_cb.addItem("llama.cpp (Local CPU/GPU GGUF)", "llama_cpp")
        self.provider_cb.addItem("ONNX Runtime", "onnx")
        self.provider_cb.addItem("Mock Provider (Dev Fallback)", "mock")
        p_row.addWidget(self.provider_cb)
        p_row.addStretch()
        ai_layout.addLayout(p_row)

        # Generation params
        params_row = QHBoxLayout()
        params_row.addWidget(QLabel("Temperature:"))
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.5)
        self.temp_spin.setSingleStep(0.05)
        self.temp_spin.setValue(self.ctx.settings.temperature)
        params_row.addWidget(self.temp_spin)

        params_row.addSpacing(20)
        params_row.addWidget(QLabel("Max Output Tokens:"))
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(64, 4096)
        self.tokens_spin.setSingleStep(64)
        self.tokens_spin.setValue(self.ctx.settings.max_tokens)
        params_row.addWidget(self.tokens_spin)

        params_row.addSpacing(20)
        params_row.addWidget(QLabel("Retrieval Top-K:"))
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 20)
        self.topk_spin.setValue(self.ctx.settings.retrieval_top_k)
        params_row.addWidget(self.topk_spin)

        params_row.addStretch()
        ai_layout.addLayout(params_row)

        s_layout.addWidget(gb_ai)

        # ── Group 2: Privacy & Offline Controls ──
        gb_priv = QGroupBox("Privacy & Offline Controls")
        gb_priv.setStyleSheet(f"font-weight: 600; color: {TEXT_PRIMARY};")
        priv_layout = QVBoxLayout(gb_priv)
        priv_layout.setSpacing(12)

        self.offline_cb = QCheckBox("Enable Strict Offline Mode (blocks all outgoing network requests)")
        self.offline_cb.setChecked(self.ctx.settings.offline_mode)
        self.offline_cb.toggled.connect(self._toggle_offline)
        priv_layout.addWidget(self.offline_cb)

        # Storage info label
        self.storage_info_lbl = QLabel("Loading local storage stats...")
        self.storage_info_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        priv_layout.addWidget(self.storage_info_lbl)

        del_row = QHBoxLayout()
        self.del_data_btn = QPushButton("🗑 Delete All Local Data")
        self.del_data_btn.setObjectName("secondary_btn")
        self.del_data_btn.setStyleSheet(f"color: {ERROR}; border-color: {ERROR};")
        self.del_data_btn.setFixedHeight(36)
        self.del_data_btn.clicked.connect(self._delete_data)
        del_row.addWidget(self.del_data_btn)
        del_row.addStretch()
        priv_layout.addLayout(del_row)

        s_layout.addWidget(gb_priv)

        # ── Group 3: Hardware Diagnostics ──
        gb_hw = QGroupBox("Hardware & Environment Diagnostics")
        gb_hw.setStyleSheet(f"font-weight: 600; color: {TEXT_PRIMARY};")
        hw_layout = QVBoxLayout(gb_hw)

        self.hw_details_lbl = QLabel("Loading system diagnostics...")
        self.hw_details_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.4;")
        hw_layout.addWidget(self.hw_details_lbl)
        s_layout.addWidget(gb_hw)

        # ── Group 4: Model Manifest & Directory ──
        gb_models = QGroupBox("Model Manifest (Qualcomm AI Hub & Open-Source)")
        gb_models.setStyleSheet(f"font-weight: 600; color: {TEXT_PRIMARY};")
        models_layout = QVBoxLayout(gb_models)

        self.models_table = QTableWidget(0, 5)
        self.models_table.setHorizontalHeaderLabels(["Model Name", "Runtime", "Precision", "Target", "Status"])
        self.models_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.models_table.setFixedHeight(140)
        models_layout.addWidget(self.models_table)
        s_layout.addWidget(gb_models)

        # ── Group 5: Competition & Attribution ──
        gb_about = QGroupBox("About EdgeScholar & Competition Context")
        gb_about.setStyleSheet(f"font-weight: 600; color: {TEXT_PRIMARY};")
        about_layout = QVBoxLayout(gb_about)

        about_text = (
            "<b>EdgeScholar — Private On-Device AI Study Copilot (v0.1.0)</b><br>"
            "An independent student project developed for the Qualcomm Snapdragon AI Lab "
            "Build & Present Challenge.<br><br>"
            "<b>Important Positioning & Trademarks:</b><br>"
            "• Offline-first edge AI architecture intended for Snapdragon-powered Windows PCs.<br>"
            "• EdgeScholar is an independent student project and is NOT officially endorsed by Qualcomm or HP.<br>"
            "• 'Snapdragon', 'Qualcomm', and 'QNN' are trademarks of Qualcomm Technologies, Inc."
        )
        lbl_about = QLabel(about_text)
        lbl_about.setTextFormat(Qt.TextFormat.RichText)
        lbl_about.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.5;")
        about_layout.addWidget(lbl_about)
        s_layout.addWidget(gb_about)

        s_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self._refresh_all()

    def on_enter(self) -> None:
        self._refresh_all()

    def _refresh_all(self) -> None:
        # Preferred provider
        idx = self.provider_cb.findData(self.ctx.settings.preferred_runtime)
        if idx >= 0:
            self.provider_cb.setCurrentIndex(idx)

        # Offline
        self.offline_cb.setChecked(self.ctx.settings.offline_mode)

        # Storage
        info = LocalStorageInfo(self.ctx.data_dir).describe()
        self.storage_info_lbl.setText(
            f"Storage Location: {info['data_directory']}\n"
            f"Disk Usage: {info['total_size_mb']} MB  |  Documents: {info['document_count']}  |  "
            f"Telemetry: Disabled  |  Cloud AI: Disabled"
        )

        # Hardware diagnostics
        try:
            sys_info = detect_system()
            lines = [
                f"Operating System: {sys_info.get('os')} ({sys_info.get('architecture')})",
                f"Processor: {sys_info.get('processor')}",
                f"RAM: {sys_info.get('ram_gb')} GB (Available: {sys_info.get('ram_available_gb')} GB)",
                f"Snapdragon Status: {sys_info.get('snapdragon_status', NOT_DETECTED)}",
                f"QNN Runtime: {sys_info.get('qnn_status', NOT_DETECTED)}",
                f"NPU Accelerator: {sys_info.get('npu_status', NOT_DETECTED)}",
            ]
            self.hw_details_lbl.setText("\n".join(lines))
        except Exception as e:
            self.hw_details_lbl.setText(f"Error querying hardware: {e}")

        # Model manifest
        try:
            mm = ModelManager(self.ctx.data_dir.parent / "models")
            models = mm.list_models()
            self.models_table.setRowCount(0)
            for m in models:
                row = self.models_table.rowCount()
                self.models_table.insertRow(row)
                self.models_table.setItem(row, 0, QTableWidgetItem(m.name))
                self.models_table.setItem(row, 1, QTableWidgetItem(m.runtime))
                self.models_table.setItem(row, 2, QTableWidgetItem(m.precision))
                self.models_table.setItem(row, 3, QTableWidgetItem(m.target_chipset))
                self.models_table.setItem(row, 4, QTableWidgetItem(m.status.capitalize()))
        except Exception as e:
            logger.warning("Could not list model manifest: %s", e)

    def _toggle_offline(self, checked: bool) -> None:
        self.ctx.settings.offline_mode = checked
        self.ctx.save_settings()
        self.main_window.refresh_status()

    def _save_settings(self) -> None:
        self.ctx.settings.preferred_runtime = self.provider_cb.currentData()
        self.ctx.settings.temperature = self.temp_spin.value()
        self.ctx.settings.max_tokens = self.tokens_spin.value()
        self.ctx.settings.retrieval_top_k = self.topk_spin.value()
        self.ctx.settings.offline_mode = self.offline_cb.isChecked()
        self.ctx.save_settings()
        self.main_window.refresh_status()
        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    def _delete_data(self) -> None:
        reply = QMessageBox.question(
            self, "Confirm Data Deletion",
            "Are you sure you want to permanently delete ALL local documents, indexes, "
            "embeddings, transcripts, and benchmarks?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            mgr = DeletionManager(self.ctx.data_dir)
            mgr.delete_all_data(keep_exports=True)
            self._refresh_all()
            QMessageBox.information(
                self, "Data Cleared",
                "All application data has been purged from this device."
            )
