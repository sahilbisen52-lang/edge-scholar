"""
Full RAG pipeline: query → retrieve → prompt → generate → cite.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Generator

from app.ai.base_provider import AIProvider, GenerationResult
from app.rag.citation_builder import Citation, build_citations, chunks_to_context, format_citations_text
from app.rag.prompt_templates import rag_qa_prompt
from app.retrieval.retriever import Retriever, RetrievedChunk
from app.core.errors import ModelNotLoadedError

logger = logging.getLogger("edge_scholar.rag")


@dataclass
class RAGResponse:
    question: str
    answer: str
    citations: list[Citation]
    chunks_used: list[RetrievedChunk]
    retrieval_latency: float
    generation_result: Optional[GenerationResult]
    grounding_status: str  # "grounded" | "partially_grounded" | "insufficient_context"
    total_latency: float

    def formatted_answer(self) -> str:
        """Full answer with citations appended."""
        return self.answer + format_citations_text(self.citations)

    @property
    def runtime_badge(self) -> str:
        if self.generation_result and self.generation_result.runtime_info:
            return self.generation_result.runtime_info.badge()
        return "LOCAL"


class RAGPipeline:
    """
    Full Retrieval-Augmented Generation pipeline.
    
    Flow: query → embed → FAISS search → top-K chunks → build prompt → LLM → citations
    """

    def __init__(self, retriever: Retriever, provider: AIProvider) -> None:
        self.retriever = retriever
        self.provider = provider

    def query(
        self,
        question: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.15,
    ) -> RAGResponse:
        t_start = time.perf_counter()

        # 1. Retrieve relevant chunks
        chunks, retrieval_latency = self.retriever.retrieve(
            question, top_k=top_k, document_id=document_id
        )

        # 2. Assess grounding
        grounding_status = self._assess_grounding(chunks)

        # 3. Build prompt
        context = chunks_to_context(chunks)
        prompt = rag_qa_prompt(question, context)

        # 4. Generate
        try:
            gen_result = self.provider.generate(prompt, max_tokens=max_tokens, temperature=temperature)
            answer = gen_result.text
        except ModelNotLoadedError:
            answer = "⚠️ No AI model is loaded. Please install and load a model via the Model Manager."
            gen_result = None
        except Exception as e:
            logger.exception("Generation error: %s", e)
            answer = f"⚠️ Generation failed: {e}"
            gen_result = None

        # 5. Build citations
        citations = build_citations(chunks)
        total_latency = time.perf_counter() - t_start

        logger.info(
            "RAG query complete: %d chunks, %.2fs total (%.2fs retrieval)",
            len(chunks), total_latency, retrieval_latency,
        )

        return RAGResponse(
            question=question,
            answer=answer,
            citations=citations,
            chunks_used=chunks,
            retrieval_latency=retrieval_latency,
            generation_result=gen_result,
            grounding_status=grounding_status,
            total_latency=total_latency,
        )

    def stream_query(
        self,
        question: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.15,
    ) -> Generator[str, None, RAGResponse]:
        """Streaming version — yields text tokens, returns RAGResponse."""
        t_start = time.perf_counter()

        chunks, retrieval_latency = self.retriever.retrieve(
            question, top_k=top_k, document_id=document_id
        )
        grounding_status = self._assess_grounding(chunks)
        context = chunks_to_context(chunks)
        prompt = rag_qa_prompt(question, context)

        full_text = ""
        gen_result = None
        try:
            gen = self.provider.stream_generate(prompt, max_tokens=max_tokens, temperature=temperature)
            while True:
                try:
                    token = next(gen)
                    full_text += token
                    yield token
                except StopIteration as exc:
                    gen_result = exc.value
                    break
        except ModelNotLoadedError:
            msg = "⚠️ No AI model is loaded."
            full_text = msg
            yield msg
        except Exception as e:
            msg = f"⚠️ Generation failed: {e}"
            full_text = msg
            yield msg

        citations = build_citations(chunks)
        total_latency = time.perf_counter() - t_start

        return RAGResponse(
            question=question,
            answer=full_text,
            citations=citations,
            chunks_used=chunks,
            retrieval_latency=retrieval_latency,
            generation_result=gen_result,
            grounding_status=grounding_status,
            total_latency=total_latency,
        )

    @staticmethod
    def _assess_grounding(chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "insufficient_context"
        avg_score = sum(c.score for c in chunks) / len(chunks)
        if avg_score > 0.7:
            return "grounded"
        elif avg_score > 0.4:
            return "partially_grounded"
        return "insufficient_context"
