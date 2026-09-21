"""Integration test: full RAG pipeline with mock provider."""
from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np

from app.ai.mock_provider import MockProvider
from app.documents.metadata import PageContent
from app.rag.citation_builder import build_citations, chunks_to_context
from app.rag.prompt_templates import rag_qa_prompt
from app.retrieval.retriever import RetrievedChunk


# ───────────────────────────────────────────────
# Mock Retriever for integration testing
# ───────────────────────────────────────────────

class MockRetriever:
    """Returns deterministic chunks for integration testing."""

    def retrieve(self, query: str, top_k: int = 5, document_id=None):
        chunks = [
            RetrievedChunk(
                chunk_id="c1",
                document_id="doc-os",
                page_number=12,
                text="A process is a program in execution. It has its own memory space and resources.",
                score=0.92,
                filename="operating_systems.pdf",
            ),
            RetrievedChunk(
                chunk_id="c2",
                document_id="doc-os",
                page_number=15,
                text="Process scheduling decides which process runs on the CPU and for how long.",
                score=0.85,
                filename="operating_systems.pdf",
            ),
        ]
        return chunks[:top_k], 0.05


class TestRAGPipeline:
    def test_prompt_construction(self):
        context = [
            {"text": "Processes are programs in execution.", "filename": "os.pdf", "page_number": 3},
        ]
        prompt = rag_qa_prompt("What is a process?", context)
        assert "What is a process?" in prompt
        assert "os.pdf" in prompt
        assert "Processes are programs in execution." in prompt
        assert "Do not invent" in prompt or "solely" in prompt or "RULES" in prompt

    def test_mock_provider_generate(self):
        provider = MockProvider()
        provider.load_model("mock")
        result = provider.generate("Explain the concept of a process.", max_tokens=100)
        assert result.text
        assert result.total_seconds > 0

    def test_mock_provider_health(self):
        provider = MockProvider()
        provider.load_model()
        assert provider.health_check()

    def test_mock_provider_runtime_info(self):
        provider = MockProvider()
        provider.load_model()
        info = provider.get_runtime_info()
        assert info.provider_name == "MockProvider"
        assert not info.accelerator_verified  # Mock never claims verified hardware

    def test_full_rag_flow(self):
        from app.rag.pipeline import RAGPipeline

        provider = MockProvider()
        provider.load_model()

        retriever = MockRetriever()

        pipeline = RAGPipeline(retriever=retriever, provider=provider)
        response = pipeline.query("What is a process?", top_k=2)

        assert response.question == "What is a process?"
        assert response.answer  # Should have some response
        assert len(response.citations) > 0
        assert response.total_latency > 0
        assert response.grounding_status in ("grounded", "partially_grounded", "insufficient_context")

    def test_citations_from_chunks(self):
        chunks = [
            RetrievedChunk("c1", "doc1", 5, "Some text", 0.9, "lecture.pdf"),
            RetrievedChunk("c2", "doc1", 8, "More text", 0.8, "lecture.pdf"),
        ]
        citations = build_citations(chunks)
        assert len(citations) == 2
        assert citations[0].filename == "lecture.pdf"
        assert citations[0].page_number == 5
        assert citations[1].page_number == 8

    def test_rag_response_badge(self):
        from app.rag.pipeline import RAGPipeline

        provider = MockProvider()
        provider.load_model()
        retriever = MockRetriever()
        pipeline = RAGPipeline(retriever=retriever, provider=provider)
        response = pipeline.query("Test question")
        # Badge should contain "LOCAL" since mock is local
        badge = response.runtime_badge
        assert "LOCAL" in badge
