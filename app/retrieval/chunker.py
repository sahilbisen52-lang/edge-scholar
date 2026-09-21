"""Page-aware text chunker."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.config.constants import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from app.documents.metadata import PageContent
from app.utils.hashing import short_hash

logger = logging.getLogger("edge_scholar.retrieval")

APPROX_CHARS_PER_TOKEN = 4


@dataclass
class TextChunk:
    chunk_id: str
    document_id: str
    page_number: int
    text: str
    token_estimate: int
    hash: str

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "text": self.text,
            "token_estimate": self.token_estimate,
            "hash": self.hash,
        }


class Chunker:
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_pages(self, pages: list[PageContent]) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        seen_hashes: set[str] = set()

        for page in pages:
            page_chunks = self._chunk_text(page.text, page.document_id, page.page_number)
            for chunk in page_chunks:
                if chunk.hash not in seen_hashes:
                    seen_hashes.add(chunk.hash)
                    chunks.append(chunk)

        logger.debug(
            "Chunked %d pages into %d unique chunks", len(pages), len(chunks)
        )
        return chunks

    def _chunk_text(self, text: str, document_id: str, page_number: int) -> list[TextChunk]:
        if not text.strip():
            return []

        char_size = self.chunk_size * APPROX_CHARS_PER_TOKEN
        char_overlap = self.overlap * APPROX_CHARS_PER_TOKEN

        chunks = []
        start = 0
        while start < len(text):
            end = start + char_size
            chunk_text = text[start:end]
            if not chunk_text.strip():
                break

            h = short_hash(f"{document_id}:{page_number}:{chunk_text}")
            chunk_id = f"{document_id}_p{page_number}_{h}"
            token_est = max(1, len(chunk_text) // APPROX_CHARS_PER_TOKEN)

            chunks.append(TextChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                page_number=page_number,
                text=chunk_text,
                token_estimate=token_est,
                hash=h,
            ))

            start += char_size - char_overlap
            if start >= len(text):
                break

        return chunks
