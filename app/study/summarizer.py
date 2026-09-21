"""Document summarizer using local LLM."""
from __future__ import annotations

import logging
from typing import Optional

from app.ai.base_provider import AIProvider, GenerationResult
from app.documents.document_store import DocumentStore
from app.rag.prompt_templates import summarize_prompt
from app.core.errors import ModelNotLoadedError

logger = logging.getLogger("edge_scholar.study")


class Summarizer:
    def __init__(self, provider: AIProvider, document_store: DocumentStore) -> None:
        self.provider = provider
        self.document_store = document_store

    def summarize_document(
        self,
        document_id: str,
        max_tokens: int = 700,
        temperature: float = 0.2,
    ) -> str:
        """Summarize a document by ID. Returns formatted summary text."""
        meta = self.document_store.get_document(document_id)
        if not meta:
            raise ValueError(f"Document not found: {document_id}")

        pages = self.document_store.get_pages(document_id)
        if not pages:
            return "No content found in this document."

        # Concatenate up to ~6000 chars for summary
        text = " ".join(p.text for p in pages)
        text = text[:6000]

        prompt = summarize_prompt(text, meta.filename)
        try:
            result = self.provider.generate(prompt, max_tokens=max_tokens, temperature=temperature)
            return result.text
        except ModelNotLoadedError:
            return "⚠️ No model loaded. Please install a local model via Model Manager."
        except Exception as e:
            logger.exception("Summarization failed: %s", e)
            return f"⚠️ Summarization failed: {e}"
