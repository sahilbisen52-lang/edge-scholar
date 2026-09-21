"""Unit tests for document metadata and store."""
from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from app.documents.metadata import DocumentMetadata, PageContent
from app.documents.document_store import DocumentStore
from app.utils.timestamps import utc_now


def make_meta(doc_id: str = "test-001", filename: str = "test.pdf") -> DocumentMetadata:
    return DocumentMetadata(
        document_id=doc_id,
        filename=filename,
        file_path=f"/tmp/{filename}",
        file_type="pdf",
        file_size_bytes=1024,
        page_count=5,
        character_count=5000,
        title="Test Document",
        import_timestamp=utc_now(),
    )


class TestDocumentMetadata:
    def test_to_dict_roundtrip(self):
        meta = make_meta()
        d = meta.to_dict()
        restored = DocumentMetadata.from_dict(d)
        assert restored.document_id == meta.document_id
        assert restored.filename == meta.filename
        assert restored.page_count == meta.page_count

    def test_size_mb(self):
        meta = make_meta()
        meta.file_size_bytes = 1048576  # 1 MB
        assert abs(meta.size_mb - 1.0) < 0.001

    def test_page_content(self):
        page = PageContent(document_id="doc1", page_number=3, text="Hello world")
        assert page.character_count == len("Hello world")


class TestDocumentStore:
    def test_upsert_and_get(self, tmp_path):
        store = DocumentStore(tmp_path / "test.db")
        meta = make_meta("doc-123")
        store.upsert_document(meta)
        retrieved = store.get_document("doc-123")
        assert retrieved is not None
        assert retrieved.document_id == "doc-123"
        assert retrieved.filename == "test.pdf"

    def test_list_documents(self, tmp_path):
        store = DocumentStore(tmp_path / "test.db")
        for i in range(3):
            store.upsert_document(make_meta(f"doc-{i}", f"test{i}.pdf"))
        docs = store.list_documents()
        assert len(docs) == 3

    def test_delete_document(self, tmp_path):
        store = DocumentStore(tmp_path / "test.db")
        meta = make_meta("doc-del")
        store.upsert_document(meta)
        assert store.get_document("doc-del") is not None
        store.delete_document("doc-del")
        assert store.get_document("doc-del") is None

    def test_save_and_get_pages(self, tmp_path):
        store = DocumentStore(tmp_path / "test.db")
        meta = make_meta("doc-pages")
        store.upsert_document(meta)
        pages = [
            PageContent(document_id="doc-pages", page_number=1, text="Page 1 content"),
            PageContent(document_id="doc-pages", page_number=2, text="Page 2 content"),
        ]
        store.save_pages(pages)
        retrieved_pages = store.get_pages("doc-pages")
        assert len(retrieved_pages) == 2

    def test_save_and_get_chunks(self, tmp_path):
        store = DocumentStore(tmp_path / "test.db")
        meta = make_meta("doc-chunks")
        store.upsert_document(meta)
        chunks = [
            {"chunk_id": "c1", "document_id": "doc-chunks", "page_number": 1,
             "text": "Chunk 1", "token_estimate": 10, "hash": "abc"},
        ]
        store.save_chunks(chunks)
        retrieved = store.get_chunks("doc-chunks")
        assert len(retrieved) == 1
        assert retrieved[0]["chunk_id"] == "c1"

    def test_questions_answered_counter(self, tmp_path):
        store = DocumentStore(tmp_path / "test.db")
        assert store.get_total_questions_answered() == 0
        store.increment_questions_answered()
        store.increment_questions_answered()
        assert store.get_total_questions_answered() == 2
