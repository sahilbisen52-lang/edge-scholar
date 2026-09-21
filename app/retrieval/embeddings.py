"""Local embedding provider using sentence-transformers."""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

import numpy as np

from app.config.constants import DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIM
from app.core.errors import EmbeddingError

logger = logging.getLogger("edge_scholar.retrieval")


class LocalEmbeddings:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self._dim = EMBEDDING_DIM

    def _ensure_loaded(self) -> None:
        if self._model is None:
            logger.info("Loading embedding model: %s", self.model_name)
            try:
                from sentence_transformers import SentenceTransformer
                # Prefer local offline cache first to guarantee 100% offline operation
                try:
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                except Exception:
                    self._model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded.")
            except Exception as e:
                raise EmbeddingError(
                    str(e),
                    user_message="Could not load embedding model. Ensure sentence-transformers is installed.",
                )

    def embed(self, texts: list[str]) -> np.ndarray:
        self._ensure_loaded()
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        try:
            t0 = time.perf_counter()
            embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            elapsed = time.perf_counter() - t0
            logger.debug("Embedded %d texts in %.2fs", len(texts), elapsed)
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            raise EmbeddingError(str(e))

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    @property
    def dim(self) -> int:
        return self._dim

    def is_loaded(self) -> bool:
        return self._model is not None
