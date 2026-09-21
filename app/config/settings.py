"""Persistent application settings using pydantic-settings."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EdgeScholarSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EDGESCHOLAR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Model selection
    selected_llm_model: str = Field(default="mock", description="Selected LLM model ID")
    selected_embedding_model: str = Field(default="all-MiniLM-L6-v2")
    selected_asr_model: str = Field(default="whisper-base")
    preferred_runtime: Literal["auto", "qnn", "onnx", "llama_cpp", "mock"] = Field(default="auto")

    # Privacy
    offline_mode: bool = Field(default=False)
    telemetry_enabled: bool = Field(default=False)
    cloud_ai_enabled: bool = Field(default=False)

    # Chunking
    chunk_size: int = Field(default=600, ge=100, le=2000)
    chunk_overlap: int = Field(default=100, ge=0, le=500)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)

    # Generation
    temperature: float = Field(default=0.15, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=64, le=4096)

    # Benchmark
    benchmark_iterations: int = Field(default=3, ge=1, le=20)

    # UI
    theme: Literal["dark", "light"] = Field(default="dark")
    font_size: int = Field(default=14, ge=10, le=24)

    @classmethod
    def load(cls, settings_path: Path) -> "EdgeScholarSettings":
        """Load settings from a JSON file, fall back to defaults."""
        if settings_path.exists():
            try:
                data = json.loads(settings_path.read_text(encoding="utf-8"))
                return cls(**data)
            except Exception:
                pass
        return cls()

    def save(self, settings_path: Path) -> None:
        """Persist settings to a JSON file."""
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(self.model_dump(), indent=2),
            encoding="utf-8",
        )
