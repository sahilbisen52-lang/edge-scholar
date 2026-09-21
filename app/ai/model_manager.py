"""
Model manager — reads model manifest, tracks download/install status.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.utils.hashing import sha256_file

logger = logging.getLogger("edge_scholar.ai.model_manager")


@dataclass
class ModelManifestEntry:
    name: str
    model_id: str
    provider: str
    version: str = ""
    source: str = ""
    license: str = ""
    runtime: str = ""
    target_chipset: str = ""
    precision: str = ""
    size_mb: float = 0.0
    sha256: str = ""
    filename: str = ""
    description: str = ""
    downloaded: bool = False
    verified: bool = False
    status: str = "missing"  # missing | downloading | installed | incompatible | error

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "model_id": self.model_id,
            "provider": self.provider,
            "version": self.version,
            "source": self.source,
            "license": self.license,
            "runtime": self.runtime,
            "target_chipset": self.target_chipset,
            "precision": self.precision,
            "size_mb": self.size_mb,
            "sha256": self.sha256,
            "filename": self.filename,
            "description": self.description,
            "downloaded": self.downloaded,
            "verified": self.verified,
            "status": self.status,
        }


DEFAULT_MANIFEST = [
    ModelManifestEntry(
        name="Llama 3.2 3B Instruct (GGUF Q4)",
        model_id="llama-3.2-3b-instruct-q4",
        provider="llama.cpp",
        version="3.2",
        source="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF",
        license="Llama 3.2 Community License",
        runtime="llama.cpp",
        target_chipset="Any CPU (ARM64 optimized)",
        precision="Q4_K_M",
        size_mb=2100,
        filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        description="Compact 3B parameter model, good for Q&A and summarization on 8GB+ RAM devices.",
    ),
    ModelManifestEntry(
        name="Whisper Base (local ASR)",
        model_id="whisper-base",
        provider="faster-whisper",
        version="v3",
        source="https://huggingface.co/Systran/faster-whisper-base",
        license="MIT",
        runtime="faster-whisper",
        target_chipset="Any CPU",
        precision="INT8",
        size_mb=74,
        filename="whisper-base",
        description="Fast local speech-to-text. ~74MB download. Good for lecture transcription.",
    ),
    ModelManifestEntry(
        name="Sentence Transformers MiniLM (Embeddings)",
        model_id="all-MiniLM-L6-v2",
        provider="sentence-transformers",
        version="v2",
        source="https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
        license="Apache 2.0",
        runtime="sentence-transformers",
        target_chipset="Any CPU",
        precision="FP32",
        size_mb=90,
        filename="all-MiniLM-L6-v2",
        description="Local embedding model for semantic search. Auto-downloads via sentence-transformers.",
    ),
]


class ModelManager:
    def __init__(self, models_dir: Path) -> None:
        self.models_dir = models_dir
        models_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = models_dir / "model_manifest.json"
        self._manifest: list[ModelManifestEntry] = []
        self._load_manifest()

    def _load_manifest(self) -> None:
        if self._manifest_path.exists():
            try:
                data = json.loads(self._manifest_path.read_text())
                self._manifest = [ModelManifestEntry(**entry) for entry in data]
                logger.info("Loaded manifest with %d entries", len(self._manifest))
            except Exception as e:
                logger.warning("Manifest load failed, using defaults: %s", e)
                self._manifest = list(DEFAULT_MANIFEST)
        else:
            self._manifest = list(DEFAULT_MANIFEST)
            self._save_manifest()

        # Refresh download status
        self._refresh_status()

    def _refresh_status(self) -> None:
        for entry in self._manifest:
            if entry.filename:
                candidate = self.models_dir / entry.filename
                if candidate.exists():
                    entry.downloaded = True
                    # Verify hash if known
                    if entry.sha256:
                        try:
                            actual = sha256_file(candidate)
                            entry.verified = actual == entry.sha256
                            entry.status = "installed" if entry.verified else "error"
                        except Exception:
                            entry.status = "error"
                    else:
                        entry.status = "installed"
                        entry.verified = False  # Can't verify without hash
                else:
                    entry.downloaded = False
                    entry.verified = False
                    entry.status = "missing"

    def _save_manifest(self) -> None:
        self._manifest_path.write_text(
            json.dumps([e.to_dict() for e in self._manifest], indent=2),
            encoding="utf-8",
        )

    def list_models(self) -> list[ModelManifestEntry]:
        self._refresh_status()
        return list(self._manifest)

    def get_model(self, model_id: str) -> Optional[ModelManifestEntry]:
        for entry in self._manifest:
            if entry.model_id == model_id:
                return entry
        return None

    def find_installed_gguf(self) -> Optional[Path]:
        """Find the first installed .gguf file."""
        for f in self.models_dir.glob("*.gguf"):
            return f
        return None

    def get_status_summary(self) -> dict:
        self._refresh_status()
        installed = [e for e in self._manifest if e.status == "installed"]
        return {
            "total": len(self._manifest),
            "installed": len(installed),
            "installed_names": [e.name for e in installed],
        }
