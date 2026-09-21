"""
Mock AI provider for testing and development without a real model.
Never use this in production.
"""
from __future__ import annotations

import time
from typing import Any, Generator, Optional

from app.ai.base_provider import AIProvider, GenerationResult, ModelInfo, RuntimeInfo


MOCK_RESPONSES = {
    "summarize": "This document covers key concepts in the selected topic. [MOCK SUMMARY — no model loaded]",
    "quiz": "Q1: What is the main concept? A) Option A B) Option B C) Option C D) Option D\nAnswer: A [MOCK QUIZ]",
    "default": (
        "⚠️ No local AI model is currently loaded. "
        "This is a placeholder response from the Mock Provider.\n\n"
        "To enable real AI responses:\n"
        "1. Open Model Manager\n"
        "2. Download a compatible local model\n"
        "3. The app will automatically use it for inference"
    ),
}


class MockProvider(AIProvider):
    """Development mock — returns deterministic placeholder responses."""

    def __init__(self) -> None:
        self._loaded = False
        self._model_id = "mock"

    def load_model(self, model_id: str = "mock", **kwargs: Any) -> None:
        self._loaded = True
        self._model_id = model_id

    def unload_model(self) -> None:
        self._loaded = False

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.15,
        **kwargs: Any,
    ) -> GenerationResult:
        t0 = time.perf_counter()
        time.sleep(0.05)  # Simulate tiny latency

        # Choose response based on prompt content
        p_lower = prompt.lower()
        if "summarize" in p_lower or "summary" in p_lower:
            text = MOCK_RESPONSES["summarize"]
        elif "quiz" in p_lower or "question" in p_lower:
            text = MOCK_RESPONSES["quiz"]
        else:
            text = MOCK_RESPONSES["default"]

        elapsed = time.perf_counter() - t0
        return GenerationResult(
            text=text,
            input_tokens=len(prompt) // 4,
            output_tokens=len(text) // 4,
            ttft_seconds=elapsed,
            total_seconds=elapsed,
            tokens_per_second=0.0,
            runtime_info=self.get_runtime_info(),
        )

    def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.15,
        **kwargs: Any,
    ) -> Generator[str, None, GenerationResult]:
        result = self.generate(prompt, max_tokens=max_tokens, temperature=temperature)
        # Stream word by word for UX demo
        words = result.text.split()
        for word in words:
            yield word + " "
            time.sleep(0.01)
        return result

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Return zero vectors (not suitable for real search)
        return [[0.0] * 384 for _ in texts]

    def health_check(self) -> bool:
        return True

    def get_model_info(self) -> Optional[ModelInfo]:
        if not self._loaded:
            return None
        return ModelInfo(
            model_id="mock",
            name="Mock Provider",
            version="0.1.0",
            provider="EdgeScholar Dev",
            runtime="Mock",
            target_hardware="Any",
            precision="N/A",
        )

    def get_runtime_info(self) -> RuntimeInfo:
        return RuntimeInfo(
            provider_name="MockProvider",
            runtime="Mock",
            accelerator="None",
            accelerator_verified=False,
            is_ready=self._loaded,
            notes="Development mock. Install a local model for real inference.",
        )

    def badge(self) -> str:
        return "LOCAL • MOCK (No Model)"
