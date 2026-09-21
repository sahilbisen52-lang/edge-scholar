"""Unit tests for the citation builder."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from app.rag.citation_builder import build_citations, format_citations_text, chunks_to_context, Citation
from app.retrieval.retriever import RetrievedChunk


def make_chunk(filename: str, page: int, score: float = 0.9, text: str = "Sample text.") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"chunk_{filename}_{page}",
        document_id=f"doc_{filename}",
        page_number=page,
        text=text,
        score=score,
        filename=filename,
    )


class TestCitationBuilder:
    def test_build_citations_basic(self):
        chunks = [
            make_chunk("os.pdf", 10),
            make_chunk("os.pdf", 15),
        ]
        citations = build_citations(chunks)
        assert len(citations) == 2
        assert citations[0].index == 1
        assert citations[1].index == 2
        assert citations[0].filename == "os.pdf"
        assert citations[0].page_number == 10

    def test_build_citations_deduplicates_same_page(self):
        chunks = [
            make_chunk("math.pdf", 5, score=0.9),
            make_chunk("math.pdf", 5, score=0.8),  # Duplicate page
        ]
        citations = build_citations(chunks)
        assert len(citations) == 1

    def test_build_citations_empty(self):
        assert build_citations([]) == []

    def test_citation_display(self):
        c = Citation(index=1, filename="notes.pdf", page_number=23, document_id="doc1")
        assert "notes.pdf" in c.display()
        assert "23" in c.display()
        assert "[1]" in c.display()

    def test_format_citations_text(self):
        chunks = [make_chunk("test.pdf", 1), make_chunk("test.pdf", 2)]
        citations = build_citations(chunks)
        text = format_citations_text(citations)
        assert "Sources:" in text
        assert "test.pdf" in text
        assert "Page 1" in text
        assert "Page 2" in text

    def test_format_citations_empty(self):
        assert format_citations_text([]) == ""

    def test_chunks_to_context(self):
        chunks = [make_chunk("doc.pdf", 7, text="Important concept here.")]
        ctx = chunks_to_context(chunks)
        assert len(ctx) == 1
        assert ctx[0]["text"] == "Important concept here."
        assert ctx[0]["filename"] == "doc.pdf"
        assert ctx[0]["page_number"] == 7

    def test_citation_to_dict(self):
        c = Citation(index=2, filename="book.pdf", page_number=42, document_id="abc", score=0.85)
        d = c.to_dict()
        assert d["index"] == 2
        assert d["filename"] == "book.pdf"
        assert d["page_number"] == 42
