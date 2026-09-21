"""Local storage management."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger("edge_scholar.privacy")


class LocalStorageInfo:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def get_total_size_mb(self) -> float:
        total = sum(f.stat().st_size for f in self.data_dir.rglob("*") if f.is_file())
        return total / (1024 * 1024)

    def get_document_count(self) -> int:
        doc_dir = self.data_dir / "documents"
        if not doc_dir.exists():
            return 0
        return len(list(doc_dir.iterdir()))

    def describe(self) -> dict:
        return {
            "data_directory": str(self.data_dir),
            "total_size_mb": round(self.get_total_size_mb(), 2),
            "document_count": self.get_document_count(),
            "ai_processing": "Local",
            "telemetry": "Disabled",
            "cloud_ai": "Disabled",
        }
