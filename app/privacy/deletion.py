"""Data deletion utilities."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger("edge_scholar.privacy")


class DeletionManager:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def delete_all_data(self, keep_exports: bool = True) -> None:
        """Delete all application data. Optionally keep user exports."""
        logger.warning("Deleting all EdgeScholar data (keep_exports=%s)", keep_exports)
        for subdir in ["documents", "indexes", "transcripts", "cache", "benchmarks"]:
            target = self.data_dir / subdir
            if target.exists():
                shutil.rmtree(target)
                target.mkdir(parents=True, exist_ok=True)
                logger.info("Cleared: %s", target)

        if not keep_exports:
            exports = self.data_dir / "exports"
            if exports.exists():
                shutil.rmtree(exports)
                exports.mkdir(parents=True, exist_ok=True)

    def delete_document_data(self, document_id: str) -> None:
        """Delete all data associated with a specific document ID."""
        logger.info("Deleting data for document: %s", document_id)
        # Document-specific deletions handled by DocumentStore and VectorStore
