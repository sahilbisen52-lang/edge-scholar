"""
Citation builder — formats retrieved chunks into user-visible citations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.retrieval.retriever import RetrievedChunk


@dataclass
class Citation:
    index: int
    filename: str
    page_number: int
    document_id: str
    excerpt: str = ""
    score: float = 0.0

    def display(self) -> str:
        return f"[{self.index}] {self.filename} — Page {self.page_number}"

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "filename": self.filename,
            "page_number": self.page_number,
            "document_id": self.document_id,
            "excerpt": self.excerpt[:200],
            "score": round(self.score, 4),
        }


def build_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    citations = []
    seen: set[tuple[str, int]] = set()
    idx = 1
    for chunk in chunks:
        key = (chunk.filename or chunk.document_id, chunk.page_number)
        if key not in seen:
            seen.add(key)
            citations.append(Citation(
                index=idx,
                filename=chunk.filename or chunk.document_id,
                page_number=chunk.page_number,
                document_id=chunk.document_id,
                excerpt=chunk.text[:200],
                score=chunk.score,
            ))
            idx += 1
    return citations


def format_citations_text(citations: list[Citation]) -> str:
    if not citations:
        return ""
    lines = ["\n\nSources:"]
    for c in citations:
        lines.append(f"  {c.display()}")
    return "\n".join(lines)


def chunks_to_context(chunks: list[RetrievedChunk]) -> list[dict]:
    """Convert chunks to context dicts for prompt templates."""
    return [
        {
            "text": chunk.text,
            "filename": chunk.filename or chunk.document_id,
            "page_number": chunk.page_number,
            "score": chunk.score,
        }
        for chunk in chunks
    ]
