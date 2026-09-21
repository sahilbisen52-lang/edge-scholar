"""Structured notes generator using local LLM."""
from __future__ import annotations

import logging

from app.ai.base_provider import AIProvider
from app.documents.document_store import DocumentStore
from app.rag.prompt_templates import notes_prompt
from app.core.errors import ModelNotLoadedError

logger = logging.getLogger("edge_scholar.study")


class NotesGenerator:
    def __init__(self, provider: AIProvider, document_store: DocumentStore) -> None:
        self.provider = provider
        self.document_store = document_store

    def generate(self, document_id: str, max_tokens: int = 900, temperature: float = 0.2) -> str:
        meta = self.document_store.get_document(document_id)
        if not meta:
            raise ValueError(f"Document not found: {document_id}")

        pages = self.document_store.get_pages(document_id)
        text = " ".join(p.text for p in pages)[:6000]

        prompt = notes_prompt(text, meta.filename)
        try:
            result = self.provider.generate(prompt, max_tokens=max_tokens, temperature=temperature)
            return result.text
        except ModelNotLoadedError:
            return "⚠️ No model loaded."
        except Exception as e:
            logger.exception("Notes generation failed: %s", e)
            return f"⚠️ Failed: {e}"
