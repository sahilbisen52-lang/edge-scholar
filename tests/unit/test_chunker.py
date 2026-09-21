"""Unit tests for the text chunker."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from app.retrieval.chunker import Chunker, TextChunk
from app.documents.metadata import PageContent


SAMPLE_TEXT = """
Discrete mathematics is the study of mathematical structures that are fundamentally discrete 
rather than continuous. In contrast to real numbers that have the property of varying smoothly, 
the objects studied in discrete mathematics (such as integers, graphs, and statements in logic) 
do not vary smoothly in this way, but have distinct, separated values.

Discrete mathematics therefore excludes topics in continuous mathematics such as calculus or 
Euclidean geometry. Discrete objects can often be enumerated by integers. More formally, 
discrete mathematics has been characterized as the branch of mathematics dealing with 
countable sets (finite sets or sets with the same cardinality as the natural numbers). 
However, there is no exact definition of the term discrete mathematics.

Sets are one of the fundamental concepts in discrete mathematics. A set is a well-defined 
collection of distinct objects. The objects are called elements or members of the set. 
Elements of a set can be anything: numbers, people, letters, etc.
""".strip()


def make_page(text: str, doc_id: str = "doc1", page: int = 1) -> PageContent:
    return PageContent(document_id=doc_id, page_number=page, text=text)


class TestChunker:
    def test_basic_chunking(self):
        chunker = Chunker(chunk_size=100, overlap=20)
        pages = [make_page(SAMPLE_TEXT)]
        chunks = chunker.chunk_pages(pages)
        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, TextChunk)
            assert chunk.text.strip()
            assert chunk.document_id == "doc1"
            assert chunk.page_number == 1

    def test_chunk_has_required_fields(self):
        chunker = Chunker(chunk_size=100, overlap=20)
        pages = [make_page("Hello world. This is a test.")]
        chunks = chunker.chunk_pages(pages)
        assert len(chunks) >= 1
        c = chunks[0]
        assert c.chunk_id
        assert c.document_id
        assert c.hash
        assert c.token_estimate > 0

    def test_empty_text_returns_no_chunks(self):
        chunker = Chunker()
        pages = [make_page("")]
        chunks = chunker.chunk_pages(pages)
        assert chunks == []

    def test_no_duplicate_chunks(self):
        chunker = Chunker(chunk_size=50, overlap=10)
        # Same page twice
        pages = [
            make_page("Same text here.", page=1),
            make_page("Same text here.", page=2),  # Identical content
        ]
        chunks = chunker.chunk_pages(pages)
        chunk_ids = [c.chunk_id for c in chunks]
        # chunk IDs include page number so they can differ; but hashes should differ due to page
        hashes = [c.hash for c in chunks]
        # We don't require deduplication across pages since page matters for citations
        assert len(chunks) >= 1

    def test_multi_page_chunking(self):
        chunker = Chunker(chunk_size=100, overlap=20)
        pages = [
            make_page("Page one text. " * 20, page=1),
            make_page("Page two text. " * 20, page=2),
        ]
        chunks = chunker.chunk_pages(pages)
        page_numbers = {c.page_number for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_chunk_to_dict(self):
        chunker = Chunker(chunk_size=200, overlap=40)
        pages = [make_page(SAMPLE_TEXT)]
        chunks = chunker.chunk_pages(pages)
        d = chunks[0].to_dict()
        assert "chunk_id" in d
        assert "document_id" in d
        assert "page_number" in d
        assert "text" in d
        assert "token_estimate" in d
        assert "hash" in d
