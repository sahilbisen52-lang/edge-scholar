"""End-to-end integration test for document ingestion, retrieval, RAG, and study tools."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from app.core.app_context import AppContext
from app.documents.parser import DocumentParser
from app.documents.document_store import DocumentStore
from app.retrieval.chunker import Chunker
from app.retrieval.embeddings import LocalEmbeddings
from app.retrieval.vector_store import VectorStore
from app.retrieval.retriever import Retriever
from app.rag.pipeline import RAGPipeline
from app.ai.mock_provider import MockProvider
from app.study.summarizer import Summarizer
from app.study.quiz_generator import QuizGenerator
from app.study.flashcards import FlashcardGenerator
from app.study.notes_generator import NotesGenerator


def test_end_to_end_document_study_workflow(tmp_path: Path):
    # Setup isolated test directory
    db_path = tmp_path / "test_scholar.db"
    index_dir = tmp_path / "indexes"
    index_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse sample fixture
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    sample_file = fixtures_dir / "sample_operating_systems.txt"
    assert sample_file.exists(), f"Fixture file not found: {sample_file}"

    parser = DocumentParser()
    meta, pages = parser.parse(sample_file)
    assert meta.filename == "sample_operating_systems.txt"
    assert len(pages) > 0

    # 2. Store document
    store = DocumentStore(db_path)
    store.upsert_document(meta)
    store.save_pages(pages)

    # 3. Chunk
    chunker = Chunker(chunk_size=300, overlap=50)
    chunks = chunker.chunk_pages(pages)
    assert len(chunks) > 0
    store.save_chunks([c.to_dict() for c in chunks])

    # 4. Embed & Index into FAISS
    embeddings = LocalEmbeddings()
    texts = [c.text for c in chunks]
    emb_vectors = embeddings.embed(texts)
    assert emb_vectors.shape[0] == len(chunks)
    assert emb_vectors.shape[1] == 384

    vs = VectorStore(index_dir, dim=384)
    meta_list = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "page_number": c.page_number,
            "text": c.text,
            "filename": meta.filename,
        }
        for c in chunks
    ]
    vs.add(emb_vectors, meta_list)
    assert vs.count() == len(chunks)

    # Mark indexed in store
    meta.indexed = True
    meta.chunk_count = len(chunks)
    store.upsert_document(meta)

    # 5. Semantic Search & Retrieval
    retriever = Retriever(embeddings, vs)
    retrieved_chunks, elapsed = retriever.retrieve("What is CPU scheduling?", top_k=3)
    assert len(retrieved_chunks) > 0
    assert elapsed >= 0.0

    # Verify retrieved content relates to scheduling
    retrieved_text = " ".join(c.text for c in retrieved_chunks).lower()
    assert "scheduling" in retrieved_text or "process" in retrieved_text

    # 6. RAG Generation
    provider = MockProvider()
    provider.load_model("mock")

    pipeline = RAGPipeline(retriever=retriever, provider=provider)
    rag_response = pipeline.query("Explain CPU scheduling algorithms in operating systems.")
    assert rag_response.question
    assert rag_response.answer
    assert len(rag_response.citations) > 0
    assert rag_response.citations[0].filename == "sample_operating_systems.txt"
    assert rag_response.grounding_status in ("grounded", "partially_grounded")

    # 7. Study Tools Generation
    summarizer = Summarizer(provider, store)
    summary = summarizer.summarize_document(meta.document_id)
    assert len(summary) > 0

    quiz_gen = QuizGenerator(provider, store)
    quiz_raw, questions = quiz_gen.generate(meta.document_id)
    assert len(quiz_raw) > 0

    fc_gen = FlashcardGenerator(provider, store)
    fc_raw, cards = fc_gen.generate(meta.document_id)
    assert len(fc_raw) > 0

    notes_gen = NotesGenerator(provider, store)
    notes = notes_gen.generate(meta.document_id)
    assert len(notes) > 0

    # 8. Deletion flow test
    vs.delete_by_document(meta.document_id)
    store.delete_document(meta.document_id)
    assert store.get_document(meta.document_id) is None
    assert len(store.get_pages(meta.document_id)) == 0
    assert len(store.get_chunks(meta.document_id)) == 0
