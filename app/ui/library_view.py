"""
Library view — document import, listing, and management.
Full implementation with real document processing pipeline.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject, QRunnable, QThreadPool
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
    QSizePolicy,
)

from app.core.app_context import AppContext
from app.ui.styles.theme import (
    ACCENT, TEXT_SECONDARY, BG_SURFACE, BORDER, TEXT_PRIMARY,
    TEXT_MUTED, SUCCESS, WARNING, ERROR, BG_ELEVATED,
)

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = logging.getLogger("edge_scholar.ui.library")


# ───────────────────────────────────────────────
# Background Workers
# ───────────────────────────────────────────────

class ImportSignals(QObject):
    progress = Signal(str)  # status message
    finished = Signal(str)  # document_id
    error = Signal(str)


class ImportWorker(QRunnable):
    """Background document import and indexing."""

    def __init__(self, ctx: AppContext, filepath: str) -> None:
        super().__init__()
        self.ctx = ctx
        self.filepath = filepath
        self.signals = ImportSignals()

    def run(self) -> None:
        try:
            from app.documents.parser import DocumentParser
            from app.documents.document_store import DocumentStore
            from app.retrieval.chunker import Chunker
            from app.retrieval.embeddings import LocalEmbeddings
            from app.retrieval.vector_store import VectorStore
            from app.utils.file_validation import validate_document_file

            path = Path(self.filepath)

            # Validate
            self.signals.progress.emit(f"Validating {path.name}...")
            validate_document_file(path)

            # Parse
            self.signals.progress.emit(f"Parsing {path.name}...")
            parser = DocumentParser()
            meta, pages = parser.parse(path)

            # Store
            db = DocumentStore(self.ctx.db_path)

            # Check for existing document by sha256
            existing_docs = db.list_documents()
            for existing in existing_docs:
                if existing.sha256 == meta.sha256:
                    self.signals.error.emit(
                        f"Document already imported: {existing.filename}"
                    )
                    return

            db.upsert_document(meta)
            db.save_pages(pages)

            # Chunk
            self.signals.progress.emit("Chunking document...")
            chunker = Chunker(
                chunk_size=self.ctx.settings.chunk_size,
                overlap=self.ctx.settings.chunk_overlap,
            )
            chunks = chunker.chunk_pages(pages)
            db.save_chunks([c.to_dict() for c in chunks])

            # Embed
            self.signals.progress.emit("Generating embeddings (this may take a moment)...")
            embeddings_model = LocalEmbeddings(self.ctx.settings.selected_embedding_model)
            texts = [c.text for c in chunks]
            if texts:
                embeddings = embeddings_model.embed(texts)

                # Index
                self.signals.progress.emit("Building vector index...")
                vs = VectorStore(self.ctx.data_dir / "indexes")
                metadata_list = [
                    {
                        "chunk_id": c.chunk_id,
                        "document_id": c.document_id,
                        "page_number": c.page_number,
                        "text": c.text,
                        "filename": meta.filename,
                    }
                    for c in chunks
                ]
                vs.add(embeddings, metadata_list)

            # Mark indexed
            meta.indexed = True
            meta.chunk_count = len(chunks)
            db.upsert_document(meta)

            logger.info("Import complete: %s (%d chunks)", meta.filename, len(chunks))
            self.signals.finished.emit(meta.document_id)

        except Exception as e:
            logger.exception("Import failed: %s", e)
            self.signals.error.emit(str(e))


# ───────────────────────────────────────────────
# Document Card Widget
# ───────────────────────────────────────────────

class DocumentCard(QFrame):
    chat_requested = Signal(str)
    delete_requested = Signal(str)
    summarize_requested = Signal(str)

    def __init__(self, meta, parent=None) -> None:
        super().__init__(parent)
        self.meta = meta
        self.setObjectName("card")
        self.setFixedHeight(120)
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # File type icon
        type_icons = {"pdf": "📄", "txt": "📝", "md": "📋"}
        icon_text = type_icons.get(self.meta.file_type, "📁")
        icon = QLabel(icon_text)
        icon.setStyleSheet("font-size: 28px;")
        icon.setFixedWidth(40)
        layout.addWidget(icon)

        # Info column
        info = QVBoxLayout()
        info.setSpacing(4)

        name = QLabel(self.meta.filename)
        name.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 14px;")
        name.setMaximumWidth(350)
        info.addWidget(name)

        details = QLabel(
            f"{self.meta.file_type.upper()} • "
            f"{self.meta.page_count} pages • "
            f"{self.meta.size_mb:.1f} MB • "
            f"Imported {self.meta.import_timestamp.strftime('%b %d, %Y')}"
        )
        details.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        info.addWidget(details)

        status_text = "✅ Indexed" if self.meta.indexed else "⏳ Not indexed"
        status_color = SUCCESS if self.meta.indexed else WARNING
        status = QLabel(status_text)
        status.setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: 600;")
        info.addWidget(status)

        layout.addLayout(info)
        layout.addStretch()

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        chat_btn = QPushButton("💬 Chat")
        chat_btn.setObjectName("secondary_btn")
        chat_btn.setFixedWidth(80)
        chat_btn.clicked.connect(lambda: self.chat_requested.emit(self.meta.document_id))
        btn_layout.addWidget(chat_btn)

        sum_btn = QPushButton("📝 Summarize")
        sum_btn.setObjectName("secondary_btn")
        sum_btn.setFixedWidth(100)
        sum_btn.clicked.connect(lambda: self.summarize_requested.emit(self.meta.document_id))
        btn_layout.addWidget(sum_btn)

        del_btn = QPushButton("🗑")
        del_btn.setObjectName("secondary_btn")
        del_btn.setFixedWidth(36)
        del_btn.setToolTip("Delete document and all associated data")
        del_btn.setStyleSheet(f"color: {ERROR}; border-color: {ERROR};")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.meta.document_id))
        btn_layout.addWidget(del_btn)

        layout.addLayout(btn_layout)


# ───────────────────────────────────────────────
# Library View
# ───────────────────────────────────────────────

class LibraryView(QWidget):
    def __init__(self, ctx: AppContext, main_window: "MainWindow") -> None:
        super().__init__()
        self.ctx = ctx
        self.main_window = main_window
        self._pool = QThreadPool.globalInstance()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # ── Header ──
        header_row = QHBoxLayout()
        heading = QLabel("Document Library")
        heading.setObjectName("heading_label")
        header_row.addWidget(heading)
        header_row.addStretch()

        self._import_btn = QPushButton("📥 Import Document")
        self._import_btn.setObjectName("primary_btn")
        self._import_btn.setFixedHeight(40)
        self._import_btn.clicked.connect(self._import_document)
        header_row.addWidget(self._import_btn)
        layout.addLayout(header_row)

        sub = QLabel("Import PDF and TXT study materials. All data is indexed and stored locally.")
        sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(sub)

        # ── Progress area ──
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {ACCENT}; font-size: 13px;")
        self._status_label.hide()
        layout.addWidget(self._status_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(6)
        self._progress.hide()
        layout.addWidget(self._progress)

        # ── Document list ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._doc_container = QWidget()
        self._doc_layout = QVBoxLayout(self._doc_container)
        self._doc_layout.setContentsMargins(0, 0, 0, 0)
        self._doc_layout.setSpacing(12)
        self._doc_layout.addStretch()

        self._scroll.setWidget(self._doc_container)
        layout.addWidget(self._scroll)

        # ── Empty state ──
        self._empty_label = QLabel(
            "📚 Your study library is empty.\n\nClick 'Import Document' to add your first document."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 16px; padding: 60px;"
        )
        layout.addWidget(self._empty_label)

        self._refresh_docs()

    def on_enter(self) -> None:
        self._refresh_docs()

    def _refresh_docs(self) -> None:
        # Clear existing cards
        while self._doc_layout.count() > 1:
            item = self._doc_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            from app.documents.document_store import DocumentStore
            store = DocumentStore(self.ctx.db_path)
            docs = store.list_documents()
        except Exception as e:
            docs = []
            logger.warning("Could not load documents: %s", e)

        if not docs:
            self._empty_label.show()
        else:
            self._empty_label.hide()
            for meta in docs:
                card = DocumentCard(meta)
                card.chat_requested.connect(self._open_chat)
                card.delete_requested.connect(self._delete_document)
                card.summarize_requested.connect(self._open_summarize)
                self._doc_layout.insertWidget(self._doc_layout.count() - 1, card)

    def _import_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Study Document",
            str(Path.home()),
            "Documents (*.pdf *.txt *.md);;PDF Files (*.pdf);;Text Files (*.txt *.md)",
        )
        if not path:
            return

        self._import_btn.setEnabled(False)
        self._status_label.setText("Importing...")
        self._status_label.show()
        self._progress.show()

        worker = ImportWorker(self.ctx, path)
        worker.signals.progress.connect(self._on_import_progress)
        worker.signals.finished.connect(self._on_import_done)
        worker.signals.error.connect(self._on_import_error)
        self._pool.start(worker)

    def _on_import_progress(self, msg: str) -> None:
        self._status_label.setText(msg)

    def _on_import_done(self, doc_id: str) -> None:
        self._import_btn.setEnabled(True)
        self._progress.hide()
        self._status_label.setText(f"✅ Document indexed successfully!")
        self._refresh_docs()
        # Notify via event bus
        self.ctx.events.publish("document.imported", document_id=doc_id)

    def _on_import_error(self, error: str) -> None:
        self._import_btn.setEnabled(True)
        self._progress.hide()
        self._status_label.setText(f"❌ Import failed: {error}")
        QMessageBox.critical(self, "Import Failed", f"Could not import document:\n\n{error}")

    def _open_chat(self, doc_id: str) -> None:
        self.main_window.navigate_to("chat")

    def _open_summarize(self, doc_id: str) -> None:
        self.main_window.navigate_to("study")

    def _delete_document(self, doc_id: str) -> None:
        from app.documents.document_store import DocumentStore
        store = DocumentStore(self.ctx.db_path)
        meta = store.get_document(doc_id)
        if not meta:
            return

        reply = QMessageBox.question(
            self,
            "Delete Document",
            f"Delete '{meta.filename}' and all associated data?\n\n"
            "This will remove:\n• Document text\n• Chunks\n• Embeddings\n• Index records",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Delete from vector store
            from app.retrieval.vector_store import VectorStore
            vs = VectorStore(self.ctx.data_dir / "indexes")
            vs.delete_by_document(doc_id)

            # Delete from DB
            store.delete_document(doc_id)

            logger.info("Deleted document: %s", doc_id)
            self._refresh_docs()
            self.ctx.events.publish("document.deleted", document_id=doc_id)
        except Exception as e:
            QMessageBox.critical(self, "Delete Failed", f"Could not delete document:\n{e}")
