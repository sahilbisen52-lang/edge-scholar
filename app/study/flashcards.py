"""Flashcard generator using local LLM."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.ai.base_provider import AIProvider
from app.documents.document_store import DocumentStore
from app.rag.prompt_templates import flashcard_prompt
from app.core.errors import ModelNotLoadedError

logger = logging.getLogger("edge_scholar.study")


@dataclass
class Flashcard:
    front: str
    back: str
    source: str = ""


class FlashcardGenerator:
    def __init__(self, provider: AIProvider, document_store: DocumentStore) -> None:
        self.provider = provider
        self.document_store = document_store

    def generate(
        self,
        document_id: str,
        num_cards: int = 10,
        max_tokens: int = 900,
    ) -> tuple[str, list[Flashcard]]:
        meta = self.document_store.get_document(document_id)
        if not meta:
            raise ValueError(f"Document not found: {document_id}")

        pages = self.document_store.get_pages(document_id)
        text = " ".join(p.text for p in pages)[:6000]

        prompt = flashcard_prompt(text, meta.filename, num_cards)
        try:
            result = self.provider.generate(prompt, max_tokens=max_tokens, temperature=0.3)
            return result.text, self._parse_flashcards(result.text)
        except ModelNotLoadedError:
            return "⚠️ No model loaded.", []
        except Exception as e:
            logger.exception("Flashcard generation failed: %s", e)
            return f"⚠️ Failed: {e}", []

    @staticmethod
    def _parse_flashcards(text: str) -> list[Flashcard]:
        cards = []
        blocks = re.split(r"\n---+\n|\n\n+", text)
        for block in blocks:
            block = block.strip()
            front_m = re.search(r"FRONT:\s*(.+)", block, re.IGNORECASE)
            back_m = re.search(r"BACK:\s*(.+)", block, re.IGNORECASE)
            src_m = re.search(r"SOURCE:\s*(.+)", block, re.IGNORECASE)
            if front_m and back_m:
                cards.append(Flashcard(
                    front=front_m.group(1).strip(),
                    back=back_m.group(1).strip(),
                    source=src_m.group(1).strip() if src_m else "",
                ))
        return cards
