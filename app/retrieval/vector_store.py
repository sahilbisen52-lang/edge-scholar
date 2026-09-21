"""FAISS-based local vector store."""
from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

from app.config.constants import EMBEDDING_DIM
from app.core.errors import IndexError as EdgeIndexError

logger = logging.getLogger("edge_scholar.retrieval")


class VectorStore:
    def __init__(self, index_dir: Path, dim: int = EMBEDDING_DIM) -> None:
        self.index_dir = index_dir
        self.dim = dim
        self._index = None
        self._metadata: list[dict] = []  # parallel list to FAISS index
        self._index_path = index_dir / "faiss.index"
        self._meta_path = index_dir / "faiss_meta.pkl"
        index_dir.mkdir(parents=True, exist_ok=True)
        self._load_if_exists()

    def _load_if_exists(self) -> None:
        if self._index_path.exists() and self._meta_path.exists():
            try:
                import faiss
                self._index = faiss.read_index(str(self._index_path))
                with open(self._meta_path, "rb") as f:
                    self._metadata = pickle.load(f)
                logger.info("Loaded FAISS index: %d vectors", self._index.ntotal)
            except Exception as e:
                logger.warning("Could not load existing index: %s", e)
                self._index = None
                self._metadata = []

    def _ensure_index(self) -> None:
        if self._index is None:
            import faiss
            self._index = faiss.IndexFlatIP(self.dim)  # Inner product (cosine on normalized)
            logger.info("Created new FAISS index (dim=%d)", self.dim)

    def add(self, embeddings: np.ndarray, metadata_list: list[dict]) -> None:
        if len(embeddings) == 0:
            return
        self._ensure_index()
        self._index.add(embeddings.astype(np.float32))
        self._metadata.extend(metadata_list)
        self._save()
        logger.info("Added %d vectors. Total: %d", len(embeddings), self._index.ntotal)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[tuple[float, dict]]:
        if self._index is None or self._index.ntotal == 0:
            return []
        q = query_embedding.reshape(1, -1).astype(np.float32)
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(q, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._metadata):
                results.append((float(score), self._metadata[idx]))
        return results

    def delete_by_document(self, document_id: str) -> None:
        """Remove all vectors associated with a document_id."""
        # FAISS flat index doesn't support deletion; rebuild without the document
        if self._index is None:
            return
        keep_indices = [i for i, m in enumerate(self._metadata) if m.get("document_id") != document_id]
        if len(keep_indices) == len(self._metadata):
            return  # Nothing to delete
        import faiss
        new_meta = [self._metadata[i] for i in keep_indices]
        # We need all vectors to rebuild; store them during add (too memory-intensive for huge indexes)
        # For MVP: rebuild from stored embeddings file if it exists
        self._metadata = new_meta
        self._index = faiss.IndexFlatIP(self.dim)
        if self._vec_path().exists():
            import pickle as pk
            with open(self._vec_path(), "rb") as f:
                all_vecs = pk.load(f)
            kept_vecs = np.array([all_vecs[i] for i in keep_indices], dtype=np.float32)
            if len(kept_vecs) > 0:
                self._index.add(kept_vecs)
            # Save filtered vecs back
            with open(self._vec_path(), "wb") as f:
                pk.dump(kept_vecs, f)
        self._save()
        logger.info("Deleted document %s from vector store", document_id)

    def _vec_path(self) -> Path:
        return self.index_dir / "faiss_vecs.pkl"

    def _save(self) -> None:
        import faiss
        faiss.write_index(self._index, str(self._index_path))
        with open(self._meta_path, "wb") as f:
            pickle.dump(self._metadata, f)

    def count(self) -> int:
        if self._index is None:
            return 0
        return self._index.ntotal

    def clear(self) -> None:
        import faiss
        self._index = faiss.IndexFlatIP(self.dim)
        self._metadata = []
        self._save()
