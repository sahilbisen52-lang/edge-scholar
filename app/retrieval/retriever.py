"""Semantic retriever: embed query → search index → return chunks."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.retrieval.embeddings import LocalEmbeddings
from app.retrieval.vector_store import VectorStore
from app.config.constants import DEFAULT_TOP_K

logger = logging.getLogger("edge_scholar.retrieval")


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    page_number: int
    text: str
    score: float
    filename: str = ""


class Retriever:
    def __init__(self, embeddings: LocalEmbeddings, vector_store: VectorStore) -> None:
        self.embeddings = embeddings
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        document_id: Optional[str] = None,
    ) -> tuple[list[RetrievedChunk], float]:
        """Return (chunks, retrieval_latency_seconds)."""
        t0 = time.perf_counter()
        q_emb = self.embeddings.embed_one(query)
        results = self.vector_store.search(q_emb, top_k=top_k * 2)  # Over-fetch for filtering
        elapsed = time.perf_counter() - t0

        chunks = []
        for score, meta in results:
            if document_id and meta.get("document_id") != document_id:
                continue
            chunks.append(RetrievedChunk(
                chunk_id=meta.get("chunk_id", ""),
                document_id=meta.get("document_id", ""),
                page_number=meta.get("page_number", 0),
                text=meta.get("text", ""),
                score=score,
                filename=meta.get("filename", ""),
            ))
            if len(chunks) >= top_k:
                break

        logger.debug("Retrieved %d chunks in %.3fs", len(chunks), elapsed)
        return chunks, elapsed
