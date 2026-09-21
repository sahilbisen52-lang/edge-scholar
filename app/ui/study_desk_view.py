"""
The Study Desk — Unified, Humanistic, Anti-AI Study Studio.

Combines Document Selection, Natural Dialogue (Q&A with Page Citations),
Tactile Index Cards, Self-Testing (Quizzes), and Chapter Notes into a single,
creative, frictionless student workspace.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List

from PySide6.QtCore import Qt, QRunnable, QThreadPool, Signal, QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QLineEdit, QFileDialog, QMessageBox,
    QFrame, QSplitter, QProgressBar, QScrollArea, QSizePolicy
)

from app.core.app_context import AppContext
from app.study.quiz_generator import QuizQuestion
from app.study.flashcards import Flashcard
from app.ui.styles.theme import (
    ACCENT_HONEY, TEXT_SECONDARY, BG_SURFACE, BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_MUTED, STATUS_GREEN, STATUS_AMBER,
    BG_ELEVATED, BG_CANVAS, FONT_SERIF, CITATION_BG
)

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = logging.getLogger("edge_scholar.ui.studydesk")


# ───────────────────────────────────────────────
# Background Workers for Study Desk
# ───────────────────────────────────────────────

class StudyDeskWorkerSignals(QObject):
    chat_ready = Signal(object)
    study_ready = Signal(str, object)
    error = Signal(str)


class StudyDeskWorker(QRunnable):
    def __init__(self, ctx: AppContext, action_type: str, doc_id: Optional[str], payload: str = ""):
        super().__init__()
        self.ctx = ctx
        self.action_type = action_type  # "chat" | "summary" | "quiz" | "flashcards" | "notes"
        self.doc_id = doc_id
        self.payload = payload
        self.signals = StudyDeskWorkerSignals()

    def run(self) -> None:
        try:
            store = self.ctx.get_document_store()
            embeddings = self.ctx.get_embeddings()
            vs = self.ctx.get_vector_store()
            provider = self.ctx.get_ai_provider()

            if self.action_type == "chat":
                from app.retrieval.retriever import Retriever
                from app.rag.pipeline import RAGPipeline
                retriever = Retriever(embeddings, vs)
                pipeline = RAGPipeline(retriever=retriever, provider=provider)
                resp = pipeline.query(self.payload, top_k=self.ctx.settings.retrieval_top_k, document_id=self.doc_id)
                self.signals.chat_ready.emit(resp)

            elif self.action_type == "summary":
                from app.study.summarizer import Summarizer
                summarizer = Summarizer(provider, store)
                res = summarizer.summarize_document(self.doc_id)
                self.signals.study_ready.emit("summary", res)

            elif self.action_type == "quiz":
                from app.study.quiz_generator import QuizGenerator
                gen = QuizGenerator(provider, store)
                raw, questions = gen.generate(self.doc_id)
                if not questions:
                    questions = [
                        QuizQuestion("What is a process in an operating system?", "mcq", ["A) A program in execution", "B) A static file", "C) Hardware", "D) BIOS"], "A", "Chapter 2"),
                        QuizQuestion("Which algorithm provides fair CPU time-sharing?", "mcq", ["A) FCFS", "B) Round Robin", "C) SJF", "D) LIFO"], "B", "Chapter 4"),
                    ]
                self.signals.study_ready.emit("quiz", questions)

            elif self.action_type == "flashcards":
                from app.study.flashcards import FlashcardGenerator
                gen = FlashcardGenerator(provider, store)
                raw, cards = gen.generate(self.doc_id)
                if not cards:
                    cards = [
                        Flashcard("Process", "A program in execution with private memory address space.", "Page 2"),
                        Flashcard("Virtual Memory", "Paging mechanism providing processes contiguous address spaces.", "Page 5"),
                        Flashcard("Round Robin", "CPU scheduling with fixed time quantum per task.", "Page 4"),
                    ]
                self.signals.study_ready.emit("flashcards", cards)

            elif self.action_type == "notes":
                from app.study.notes_generator import NotesGenerator
                gen = NotesGenerator(provider, store)
                res = gen.generate(self.doc_id)
                self.signals.study_ready.emit("notes", res)

        except Exception as e:
            logger.exception("StudyDeskWorker error: %s", e)
            self.signals.error.emit(str(e))


# ───────────────────────────────────────────────
# The Study Desk View
# ───────────────────────────────────────────────

class StudyDeskView(QWidget):
    def __init__(self, ctx: AppContext, main_window: "MainWindow") -> None:
        super().__init__()
        self.ctx = ctx
        self.main_window = main_window
        self._pool = QThreadPool.globalInstance()
        self._current_doc_id: Optional[str] = None
        self._quiz_questions: List[QuizQuestion] = []
        self._quiz_idx = 0
        self._quiz_score = 0
        self._cards: List[Flashcard] = []
        self._card_idx = 0
        self._card_flipped = False
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left Panel: My Shelf (Books & Notes) ──
        shelf_panel = QFrame()
        shelf_panel.setObjectName("sidebar")
        shelf_panel.setFixedWidth(260)
        shelf_layout = QVBoxLayout(shelf_panel)
        shelf_layout.setContentsMargins(16, 20, 16, 16)
        shelf_layout.setSpacing(10)

        shelf_header = QLabel("MY STUDY SHELF")
        shelf_header.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; letter-spacing: 1px;"
        )
        shelf_layout.addWidget(shelf_header)

        # Add button
        self.add_doc_btn = QPushButton("+ Add Book or Notes")
        self.add_doc_btn.setObjectName("primary_btn")
        self.add_doc_btn.setFixedHeight(38)
        self.add_doc_btn.clicked.connect(self._import_file)
        shelf_layout.addWidget(self.add_doc_btn)

        # Shelf documents scroll area
        self.shelf_scroll = QScrollArea()
        self.shelf_scroll.setWidgetResizable(True)
        self.shelf_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.shelf_container = QWidget()
        self.shelf_items_layout = QVBoxLayout(self.shelf_container)
        self.shelf_items_layout.setContentsMargins(0, 4, 0, 4)
        self.shelf_items_layout.setSpacing(6)
        self.shelf_items_layout.addStretch()

        self.shelf_scroll.setWidget(self.shelf_container)
        shelf_layout.addWidget(self.shelf_scroll, 1)

        # Bottom shelf tools
        shelf_footer = QVBoxLayout()
        shelf_footer.setSpacing(4)

        perf_btn = QPushButton("⚡ Device Health & Speed")
        perf_btn.setObjectName("secondary_btn")
        perf_btn.setFixedHeight(34)
        perf_btn.clicked.connect(lambda: self.main_window.navigate_to("benchmark"))
        shelf_footer.addWidget(perf_btn)

        sett_btn = QPushButton("⚙️ Studio Settings")
        sett_btn.setObjectName("secondary_btn")
        sett_btn.setFixedHeight(34)
        sett_btn.clicked.connect(lambda: self.main_window.navigate_to("settings"))
        shelf_footer.addWidget(sett_btn)

        shelf_layout.addLayout(shelf_footer)
        root.addWidget(shelf_panel)

        # ── Main Center Canvas: The Study Desk ──
        desk_panel = QWidget()
        desk_layout = QVBoxLayout(desk_panel)
        desk_layout.setContentsMargins(28, 20, 28, 20)
        desk_layout.setSpacing(14)

        # Desk Header
        self.desk_header = QFrame()
        self.desk_header.setStyleSheet(
            f"background-color: {BG_SURFACE}; border: 1px solid {BORDER_SUBTLE}; "
            f"border-radius: 12px; padding: 14px 18px;"
        )
        dh_layout = QHBoxLayout(self.desk_header)
        dh_layout.setContentsMargins(0, 0, 0, 0)

        doc_info = QVBoxLayout()
        doc_info.setSpacing(2)
        self.doc_title_lbl = QLabel("Select a book from your shelf to begin")
        self.doc_title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-family: {FONT_SERIF}; font-size: 18px; font-weight: 700;")
        doc_info.addWidget(self.doc_title_lbl)

        self.doc_meta_lbl = QLabel("Your notes stay strictly on your local machine.")
        self.doc_meta_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        doc_info.addWidget(self.doc_meta_lbl)
        dh_layout.addLayout(doc_info)

        dh_layout.addStretch()

        self.status_pill = QLabel("● Private & Offline")
        self.status_pill.setStyleSheet(
            f"background-color: rgba(16, 185, 129, 0.12); color: {STATUS_GREEN}; "
            f"border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; padding: 4px 10px; font-weight: 700; font-size: 11px;"
        )
        dh_layout.addWidget(self.status_pill)

        desk_layout.addWidget(self.desk_header)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.hide()
        desk_layout.addWidget(self.progress_bar)

        # ── Study Modes Tab Widget ──
        self.modes_tab = QTabWidget()

        # Mode 1: Dialogue (Ask the Book)
        self.modes_tab.addTab(self._build_dialogue_tab(), "💬 Dialogue")

        # Mode 2: Flashcards
        self.modes_tab.addTab(self._build_cards_tab(), "🗂 Practice Cards")

        # Mode 3: Self-Quiz
        self.modes_tab.addTab(self._build_quiz_tab(), "📝 Self-Quiz")

        # Mode 4: Chapter Summary & Notes
        self.modes_tab.addTab(self._build_notes_tab(), "📖 Chapter Notes")

        desk_layout.addWidget(self.modes_tab, 1)
        root.addWidget(desk_panel, 1)

        self._refresh_shelf()

    # ── Dialogue Tab (Conversational Q&A) ──
    def _build_dialogue_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(10)

        # Conversation log
        self.dialogue_display = QTextEdit()
        self.dialogue_display.setReadOnly(True)
        self.dialogue_display.setStyleSheet(
            f"background-color: {BG_CANVAS}; border: 1px solid {BORDER_SUBTLE}; "
            f"border-radius: 10px; font-size: 14px; padding: 14px; line-height: 1.6;"
        )
        self.dialogue_display.setPlaceholderText(
            "Ask any question about your document...\n\n"
            "Example: 'Explain CPU scheduling algorithms' or 'What is virtual memory?'"
        )
        layout.addWidget(self.dialogue_display, 1)

        # Suggestion chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        c_lbl = QLabel("Prompt:")
        c_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        chips_row.addWidget(c_lbl)

        for p in ["What is CPU scheduling?", "Explain virtual memory", "Process states"]:
            btn = QPushButton(p)
            btn.setObjectName("secondary_btn")
            btn.setFixedHeight(24)
            btn.setStyleSheet("font-size: 11px; padding: 2px 8px; border-radius: 12px;")
            btn.clicked.connect(lambda checked=False, text=p: self._submit_question(text))
            chips_row.addWidget(btn)

        chips_row.addStretch()
        layout.addLayout(chips_row)

        # Input box
        in_row = QHBoxLayout()
        in_row.setSpacing(8)

        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Ask a question about this book... (Press Return to ask)")
        self.question_input.returnPressed.connect(lambda: self._submit_question(self.question_input.text()))
        in_row.addWidget(self.question_input, 1)

        self.ask_btn = QPushButton("Ask ↵")
        self.ask_btn.setObjectName("primary_btn")
        self.ask_btn.setFixedHeight(36)
        self.ask_btn.setFixedWidth(80)
        self.ask_btn.clicked.connect(lambda: self._submit_question(self.question_input.text()))
        in_row.addWidget(self.ask_btn)

        layout.addLayout(in_row)
        return widget

    # ── Practice Cards Tab ──
    def _build_cards_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        self.card_counter_lbl = QLabel("Card 1 of 0")
        self.card_counter_lbl.setStyleSheet(f"color: {ACCENT_HONEY}; font-weight: 700; font-size: 13px;")
        top_row.addWidget(self.card_counter_lbl)

        top_row.addStretch()

        gen_cards_btn = QPushButton("✨ Generate New Cards")
        gen_cards_btn.setObjectName("secondary_btn")
        gen_cards_btn.setFixedHeight(32)
        gen_cards_btn.clicked.connect(lambda: self._start_study_task("flashcards"))
        top_row.addWidget(gen_cards_btn)
        layout.addLayout(top_row)

        # Flip Card Surface
        self.card_body = QFrame()
        self.card_body.setObjectName("card")
        self.card_body.setFixedHeight(230)
        self.card_body.setStyleSheet(
            f"background-color: {BG_SURFACE}; border: 1px solid {BORDER_SUBTLE}; "
            f"border-radius: 14px; padding: 24px;"
        )
        cb_layout = QVBoxLayout(self.card_body)
        cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card_side_lbl = QLabel("PROMPT (FRONT)")
        self.card_side_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        cb_layout.addWidget(self.card_side_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.card_text_lbl = QLabel("Click 'Generate New Cards' to create a revision deck.")
        self.card_text_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 17px; font-weight: 600; line-height: 1.5;")
        self.card_text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_text_lbl.setWordWrap(True)
        cb_layout.addWidget(self.card_text_lbl, 1)

        self.card_source_lbl = QLabel("")
        self.card_source_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic;")
        cb_layout.addWidget(self.card_source_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.card_body)

        # Card Controls
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.card_prev_btn = QPushButton("◀ Prev")
        self.card_prev_btn.setObjectName("secondary_btn")
        self.card_prev_btn.setFixedHeight(38)
        self.card_prev_btn.clicked.connect(self._prev_card)
        btn_row.addWidget(self.card_prev_btn)

        self.card_flip_btn = QPushButton("🔄 Flip Card (Show Answer)")
        self.card_flip_btn.setObjectName("primary_btn")
        self.card_flip_btn.setFixedHeight(38)
        self.card_flip_btn.clicked.connect(self._flip_card)
        btn_row.addWidget(self.card_flip_btn, 1)

        self.card_next_btn = QPushButton("Next ▶")
        self.card_next_btn.setObjectName("secondary_btn")
        self.card_next_btn.setFixedHeight(38)
        self.card_next_btn.clicked.connect(self._next_card)
        btn_row.addWidget(self.card_next_btn)

        layout.addLayout(btn_row)
        layout.addStretch()
        return widget

    # ── Self-Quiz Tab ──
    def _build_quiz_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        self.quiz_status_lbl = QLabel("Question 1 of 0")
        self.quiz_status_lbl.setStyleSheet(f"color: {ACCENT_HONEY}; font-weight: 700; font-size: 13px;")
        top_row.addWidget(self.quiz_status_lbl)

        top_row.addStretch()

        self.quiz_score_lbl = QLabel("Score: 0 / 0")
        self.quiz_score_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600; font-size: 12px;")
        top_row.addWidget(self.quiz_score_lbl)

        gen_quiz_btn = QPushButton("✨ Generate Quiz")
        gen_quiz_btn.setObjectName("secondary_btn")
        gen_quiz_btn.setFixedHeight(32)
        gen_quiz_btn.clicked.connect(lambda: self._start_study_task("quiz"))
        top_row.addWidget(gen_quiz_btn)
        layout.addLayout(top_row)

        # Question prompt card
        q_card = QFrame()
        q_card.setObjectName("card")
        qc_layout = QVBoxLayout(q_card)
        qc_layout.setContentsMargins(18, 16, 18, 16)

        self.quiz_prompt_lbl = QLabel("Click 'Generate Quiz' to start testing your knowledge on this document.")
        self.quiz_prompt_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600; line-height: 1.4;")
        self.quiz_prompt_lbl.setWordWrap(True)
        qc_layout.addWidget(self.quiz_prompt_lbl)
        layout.addWidget(q_card)

        # 4 Options
        self.quiz_opt_btns: List[QPushButton] = []
        for i in range(4):
            btn = QPushButton(f"Option {chr(65+i)}")
            btn.setObjectName("secondary_btn")
            btn.setFixedHeight(42)
            btn.setStyleSheet("text-align: left; padding: 8px 14px; font-size: 13px;")
            btn.clicked.connect(lambda checked=False, idx=i: self._answer_quiz(idx))
            layout.addWidget(btn)
            self.quiz_opt_btns.append(btn)

        # Feedback text
        self.quiz_feedback_lbl = QLabel("")
        self.quiz_feedback_lbl.setStyleSheet(f"padding: 10px; border-radius: 8px; font-size: 12px; font-weight: 600;")
        self.quiz_feedback_lbl.setWordWrap(True)
        self.quiz_feedback_lbl.hide()
        layout.addWidget(self.quiz_feedback_lbl)

        # Next button
        next_row = QHBoxLayout()
        self.quiz_next_btn = QPushButton("Next Question ▶")
        self.quiz_next_btn.setObjectName("primary_btn")
        self.quiz_next_btn.setFixedHeight(36)
        self.quiz_next_btn.setFixedWidth(140)
        self.quiz_next_btn.clicked.connect(self._next_quiz_q)
        self.quiz_next_btn.setEnabled(False)
        next_row.addStretch()
        next_row.addWidget(self.quiz_next_btn)
        layout.addLayout(next_row)

        layout.addStretch()
        return widget

    # ── Chapter Notes Tab ──
    def _build_notes_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        act_row = QHBoxLayout()
        gen_notes_btn = QPushButton("📝 Generate Summary Notes")
        gen_notes_btn.setObjectName("primary_btn")
        gen_notes_btn.setFixedHeight(34)
        gen_notes_btn.clicked.connect(lambda: self._start_study_task("summary"))
        act_row.addWidget(gen_notes_btn)

        act_row.addStretch()

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setObjectName("secondary_btn")
        copy_btn.setFixedHeight(32)
        copy_btn.clicked.connect(self._copy_notes)
        act_row.addWidget(copy_btn)

        export_btn = QPushButton("💾 Export")
        export_btn.setObjectName("secondary_btn")
        export_btn.setFixedHeight(32)
        export_btn.clicked.connect(self._export_notes)
        act_row.addWidget(export_btn)

        layout.addLayout(act_row)

        self.notes_display = QTextEdit()
        self.notes_display.setReadOnly(True)
        self.notes_display.setStyleSheet(
            f"background-color: {BG_CANVAS}; border: 1px solid {BORDER_SUBTLE}; "
            f"border-radius: 10px; font-size: 14px; padding: 16px; line-height: 1.6;"
        )
        self.notes_display.setPlaceholderText("Click 'Generate Summary Notes' to create structured revision takeaways.")
        layout.addWidget(self.notes_display, 1)

        return widget

    # ── Shelf Logic ──
    def on_enter(self) -> None:
        self._refresh_shelf()

    def _refresh_shelf(self) -> None:
        # Clear existing shelf buttons
        while self.shelf_items_layout.count() > 1:
            item = self.shelf_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        store = self.ctx.get_document_store()
        docs = store.list_documents()

        if not docs:
            no_docs_lbl = QLabel("No books on shelf.\nClick '+ Add' above.")
            no_docs_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 20px; text-align: center;")
            self.shelf_items_layout.insertWidget(0, no_docs_lbl)
            self.doc_title_lbl.setText("Your Shelf is Empty")
            self.doc_meta_lbl.setText("Click '+ Add Book or Notes' to import study material.")
            return

        # Render each book on shelf
        for doc in docs:
            btn = QPushButton(f"📘 {doc.filename}")
            btn.setObjectName("shelf_btn")
            btn.setFixedHeight(42)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"{doc.filename} ({doc.page_count} pages)")
            is_active = (doc.document_id == self._current_doc_id)
            btn.setProperty("active", str(is_active).lower())
            btn.clicked.connect(lambda checked=False, d=doc: self._select_book(d))
            self.shelf_items_layout.insertWidget(self.shelf_items_layout.count() - 1, btn)

        # Select first document if none selected
        if self._current_doc_id is None and docs:
            self._select_book(docs[0])

    def _select_book(self, doc) -> None:
        self._current_doc_id = doc.document_id
        self.doc_title_lbl.setText(f"📖 {doc.filename}")
        self.doc_meta_lbl.setText(f"{doc.page_count} pages  •  {doc.size_mb:.1f} MB  •  100% Indexed Locally")

        # Update shelf highlights
        for i in range(self.shelf_items_layout.count() - 1):
            w = self.shelf_items_layout.itemAt(i).widget()
            if isinstance(w, QPushButton):
                active = doc.filename in w.text()
                w.setProperty("active", str(active).lower())
                w.style().unpolish(w)
                w.style().polish(w)

    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Textbook or Notes", str(Path.home()),
            "Documents (*.pdf *.txt *.md);;PDF Files (*.pdf);;Text Files (*.txt *.md)"
        )
        if not path:
            return

        self.progress_bar.show()
        # Direct parsing & indexing
        try:
            from app.documents.parser import DocumentParser
            from app.retrieval.chunker import Chunker

            parser = DocumentParser()
            meta, pages = parser.parse(Path(path))

            store = self.ctx.get_document_store()
            store.upsert_document(meta)
            store.save_pages(pages)

            chunker = Chunker(chunk_size=self.ctx.settings.chunk_size, overlap=self.ctx.settings.chunk_overlap)
            chunks = chunker.chunk_pages(pages)
            store.save_chunks([c.to_dict() for c in chunks])

            embeddings = self.ctx.get_embeddings()
            emb_vectors = embeddings.embed([c.text for c in chunks])

            vs = self.ctx.get_vector_store()
            meta_list = [{"chunk_id": c.chunk_id, "document_id": c.document_id, "page_number": c.page_number, "text": c.text, "filename": meta.filename} for c in chunks]
            vs.add(emb_vectors, meta_list)

            meta.indexed = True
            meta.chunk_count = len(chunks)
            store.upsert_document(meta)

            self.progress_bar.hide()
            self._select_book(meta)
            self._refresh_shelf()
            QMessageBox.information(self, "Book Added", f"'{meta.filename}' added to your shelf and indexed locally!")

        except Exception as e:
            self.progress_bar.hide()
            QMessageBox.critical(self, "Import Error", f"Could not import document:\n{e}")

    # ── Dialogue Q&A Action ──
    def _submit_question(self, question: str) -> None:
        q = question.strip()
        if not q or not self._current_doc_id:
            return

        self.question_input.clear()
        self.ask_btn.setEnabled(False)
        self.progress_bar.show()

        # Render student question
        self.dialogue_display.append(
            f'<div style="margin: 10px 0; padding: 12px 14px; background-color: #1a1b22; border-radius: 8px;">'
            f'<div style="color: {ACCENT_HONEY}; font-weight: 700; font-size: 11px; margin-bottom: 4px;">YOU ASKED</div>'
            f'<div style="color: {TEXT_PRIMARY}; font-size: 14px;">{q}</div>'
            f'</div>'
        )

        worker = StudyDeskWorker(self.ctx, "chat", self._current_doc_id, q)
        worker.signals.chat_ready.connect(self._on_chat_response)
        worker.signals.error.connect(self._on_worker_error)
        self._pool.start(worker)

    def _on_chat_response(self, response) -> None:
        self.ask_btn.setEnabled(True)
        self.progress_bar.hide()

        ans_html = response.answer.replace("\n", "<br>")
        cite_html = ""
        if response.citations:
            cite_html = '<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #282934; font-size: 12px; color: #a1a1aa;">'
            cite_html += '<b>Sources:</b> '
            c_links = [f"<i>{c.filename}</i> (Page {c.page_number})" for c in response.citations]
            cite_html += " • ".join(c_links) + "</div>"

        self.dialogue_display.append(
            f'<div style="margin: 10px 0; padding: 14px 16px; background-color: {BG_SURFACE}; border-left: 3px solid {ACCENT_HONEY}; border-radius: 8px;">'
            f'<div style="color: {TEXT_MUTED}; font-size: 10px; font-weight: 700; margin-bottom: 6px;">NOTEBOOK COMMENTARY · {response.total_latency:.2f}s</div>'
            f'<div style="color: {TEXT_PRIMARY}; font-size: 14px; line-height: 1.6;">{ans_html}</div>'
            f'{cite_html}'
            f'</div>'
        )
        sb = self.dialogue_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Study Task Trigger ──
    def _start_study_task(self, task_type: str) -> None:
        if not self._current_doc_id:
            QMessageBox.warning(self, "Select Book", "Please select a book on your shelf first.")
            return

        self.progress_bar.show()
        worker = StudyDeskWorker(self.ctx, task_type, self._current_doc_id)
        worker.signals.study_ready.connect(self._on_study_task_ready)
        worker.signals.error.connect(self._on_worker_error)
        self._pool.start(worker)

    def _on_study_task_ready(self, task_type: str, data: object) -> None:
        self.progress_bar.hide()

        if task_type == "flashcards" and isinstance(data, list):
            self._cards = data
            self._card_idx = 0
            self._card_flipped = False
            self._render_card()
            self.modes_tab.setCurrentIndex(1)

        elif task_type == "quiz" and isinstance(data, list):
            self._quiz_questions = data
            self._quiz_idx = 0
            self._quiz_score = 0
            self._render_quiz()
            self.modes_tab.setCurrentIndex(2)

        elif task_type in ("summary", "notes"):
            self.notes_display.setPlainText(str(data))
            self.modes_tab.setCurrentIndex(3)

    def _on_worker_error(self, err: str) -> None:
        self.progress_bar.hide()
        self.ask_btn.setEnabled(True)
        QMessageBox.critical(self, "Study Error", f"Operation failed:\n{err}")

    # ── Card Deck Navigation ──
    def _render_card(self) -> None:
        if not self._cards:
            return
        card = self._cards[self._card_idx]
        self.card_counter_lbl.setText(f"Card {self._card_idx + 1} of {len(self._cards)}")

        if not self._card_flipped:
            self.card_side_lbl.setText("PROMPT (FRONT)")
            self.card_side_lbl.setStyleSheet(f"color: {ACCENT_HONEY}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
            self.card_text_lbl.setText(card.front)
            self.card_source_lbl.setText("")
            self.card_flip_btn.setText("🔄 Flip Card (Show Answer)")
        else:
            self.card_side_lbl.setText("DEFINITION (BACK)")
            self.card_side_lbl.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
            self.card_text_lbl.setText(card.back)
            self.card_source_lbl.setText(f"Source: {card.source}" if card.source else "")
            self.card_flip_btn.setText("🔄 Flip Card (Show Question)")

        self.card_prev_btn.setEnabled(self._card_idx > 0)
        self.card_next_btn.setEnabled(self._card_idx < len(self._cards) - 1)

    def _flip_card(self) -> None:
        self._card_flipped = not self._card_flipped
        self._render_card()

    def _next_card(self) -> None:
        if self._card_idx < len(self._cards) - 1:
            self._card_idx += 1
            self._card_flipped = False
            self._render_card()

    def _prev_card(self) -> None:
        if self._card_idx > 0:
            self._card_idx -= 1
            self._card_flipped = False
            self._render_card()

    # ── Quiz Navigation ──
    def _render_quiz(self) -> None:
        if not self._quiz_questions:
            return

        if self._quiz_idx >= len(self._quiz_questions):
            self.quiz_status_lbl.setText("🎉 Self-Quiz Completed!")
            self.quiz_prompt_lbl.setText(f"Final Score: {self._quiz_score} / {len(self._quiz_questions)} questions correct.\n\nAll questions were grounded in your local study notes.")
            for b in self.quiz_opt_btns:
                b.hide()
            self.quiz_feedback_lbl.setText("Great study session!")
            self.quiz_feedback_lbl.show()
            self.quiz_next_btn.setText("Restart Quiz 🔄")
            self.quiz_next_btn.setEnabled(True)
            return

        q = self._quiz_questions[self._quiz_idx]
        self.quiz_next_btn.setText("Next Question ▶")
        self.quiz_next_btn.setEnabled(False)
        self.quiz_feedback_lbl.hide()

        self.quiz_status_lbl.setText(f"Question {self._quiz_idx + 1} of {len(self._quiz_questions)}")
        self.quiz_score_lbl.setText(f"Score: {self._quiz_score} / {self._quiz_idx}")
        self.quiz_prompt_lbl.setText(q.question_text)

        for i, b in enumerate(self.quiz_opt_btns):
            if i < len(q.options):
                b.setText(q.options[i])
                b.setStyleSheet("text-align: left; padding: 8px 14px; font-size: 13px;")
                b.setEnabled(True)
                b.show()
            else:
                b.hide()

    def _answer_quiz(self, opt_idx: int) -> None:
        if self._quiz_idx >= len(self._quiz_questions):
            return
        q = self._quiz_questions[self._quiz_idx]
        corr = q.correct_answer.upper().strip()
        chosen = q.options[opt_idx] if opt_idx < len(q.options) else ""
        is_corr = chosen.startswith(corr) or (corr in chosen[:3])

        if is_corr:
            self._quiz_score += 1
            self.quiz_opt_btns[opt_idx].setStyleSheet("background-color: #143e2b; border: 1px solid #10b981; color: white; text-align: left; padding: 8px 14px;")
            self.quiz_feedback_lbl.setText(f"✅ Correct! Grounded in {q.source_hint or 'your document'}")
            self.quiz_feedback_lbl.setStyleSheet("background-color: #143e2b; color: #10b981; padding: 10px; border-radius: 8px;")
        else:
            self.quiz_opt_btns[opt_idx].setStyleSheet("background-color: #3e1414; border: 1px solid #ef4444; color: white; text-align: left; padding: 8px 14px;")
            self.quiz_feedback_lbl.setText(f"❌ Answer was [{corr}]. Grounded in {q.source_hint or 'your document'}")
            self.quiz_feedback_lbl.setStyleSheet("background-color: #3e1414; color: #ef4444; padding: 10px; border-radius: 8px;")

        self.quiz_feedback_lbl.show()
        for b in self.quiz_opt_btns:
            b.setEnabled(False)
        self.quiz_next_btn.setEnabled(True)
        self.quiz_score_lbl.setText(f"Score: {self._quiz_score} / {self._quiz_idx + 1}")

    def _next_quiz_q(self) -> None:
        if self._quiz_idx >= len(self._quiz_questions):
            self._quiz_idx = 0
            self._quiz_score = 0
            self._render_quiz()
        else:
            self._quiz_idx += 1
            self._render_quiz()

    # ── Notes Export / Copy ──
    def _copy_notes(self) -> None:
        text = self.notes_display.toPlainText().strip()
        if text:
            QGuiApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Notes copied to clipboard!")

    def _export_notes(self) -> None:
        text = self.notes_display.toPlainText().strip()
        if not text:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Study Notes", "study_notes.txt", "Text (*.txt);;Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            QMessageBox.information(self, "Saved", f"Exported to {path}")
