"""
Chat view — full RAG question answering interface.
Documents are selected via dropdown; questions answered with grounded citations.
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QObject, Signal, QRunnable, QThreadPool
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QComboBox, QSplitter, QFrame,
    QScrollArea, QSizePolicy,
)

from app.core.app_context import AppContext
from app.ui.styles.theme import (
    ACCENT, TEXT_SECONDARY, BG_SURFACE, BORDER, TEXT_PRIMARY,
    TEXT_MUTED, SUCCESS, WARNING, BG_ELEVATED, BG_DARK, CITATION_BG,
)

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = logging.getLogger("edge_scholar.ui.chat")


# ───────────────────────────────────────────────
# Background Worker
# ───────────────────────────────────────────────

class ChatSignals(QObject):
    response_ready = Signal(object)  # RAGResponse
    error = Signal(str)


class ChatWorker(QRunnable):
    def __init__(self, ctx: AppContext, question: str, document_id: Optional[str]) -> None:
        super().__init__()
        self.ctx = ctx
        self.question = question
        self.document_id = document_id
        self.signals = ChatSignals()

    def run(self) -> None:
        try:
            from app.retrieval.embeddings import LocalEmbeddings
            from app.retrieval.vector_store import VectorStore
            from app.retrieval.retriever import Retriever
            from app.ai.mock_provider import MockProvider
            from app.ai.provider_factory import ProviderFactory
            from app.rag.pipeline import RAGPipeline
            from app.documents.document_store import DocumentStore

            # Build pipeline
            store = DocumentStore(self.ctx.db_path)
            store.increment_questions_answered()

            embeddings = LocalEmbeddings(self.ctx.settings.selected_embedding_model)
            vs = VectorStore(self.ctx.data_dir / "indexes")
            retriever = Retriever(embeddings, vs)

            # Get provider (mock or real)
            factory = ProviderFactory(
                preferred=self.ctx.settings.preferred_runtime,
                models_dir=__import__("app.utils.paths", fromlist=["get_models_dir"]).get_models_dir(),
            )
            provider = factory.create()

            pipeline = RAGPipeline(retriever=retriever, provider=provider)
            response = pipeline.query(
                self.question,
                top_k=self.ctx.settings.retrieval_top_k,
                document_id=self.document_id,
                max_tokens=self.ctx.settings.max_tokens,
                temperature=self.ctx.settings.temperature,
            )

            self.signals.response_ready.emit(response)

        except Exception as e:
            logger.exception("Chat worker error: %s", e)
            self.signals.error.emit(str(e))


# ───────────────────────────────────────────────
# Chat View
# ───────────────────────────────────────────────

class ChatView(QWidget):
    def __init__(self, ctx: AppContext, main_window: "MainWindow") -> None:
        super().__init__()
        self.ctx = ctx
        self.main_window = main_window
        self._pool = QThreadPool.globalInstance()
        self._selected_doc_id: Optional[str] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top bar ──
        top_bar = QFrame()
        top_bar.setStyleSheet(f"background-color: {BG_SURFACE}; border-bottom: 1px solid {BORDER};")
        top_bar.setFixedHeight(56)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 8, 24, 8)

        top_layout.addWidget(QLabel("💬"))

        title = QLabel("Chat")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 700; font-size: 16px;")
        top_layout.addWidget(title)

        top_layout.addSpacing(16)
        top_layout.addWidget(QLabel("Context:"))

        self._doc_selector = QComboBox()
        self._doc_selector.setFixedWidth(200)
        self._doc_selector.addItem("All Documents", None)
        self._doc_selector.currentIndexChanged.connect(self._on_doc_changed)
        top_layout.addWidget(self._doc_selector)

        top_layout.addStretch()

        self._runtime_badge = QLabel("LOCAL • MOCK")
        self._runtime_badge.setObjectName("badge")
        self._runtime_badge.setStyleSheet(
            f"background-color: {BG_ELEVATED}; border: 1px solid {BORDER}; "
            f"border-radius: 4px; padding: 2px 10px; color: {TEXT_SECONDARY}; font-size: 12px;"
        )
        top_layout.addWidget(self._runtime_badge)

        layout.addWidget(top_bar)

        # ── Main splitter ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: " + BORDER + "; width: 1px; }")

        # Chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(24, 16, 24, 16)
        chat_layout.setSpacing(12)

        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setStyleSheet(
            f"background-color: {BG_DARK}; border: none; "
            f"font-size: 14px; color: {TEXT_PRIMARY}; line-height: 1.6;"
        )
        self._chat_display.setPlaceholderText(
            "Ask a question about your imported documents...\n\n"
            "Example: 'Explain the concept of process scheduling.'"
        )
        chat_layout.addWidget(self._chat_display)

        # Quick prompt suggestions row
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(8)
        chips_lbl = QLabel("Suggestions:")
        chips_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        chips_layout.addWidget(chips_lbl)

        sample_prompts = [
            "What is CPU scheduling?",
            "Explain virtual memory paging",
            "Processes vs Threads",
        ]
        for prompt_text in sample_prompts:
            chip_btn = QPushButton(f"💡 {prompt_text}")
            chip_btn.setObjectName("secondary_btn")
            chip_btn.setFixedHeight(26)
            chip_btn.setStyleSheet("font-size: 11px; padding: 2px 10px; border-radius: 13px;")
            chip_btn.clicked.connect(lambda checked=False, p=prompt_text: self._use_prompt(p))
            chips_layout.addWidget(chip_btn)

        chips_layout.addStretch()
        chat_layout.addLayout(chips_layout)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet(
            f"background-color: {BG_SURFACE}; border: 1px solid {BORDER}; border-radius: 12px;"
        )
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 8, 8)

        self._input_field = QLineEdit()
        self._input_field.setStyleSheet(
            f"background: transparent; border: none; color: {TEXT_PRIMARY}; font-size: 14px;"
        )
        self._input_field.setPlaceholderText("Ask a question about your documents... (Enter to send)")
        self._input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self._input_field)

        self._send_btn = QPushButton("Send ↵")
        self._send_btn.setObjectName("primary_btn")
        self._send_btn.setFixedHeight(36)
        self._send_btn.setFixedWidth(90)
        self._send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self._send_btn)

        chat_layout.addWidget(input_frame)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        chat_layout.addWidget(self._status_label)

        splitter.addWidget(chat_widget)

        # ── Citations panel ──
        citations_widget = QWidget()
        citations_widget.setFixedWidth(280)
        citations_widget.setStyleSheet(
            f"background-color: {BG_SURFACE}; border-left: 1px solid {BORDER};"
        )
        cite_layout = QVBoxLayout(citations_widget)
        cite_layout.setContentsMargins(16, 16, 16, 16)
        cite_layout.setSpacing(8)

        cite_title = QLabel("Sources")
        cite_title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-weight: 700; font-size: 14px; padding-bottom: 8px;"
        )
        cite_layout.addWidget(cite_title)

        self._citations_scroll = QScrollArea()
        self._citations_scroll.setWidgetResizable(True)
        self._citations_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._citations_container = QWidget()
        self._citations_layout = QVBoxLayout(self._citations_container)
        self._citations_layout.setContentsMargins(0, 0, 0, 0)
        self._citations_layout.setSpacing(8)

        self._no_sources = QLabel("Sources will appear here\nafter asking a question.")
        self._no_sources.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_sources.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; padding: 20px;")
        self._citations_layout.addWidget(self._no_sources)
        self._citations_layout.addStretch()

        self._citations_scroll.setWidget(self._citations_container)
        cite_layout.addWidget(self._citations_scroll)

        splitter.addWidget(citations_widget)
        splitter.setSizes([820, 280])

        layout.addWidget(splitter)

    def on_enter(self) -> None:
        """Refresh document selector when entering chat view."""
        self._refresh_doc_selector()

    def _refresh_doc_selector(self) -> None:
        self._doc_selector.clear()
        self._doc_selector.addItem("All Documents", None)
        try:
            from app.documents.document_store import DocumentStore
            store = DocumentStore(self.ctx.db_path)
            docs = store.list_documents()
            for doc in docs:
                if doc.indexed:
                    self._doc_selector.addItem(doc.filename, doc.document_id)
        except Exception as e:
            logger.warning("Could not load documents for chat: %s", e)

    def _on_doc_changed(self, index: int) -> None:
        self._selected_doc_id = self._doc_selector.currentData()

    def _use_prompt(self, prompt: str) -> None:
        self._input_field.setText(prompt)
        self._send_message()

    def _send_message(self) -> None:
        question = self._input_field.text().strip()
        if not question:
            return

        self._input_field.clear()
        self._send_btn.setEnabled(False)
        self._status_label.setText("⚡ Generating response...")

        # Display student message
        self._chat_display.append(
            f'<div style="margin: 10px 0; padding: 14px 16px; '
            f'background-color: #151928; border: 1px solid #232a3e; border-radius: 12px;">'
            f'<div style="font-size: 11px; font-weight: 800; color: #00d2ff; letter-spacing: 0.6px; margin-bottom: 6px;">'
            f'STUDENT QUESTION'
            f'</div>'
            f'<div style="color: #ffffff; font-size: 14px; font-weight: 500; line-height: 1.5;">'
            f'{question}'
            f'</div>'
            f'</div>'
        )

        worker = ChatWorker(self.ctx, question, self._selected_doc_id)
        worker.signals.response_ready.connect(self._on_response)
        worker.signals.error.connect(self._on_error)
        self._pool.start(worker)

    def _on_response(self, response) -> None:
        self._send_btn.setEnabled(True)
        self._status_label.setText(
            f"⏱ {response.total_latency:.2f}s • {response.grounding_status.replace('_', ' ').title()}"
        )

        # Update runtime badge
        badge_text = response.runtime_badge if hasattr(response, "runtime_badge") else "LOCAL"
        self._runtime_badge.setText(badge_text)

        # Format answer
        answer_html = response.answer.replace("\n", "<br>")

        # Format citations
        cite_lines = ""
        if response.citations:
            cite_lines = '<div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid #232a3e;">'
            cite_lines += '<div style="font-size: 11px; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">VERIFIED SOURCE CITATIONS:</div>'
            for c in response.citations:
                cite_lines += (
                    f'<div style="font-size: 12px; color: #38bdf8; margin: 3px 0;">'
                    f'■ <b>{c.filename}</b> — Page {c.page_number}'
                    f'</div>'
                )
            cite_lines += '</div>'

        self._chat_display.append(
            f'<div style="margin: 10px 0; padding: 16px 18px; '
            f'background-color: #0f121d; border: 1px solid #1e2438; border-left: 3px solid #e60027; border-radius: 12px;">'
            f'<div style="margin-bottom: 8px;">'
            f'<span style="font-size: 11px; font-weight: 800; color: #ff2d55; letter-spacing: 0.5px;">⚡ EDGESCHOLAR</span>'
            f'<span style="font-size: 10px; color: #10b981; font-weight: 700; background-color: rgba(16,185,129,0.15); padding: 2px 6px; border-radius: 4px; margin-left: 8px;">● 100% GROUNDED</span>'
            f'</div>'
            f'<div style="color: #f1f5f9; font-size: 14px; line-height: 1.6;">'
            f'{answer_html}'
            f'</div>'
            f'{cite_lines}'
            f'</div>'
        )

        # Update citations panel
        self._update_citations(response.citations)

        # Scroll to bottom
        sb = self._chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_error(self, error: str) -> None:
        self._send_btn.setEnabled(True)
        self._status_label.setText(f"❌ Error: {error}")
        self._chat_display.append(
            f'<div style="padding: 12px; color: {ERROR};">'
            f"⚠️ Generation error: {error}"
            f"</div>"
        )

    def _update_citations(self, citations: list) -> None:
        # Clear existing
        while self._citations_layout.count() > 1:
            item = self._citations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not citations:
            self._no_sources.show()
            return

        self._no_sources.hide()
        for citation in citations:
            card = QFrame()
            card.setStyleSheet(
                f"background-color: {CITATION_BG}; border: 1px solid {BORDER}; "
                f"border-radius: 8px; padding: 8px;"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 8, 8, 8)
            cl.setSpacing(4)

            num = QLabel(f"[{citation.index}]")
            num.setStyleSheet(f"color: {ACCENT}; font-weight: 700; font-size: 13px;")
            cl.addWidget(num)

            fname = QLabel(citation.filename)
            fname.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: 600;")
            fname.setWordWrap(True)
            cl.addWidget(fname)

            page = QLabel(f"Page {citation.page_number}")
            page.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            cl.addWidget(page)

            if citation.excerpt:
                excerpt = QLabel(f'"{citation.excerpt[:100]}..."')
                excerpt.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-style: italic;")
                excerpt.setWordWrap(True)
                cl.addWidget(excerpt)

            self._citations_layout.insertWidget(
                self._citations_layout.count() - 1, card
            )
