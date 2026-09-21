"""
Abstract base class for all AI providers in EdgeScholar.
Never hard-code to one runtime — swap via config.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generator, Optional


@dataclass
class ModelInfo:
    model_id: str
    name: str
    version: str = ""
    provider: str = ""
    runtime: str = ""
    target_hardware: str = ""
    precision: str = ""
    size_mb: float = 0.0
    license: str = ""
    parameters: str = ""


@dataclass
class RuntimeInfo:
    provider_name: str
    runtime: str
    accelerator: str = "CPU"
    accelerator_verified: bool = False
    backend_version: str = ""
    is_ready: bool = False
    notes: str = ""

    def badge(self) -> str:
        acc = self.accelerator if self.accelerator_verified else "CPU"
        return f"LOCAL • {self.runtime}/{acc}"


@dataclass
class GenerationResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    ttft_seconds: float = 0.0
    total_seconds: float = 0.0
    tokens_per_second: float = 0.0
    runtime_info: Optional[RuntimeInfo] = None
    truncated: bool = False


class AIProvider(ABC):
    """Abstract interface for all AI inference providers."""

    @abstractmethod
    def load_model(self, model_id: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def unload_model(self) -> None: ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.15,
        **kwargs: Any,
    ) -> GenerationResult: ...

    def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.15,
        **kwargs: Any,
    ) -> Generator[str, None, GenerationResult]:
        """Default: non-streaming fallback. Providers may override."""
        result = self.generate(prompt, max_tokens=max_tokens, temperature=temperature, **kwargs)
        yield result.text
        return result

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    @abstractmethod
    def get_model_info(self) -> Optional[ModelInfo]: ...

    @abstractmethod
    def get_runtime_info(self) -> RuntimeInfo: ...

    def is_loaded(self) -> bool:
        info = self.get_model_info()
        return info is not None
