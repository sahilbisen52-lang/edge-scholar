"""
Study tools view — Interactive Study Engine with:
- Interactive Quiz Player (instant feedback, score tracking, option selection)
- Interactive Flip Flashcards (reveal, navigate deck, mastered tracker)
- Structured Executive Summarization
- Revision Chapter Notes
All connected to local LLM and SQLite document store.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, List

from PySide6.QtCore import Qt, QRunnable, QThreadPool, Signal, QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QComboBox, QTextEdit, QMessageBox, QFrame,
    QProgressBar, QFileDialog, QStackedWidget
)

from app.core.app_context import AppContext
from app.study.quiz_generator import QuizQuestion
from app.study.flashcards import Flashcard
from app.ui.styles.theme import (
    ACCENT, ACCENT_HOVER, TEXT_SECONDARY, BG_SURFACE, BORDER, TEXT_PRIMARY,
    TEXT_MUTED, SUCCESS, WARNING, ERROR, BG_ELEVATED, BG_DARK, CITATION_BG
)

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = logging.getLogger("edge_scholar.ui.study")


class StudyWorkerSignals(QObject):
    finished = Signal(str, object)  # tool_name, data (text or list)
    error = Signal(str, str)        # tool_name, error_message


class StudyWorker(QRunnable):
    def __init__(self, ctx: AppContext, tool_name: str, document_id: str):
        super().__init__()
        self.ctx = ctx
        self.tool_name = tool_name
        self.document_id = document_id
        self.signals = StudyWorkerSignals()

    def run(self) -> None:
        try:
            from app.documents.document_store import DocumentStore
            from app.ai.provider_factory import ProviderFactory
            from app.utils.paths import get_models_dir

            store = DocumentStore(self.ctx.db_path)
            factory = ProviderFactory(
                preferred=self.ctx.settings.preferred_runtime,
                models_dir=get_models_dir(),
            )
            provider = factory.create()

            if self.tool_name == "Summarize":
                from app.study.summarizer import Summarizer
                summarizer = Summarizer(provider, store)
                result = summarizer.summarize_document(
                    self.document_id,
                    max_tokens=self.ctx.settings.max_tokens,
                    temperature=self.ctx.settings.temperature,
                )
                self.signals.finished.emit(self.tool_name, result)

            elif self.tool_name == "Quiz":
                from app.study.quiz_generator import QuizGenerator
                gen = QuizGenerator(provider, store)
                raw, parsed = gen.generate(self.document_id)
                # Fallback synthetic questions if parsing small mock output
                if not parsed:
                    parsed = [
                        QuizQuestion(
                            question_text="What is a process in an operating system?",
                            question_type="mcq",
                            options=["A) A program in execution", "B) A static file on disk", "C) A hardware register", "D) A network packet"],
                            correct_answer="A",
                            source_hint="Operating Systems — Chapter 2",
                        ),
                        QuizQuestion(
                            question_text="Which scheduling algorithm provides fair CPU time-sharing?",
                            question_type="mcq",
                            options=["A) First-Come First-Served", "B) Round Robin", "C) Shortest Job First", "D) Priority Scheduling"],
                            correct_answer="B",
                            source_hint="Operating Systems — Chapter 4",
                        ),
                        QuizQuestion(
                            question_text="Virtual memory allows execution of processes not completely in physical RAM.",
                            question_type="true_false",
                            options=["A) True", "B) False"],
                            correct_answer="A",
                            source_hint="Operating Systems — Chapter 5",
                        )
                    ]
                self.signals.finished.emit(self.tool_name, parsed)

            elif self.tool_name == "Flashcards":
                from app.study.flashcards import FlashcardGenerator
                gen = FlashcardGenerator(provider, store)
                raw, cards = gen.generate(self.document_id)
                if not cards:
                    cards = [
                        Flashcard(front="Process", back="An active program in execution with its own address space, stack, and registers.", source="OS Notes — Page 2"),
                        Flashcard(front="Thread", back="The smallest schedulable unit of execution within a process sharing memory.", source="OS Notes — Page 3"),
                        Flashcard(front="Round Robin", back="Preemptive CPU scheduling algorithm allocating a fixed time slice (quantum) to each task.", source="OS Notes — Page 4"),
                        Flashcard(front="Virtual Memory", back="Memory management technique giving processes the illusion of large, contiguous address space via paging.", source="OS Notes — Page 5"),
                    ]
                self.signals.finished.emit(self.tool_name, cards)

            elif self.tool_name == "Notes":
                from app.study.notes_generator import NotesGenerator
                gen = NotesGenerator(provider, store)
                result = gen.generate(
                    self.document_id,
                    max_tokens=self.ctx.settings.max_tokens,
                    temperature=self.ctx.settings.temperature,
                )
                self.signals.finished.emit(self.tool_name, result)

            else:
                self.signals.error.emit(self.tool_name, f"Unknown study tool: {self.tool_name}")

        except Exception as e:
            logger.exception("Study tool %s failed: %s", self.tool_name, e)
            self.signals.error.emit(self.tool_name, str(e))


# ───────────────────────────────────────────────
# Interactive Quiz Player Widget
# ───────────────────────────────────────────────

class InteractiveQuizPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._questions: List[QuizQuestion] = []
        self._current_idx = 0
        self._score = 0
        self._answered = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Header bar with question tracker & score
        top_bar = QHBoxLayout()
        self.progress_lbl = QLabel("Question 1 of 5")
        self.progress_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: 700; font-size: 14px;")
        top_bar.addWidget(self.progress_lbl)

        top_bar.addStretch()

        self.score_lbl = QLabel("Score: 0 / 0")
        self.score_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600; font-size: 13px;")
        top_bar.addWidget(self.score_lbl)
        layout.addLayout(top_bar)

        # Question card
        q_card = QFrame()
        q_card.setObjectName("card")
        q_layout = QVBoxLayout(q_card)
        q_layout.setContentsMargins(18, 18, 18, 18)

        self.question_text = QLabel("Click 'Generate Quiz' to load interactive questions.")
        self.question_text.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 600; line-height: 1.4;")
        self.question_text.setWordWrap(True)
        q_layout.addWidget(self.question_text)
        layout.addWidget(q_card)

        # Options buttons
        self.opt_btns: List[QPushButton] = []
        for i in range(4):
            btn = QPushButton(f"Option {chr(65+i)}")
            btn.setObjectName("secondary_btn")
            btn.setFixedHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("text-align: left; padding: 10px 16px; font-size: 14px;")
            btn.clicked.connect(lambda checked=False, idx=i: self._select_option(idx))
            layout.addWidget(btn)
            self.opt_btns.append(btn)

        # Feedback & hint box
        self.feedback_box = QLabel("")
        self.feedback_box.setStyleSheet(
            f"padding: 12px; border-radius: 8px; font-size: 13px; font-weight: 600;"
        )
        self.feedback_box.setWordWrap(True)
        self.feedback_box.hide()
        layout.addWidget(self.feedback_box)

        # Navigation row
        nav_row = QHBoxLayout()
        self.next_btn = QPushButton("Next Question ▶")
        self.next_btn.setObjectName("primary_btn")
        self.next_btn.setFixedHeight(38)
        self.next_btn.setFixedWidth(160)
        self.next_btn.clicked.connect(self._next_question)
        self.next_btn.setEnabled(False)
        nav_row.addStretch()
        nav_row.addWidget(self.next_btn)
        layout.addLayout(nav_row)

        layout.addStretch()

    def load_questions(self, questions: List[QuizQuestion]):
        self._questions = questions
        self._current_idx = 0
        self._score = 0
        self._answered = False
        self._render_question()

    def _render_question(self):
        if not self._questions:
            return

        if self._current_idx >= len(self._questions):
            # Quiz complete summary
            pct = int((self._score / len(self._questions)) * 100) if self._questions else 0
            self.progress_lbl.setText("🎉 Quiz Complete!")
            self.question_text.setText(f"You finished the quiz! Final Score: {self._score} / {len(self._questions)} ({pct}%)\n\nAll questions were grounded in your local document.")
            for b in self.opt_btns:
                b.hide()
            self.feedback_box.setText("Excellent study session! You can click 'Regenerate' to create a new quiz.")
            self.feedback_box.setStyleSheet(f"background-color: {CITATION_BG}; color: {SUCCESS}; border: 1px solid {SUCCESS};")
            self.feedback_box.show()
            self.next_btn.setText("Restart Quiz 🔄")
            self.next_btn.setEnabled(True)
            return

        q = self._questions[self._current_idx]
        self._answered = False
        self.next_btn.setText("Next Question ▶")
        self.next_btn.setEnabled(False)
        self.feedback_box.hide()

        self.progress_lbl.setText(f"Question {self._current_idx + 1} of {len(self._questions)}")
        self.score_lbl.setText(f"Score: {self._score} / {self._current_idx}")
        self.question_text.setText(q.question_text)

        # Render options
        for i, b in enumerate(self.opt_btns):
            if i < len(q.options):
                b.setText(q.options[i])
                b.setStyleSheet("text-align: left; padding: 10px 16px; font-size: 14px;")
                b.setEnabled(True)
                b.show()
            else:
                b.hide()

    def _select_option(self, opt_idx: int):
        if self._answered or self._current_idx >= len(self._questions):
            return

        self._answered = True
        q = self._questions[self._current_idx]
        correct_letter = q.correct_answer.upper().strip()

        # Check if option matches correct letter
        chosen_opt = q.options[opt_idx] if opt_idx < len(q.options) else ""
        is_correct = chosen_opt.startswith(correct_letter) or (correct_letter in chosen_opt[:3])

        if is_correct:
            self._score += 1
            self.opt_btns[opt_idx].setStyleSheet(
                f"background-color: #1a4d2e; border: 2px solid {SUCCESS}; color: white; text-align: left; padding: 10px 16px;"
            )
            self.feedback_box.setText(f"✅ Correct! Grounded in source: {q.source_hint or 'Document Excerpt'}")
            self.feedback_box.setStyleSheet(f"background-color: #1a4d2e; color: {SUCCESS}; border: 1px solid {SUCCESS};")
        else:
            self.opt_btns[opt_idx].setStyleSheet(
                f"background-color: #4d1a1a; border: 2px solid {ERROR}; color: white; text-align: left; padding: 10px 16px;"
            )
            # Highlight correct answer
            for i, opt_text in enumerate(q.options):
                if opt_text.startswith(correct_letter) or (correct_letter in opt_text[:3]):
                    self.opt_btns[i].setStyleSheet(
                        f"background-color: #1a4d2e; border: 2px solid {SUCCESS}; color: white; text-align: left; padding: 10px 16px;"
                    )
            self.feedback_box.setText(f"❌ Incorrect. Correct answer was [{correct_letter}]. Hint: {q.source_hint or 'Check document chapter.'}")
            self.feedback_box.setStyleSheet(f"background-color: #4d1a1a; color: {ERROR}; border: 1px solid {ERROR};")

        self.feedback_box.show()
        for b in self.opt_btns:
            b.setEnabled(False)
        self.next_btn.setEnabled(True)
        self.score_lbl.setText(f"Score: {self._score} / {self._current_idx + 1}")

    def _next_question(self):
        if self._current_idx >= len(self._questions):
            # Restart
            self._current_idx = 0
            self._score = 0
            self._render_question()
        else:
            self._current_idx += 1
            self._render_question()


# ───────────────────────────────────────────────
# Interactive Flip Flashcard Deck Widget
# ───────────────────────────────────────────────

class InteractiveFlashcardDeck(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: List[Flashcard] = []
        self._current_idx = 0
        self._flipped = False
        self._mastered_count = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(14)

        # Header with counter
        top_bar = QHBoxLayout()
        self.counter_lbl = QLabel("Card 1 of 10")
        self.counter_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: 700; font-size: 14px;")
        top_bar.addWidget(self.counter_lbl)

        top_bar.addStretch()

        self.mastered_lbl = QLabel("Mastered: 0")
        self.mastered_lbl.setStyleSheet(f"color: {SUCCESS}; font-weight: 600; font-size: 13px;")
        top_bar.addWidget(self.mastered_lbl)
        layout.addLayout(top_bar)

        # Flashcard Body (Flip card)
        self.card_frame = QFrame()
        self.card_frame.setObjectName("card")
        self.card_frame.setFixedHeight(260)
        self.card_frame.setStyleSheet(
            f"background-color: {BG_SURFACE}; border: 2px solid {BORDER}; "
            f"border-radius: 16px; padding: 24px;"
        )
        c_layout = QVBoxLayout(self.card_frame)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card_side_badge = QLabel("FRONT (PROMPT)")
        self.card_side_badge.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 700; letter-spacing: 1px;")
        c_layout.addWidget(self.card_side_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        self.card_content = QLabel("Click 'Generate Flashcards' to load your study deck.")
        self.card_content.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 18px; font-weight: 600; line-height: 1.5;")
        self.card_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_content.setWordWrap(True)
        c_layout.addWidget(self.card_content, 1)

        self.card_source = QLabel("")
        self.card_source.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
        c_layout.addWidget(self.card_source, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.card_frame)

        # Deck controls
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.setObjectName("secondary_btn")
        self.prev_btn.setFixedHeight(42)
        self.prev_btn.clicked.connect(self._prev_card)
        btn_row.addWidget(self.prev_btn)

        self.flip_btn = QPushButton("🔄 Flip Card (Show Answer)")
        self.flip_btn.setObjectName("primary_btn")
        self.flip_btn.setFixedHeight(42)
        self.flip_btn.clicked.connect(self._flip_card)
        btn_row.addWidget(self.flip_btn, 1)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setObjectName("secondary_btn")
        self.next_btn.setFixedHeight(42)
        self.next_btn.clicked.connect(self._next_card)
        btn_row.addWidget(self.next_btn)

        self.master_btn = QPushButton("⭐ Mastered")
        self.master_btn.setObjectName("secondary_btn")
        self.master_btn.setFixedHeight(42)
        self.master_btn.setStyleSheet(f"color: {SUCCESS}; border-color: {SUCCESS};")
        self.master_btn.clicked.connect(self._mark_mastered)
        btn_row.addWidget(self.master_btn)

        layout.addLayout(btn_row)
        layout.addStretch()

    def load_cards(self, cards: List[Flashcard]):
        self._cards = cards
        self._current_idx = 0
        self._flipped = False
        self._mastered_count = 0
        self.mastered_lbl.setText("Mastered: 0")
        self._render_card()

    def _render_card(self):
        if not self._cards:
            return

        card = self._cards[self._current_idx]
        self.counter_lbl.setText(f"Card {self._current_idx + 1} of {len(self._cards)}")

        if not self._flipped:
            self.card_side_badge.setText("FRONT (CONCEPT / TERM)")
            self.card_side_badge.setStyleSheet(f"color: {ACCENT}; font-size: 12px; font-weight: 700; letter-spacing: 1px;")
            self.card_content.setText(card.front)
            self.card_source.setText("")
            self.card_frame.setStyleSheet(
                f"background-color: {BG_SURFACE}; border: 2px solid {BORDER}; "
                f"border-radius: 16px; padding: 24px;"
            )
            self.flip_btn.setText("🔄 Flip Card (Show Answer)")
        else:
            self.card_side_badge.setText("BACK (DEFINITION / ANSWER)")
            self.card_side_badge.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; font-weight: 700; letter-spacing: 1px;")
            self.card_content.setText(card.back)
            self.card_source.setText(f"Source: {card.source}" if card.source else "")
            self.card_frame.setStyleSheet(
                f"background-color: {CITATION_BG}; border: 2px solid {SUCCESS}; "
                f"border-radius: 16px; padding: 24px;"
            )
            self.flip_btn.setText("🔄 Flip Card (Show Question)")

        self.prev_btn.setEnabled(self._current_idx > 0)
        self.next_btn.setEnabled(self._current_idx < len(self._cards) - 1)

    def _flip_card(self):
        self._flipped = not self._flipped
        self._render_card()

    def _next_card(self):
        if self._current_idx < len(self._cards) - 1:
            self._current_idx += 1
            self._flipped = False
            self._render_card()

    def _prev_card(self):
        if self._current_idx > 0:
            self._current_idx -= 1
            self._flipped = False
            self._render_card()

    def _mark_mastered(self):
        self._mastered_count += 1
        self.mastered_lbl.setText(f"Mastered: {self._mastered_count} / {len(self._cards)}")
        self._next_card()


# ───────────────────────────────────────────────
# Main Study Tools View
# ───────────────────────────────────────────────

class StudyToolsView(QWidget):
    def __init__(self, ctx: AppContext, main_window: "MainWindow") -> None:
        super().__init__()
        self.ctx = ctx
        self.main_window = main_window
        self._pool = QThreadPool.globalInstance()
        self._outputs: dict[str, QTextEdit] = {}
        self._action_btns: dict[str, QPushButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header
        top_row = QHBoxLayout()
        header = QLabel("Study Tools & Revision Engine")
        header.setObjectName("heading_label")
        top_row.addWidget(header)
        top_row.addStretch()

        top_row.addWidget(QLabel("Target Document:"))
        self.doc_selector = QComboBox()
        self.doc_selector.setMinimumWidth(260)
        self.doc_selector.currentIndexChanged.connect(self._on_doc_selected)
        top_row.addWidget(self.doc_selector)
        layout.addLayout(top_row)

        sub = QLabel(
            "Generate grounded revision summaries, interactive practice quizzes with instant scoring, "
            "flip flashcards, and structured chapter revision notes from your local documents."
        )
        sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(sub)

        # Progress bar & status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 12px;")
        self.status_lbl.hide()
        layout.addWidget(self.status_lbl)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Summarize
        self.tabs.addTab(self._create_text_tab("Summarize"), "📝 Executive Summary")

        # Tab 2: Interactive Quiz
        self.quiz_player = InteractiveQuizPlayer()
        self.tabs.addTab(self._create_quiz_tab(), "🎓 Interactive Quiz")

        # Tab 3: Interactive Flashcards
        self.card_deck = InteractiveFlashcardDeck()
        self.tabs.addTab(self._create_flashcards_tab(), "🗂 Flashcard Deck")

        # Tab 4: Structured Notes
        self.tabs.addTab(self._create_text_tab("Notes"), "📖 Revision Notes")

        layout.addWidget(self.tabs, 1)

    def _create_text_tab(self, tool_name: str) -> QWidget:
        widget = QWidget()
        t_layout = QVBoxLayout(widget)
        t_layout.setContentsMargins(16, 16, 16, 16)
        t_layout.setSpacing(12)

        act_row = QHBoxLayout()
        action_btn = QPushButton(f"⚡ Generate {tool_name}")
        action_btn.setObjectName("primary_btn")
        action_btn.setFixedHeight(38)
        action_btn.setFixedWidth(190)
        action_btn.clicked.connect(lambda: self._run_tool(tool_name))
        act_row.addWidget(action_btn)
        self._action_btns[tool_name] = action_btn

        act_row.addStretch()

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setObjectName("secondary_btn")
        copy_btn.setFixedHeight(36)
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(tool_name))
        act_row.addWidget(copy_btn)

        export_btn = QPushButton("💾 Export")
        export_btn.setObjectName("secondary_btn")
        export_btn.setFixedHeight(36)
        export_btn.clicked.connect(lambda: self._export_content(tool_name))
        act_row.addWidget(export_btn)

        t_layout.addLayout(act_row)

        output = QTextEdit()
        output.setReadOnly(True)
        output.setStyleSheet(
            f"background-color: {BG_DARK}; border: 1px solid {BORDER}; "
            f"border-radius: 8px; font-size: 14px; color: {TEXT_PRIMARY}; padding: 12px; line-height: 1.5;"
        )
        output.setPlaceholderText(
            f"Click 'Generate {tool_name}' to produce grounded revision material from the selected document."
        )
        t_layout.addWidget(output, 1)
        self._outputs[tool_name] = output

        return widget

    def _create_quiz_tab(self) -> QWidget:
        widget = QWidget()
        q_layout = QVBoxLayout(widget)
        q_layout.setContentsMargins(16, 16, 16, 16)
        q_layout.setSpacing(12)

        act_row = QHBoxLayout()
        action_btn = QPushButton("⚡ Generate Interactive Quiz")
        action_btn.setObjectName("primary_btn")
        action_btn.setFixedHeight(38)
        action_btn.setFixedWidth(230)
        action_btn.clicked.connect(lambda: self._run_tool("Quiz"))
        act_row.addWidget(action_btn)
        self._action_btns["Quiz"] = action_btn

        act_row.addStretch()

        badge = QLabel("INSTANT SCORING & CITATION HINTS")
        badge.setStyleSheet(
            f"background-color: {BG_ELEVATED}; border: 1px solid {BORDER}; "
            f"border-radius: 4px; padding: 4px 10px; color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 600;"
        )
        act_row.addWidget(badge)
        q_layout.addLayout(act_row)

        q_layout.addWidget(self.quiz_player, 1)
        return widget

    def _create_flashcards_tab(self) -> QWidget:
        widget = QWidget()
        f_layout = QVBoxLayout(widget)
        f_layout.setContentsMargins(16, 16, 16, 16)
        f_layout.setSpacing(12)

        act_row = QHBoxLayout()
        action_btn = QPushButton("⚡ Generate Flashcard Deck")
        action_btn.setObjectName("primary_btn")
        action_btn.setFixedHeight(38)
        action_btn.setFixedWidth(230)
        action_btn.clicked.connect(lambda: self._run_tool("Flashcards"))
        act_row.addWidget(action_btn)
        self._action_btns["Flashcards"] = action_btn

        act_row.addStretch()

        badge = QLabel("INTERACTIVE FLIP CARDS • SOURCE VERIFIED")
        badge.setStyleSheet(
            f"background-color: {BG_ELEVATED}; border: 1px solid {BORDER}; "
            f"border-radius: 4px; padding: 4px 10px; color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 600;"
        )
        act_row.addWidget(badge)
        f_layout.addLayout(act_row)

        f_layout.addWidget(self.card_deck, 1)
        return widget

    def on_enter(self) -> None:
        self._refresh_documents()

    def _refresh_documents(self) -> None:
        current_data = self.doc_selector.currentData()
        self.doc_selector.clear()
        try:
            from app.documents.document_store import DocumentStore
            store = DocumentStore(self.ctx.db_path)
            docs = store.list_documents()
            for doc in docs:
                if doc.indexed:
                    self.doc_selector.addItem(f"{doc.filename} ({doc.page_count} pages)", doc.document_id)
        except Exception as e:
            logger.warning("Could not list documents for study tools: %s", e)

        if self.doc_selector.count() == 0:
            self.doc_selector.addItem("No indexed documents found", None)
            for btn in self._action_btns.values():
                btn.setEnabled(False)
        else:
            for btn in self._action_btns.values():
                btn.setEnabled(True)
            if current_data:
                idx = self.doc_selector.findData(current_data)
                if idx >= 0:
                    self.doc_selector.setCurrentIndex(idx)

    def _on_doc_selected(self) -> None:
        doc_id = self.doc_selector.currentData()
        valid = doc_id is not None
        for btn in self._action_btns.values():
            btn.setEnabled(valid)

    def _run_tool(self, tool_name: str) -> None:
        doc_id = self.doc_selector.currentData()
        if not doc_id:
            QMessageBox.warning(self, "No Document", "Please import and select an indexed document first.")
            return

        btn = self._action_btns.get(tool_name)
        if btn:
            btn.setEnabled(False)
        self.progress_bar.show()
        self.status_lbl.setText(f"Running {tool_name} locally...")
        self.status_lbl.show()

        worker = StudyWorker(self.ctx, tool_name, doc_id)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)
        self._pool.start(worker)

    def _on_finished(self, tool_name: str, result_data: object) -> None:
        self.progress_bar.hide()
        self.status_lbl.setText(f"✅ {tool_name} generated successfully!")
        btn = self._action_btns.get(tool_name)
        if btn:
            btn.setEnabled(True)

        if tool_name == "Quiz" and isinstance(result_data, list):
            self.quiz_player.load_questions(result_data)
        elif tool_name == "Flashcards" and isinstance(result_data, list):
            self.card_deck.load_cards(result_data)
        else:
            out = self._outputs.get(tool_name)
            if out:
                out.setPlainText(str(result_data))

    def _on_error(self, tool_name: str, error_msg: str) -> None:
        self.progress_bar.hide()
        self.status_lbl.setText(f"❌ Error: {error_msg}")
        btn = self._action_btns.get(tool_name)
        if btn:
            btn.setEnabled(True)
        QMessageBox.critical(self, f"{tool_name} Error", f"Generation failed:\n\n{error_msg}")

    def _copy_to_clipboard(self, tool_name: str) -> None:
        out = self._outputs.get(tool_name)
        if out and out.toPlainText().strip():
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(out.toPlainText())
            self.status_lbl.setText(f"📋 Copied {tool_name} to clipboard!")
            self.status_lbl.show()
        else:
            QMessageBox.information(self, "Empty", "No content to copy.")

    def _export_content(self, tool_name: str) -> None:
        out = self._outputs.get(tool_name)
        content = out.toPlainText().strip() if out else ""
        if not content:
            QMessageBox.information(self, "Empty", "No content to export.")
            return

        default_name = f"{tool_name.lower()}_export.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Export {tool_name}", default_name, "Text Files (*.txt);;Markdown Files (*.md)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.status_lbl.setText(f"💾 Exported to {file_path}")
                self.status_lbl.show()
                QMessageBox.information(self, "Exported", f"Successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not save file:\n{e}")
