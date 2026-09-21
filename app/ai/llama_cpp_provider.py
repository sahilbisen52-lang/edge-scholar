"""
llama.cpp AI provider using llama-cpp-python.
Works on CPU with GGUF model files. Supports streaming.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Generator, Optional

from app.ai.base_provider import AIProvider, GenerationResult, ModelInfo, RuntimeInfo
from app.core.errors import ModelLoadError, ModelNotLoadedError, GenerationError

logger = logging.getLogger("edge_scholar.ai.llama_cpp")


class LlamaCppProvider(AIProvider):
    """
    llama.cpp provider via llama-cpp-python.
    Supports GGUF model files. Works fully offline.
    
    On Snapdragon Windows: may use AVX2/Vulkan acceleration automatically.
    Does NOT claim NPU usage — llama.cpp uses CPU/GPU.
    """

    def __init__(self) -> None:
        self._llm = None
        self._model_info: Optional[ModelInfo] = None
        self._model_path: Optional[Path] = None

    @staticmethod
    def is_available() -> bool:
        try:
            import llama_cpp  # noqa
            return True
        except ImportError:
            return False

    def load_model(
        self,
        model_id: str,
        model_path: str = "",
        n_ctx: int = 4096,
        n_threads: int = 4,
        n_gpu_layers: int = 0,
        **kwargs: Any,
    ) -> None:
        if not self.is_available():
            raise ModelLoadError(
                "llama-cpp-python not installed",
                user_message="llama.cpp runtime not available. Run: pip install llama-cpp-python",
            )
        if not model_path or not Path(model_path).exists():
            raise ModelLoadError(
                f"Model file not found: {model_path}",
                user_message=f"Model file not found at: {model_path}",
            )

        try:
            from llama_cpp import Llama
            logger.info("Loading llama.cpp model: %s", model_path)
            t0 = time.perf_counter()
            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
            )
            elapsed = time.perf_counter() - t0
            self._model_path = Path(model_path)
            self._model_info = ModelInfo(
                model_id=model_id,
                name=Path(model_path).stem,
                provider="llama.cpp",
                runtime="llama.cpp",
                target_hardware="CPU (GPU optional)",
                precision="GGUF",
            )
            logger.info("llama.cpp model loaded in %.2fs", elapsed)
        except Exception as e:
            raise ModelLoadError(str(e), user_message=f"Failed to load model: {e}")

    def unload_model(self) -> None:
        self._llm = None
        self._model_info = None

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.15,
        **kwargs: Any,
    ) -> GenerationResult:
        if self._llm is None:
            raise ModelNotLoadedError()
        try:
            t0 = time.perf_counter()
            first_token_time = None

            output = self._llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                echo=False,
            )
            elapsed = time.perf_counter() - t0

            text = output["choices"][0]["text"].strip()
            usage = output.get("usage", {})
            input_tokens = usage.get("prompt_tokens", len(prompt) // 4)
            output_tokens = usage.get("completion_tokens", len(text) // 4)
            tps = output_tokens / elapsed if elapsed > 0 else 0.0

            return GenerationResult(
                text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                ttft_seconds=elapsed,  # Non-streaming: same as total
                total_seconds=elapsed,
                tokens_per_second=tps,
                runtime_info=self.get_runtime_info(),
            )
        except Exception as e:
            raise GenerationError(str(e))

    def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.15,
        **kwargs: Any,
    ) -> Generator[str, None, GenerationResult]:
        if self._llm is None:
            raise ModelNotLoadedError()

        t0 = time.perf_counter()
        ttft = None
        output_tokens = 0
        full_text = ""

        for chunk in self._llm(prompt, max_tokens=max_tokens, temperature=temperature, stream=True, echo=False):
            token = chunk["choices"][0]["text"]
            if token:
                if ttft is None:
                    ttft = time.perf_counter() - t0
                full_text += token
                output_tokens += 1
                yield token

        elapsed = time.perf_counter() - t0
        return GenerationResult(
            text=full_text,
            input_tokens=len(prompt) // 4,
            output_tokens=output_tokens,
            ttft_seconds=ttft or elapsed,
            total_seconds=elapsed,
            tokens_per_second=output_tokens / elapsed if elapsed > 0 else 0.0,
            runtime_info=self.get_runtime_info(),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._llm is None:
            raise ModelNotLoadedError()
        results = []
        for text in texts:
            emb = self._llm.embed(text)
            results.append(emb)
        return results

    def health_check(self) -> bool:
        return self._llm is not None

    def get_model_info(self) -> Optional[ModelInfo]:
        return self._model_info

    def get_runtime_info(self) -> RuntimeInfo:
        return RuntimeInfo(
            provider_name="LlamaCppProvider",
            runtime="llama.cpp",
            accelerator="CPU",
            accelerator_verified=False,  # CPU is certain; GPU layers not verified here
            is_ready=self._llm is not None,
            backend_version="",
            notes="llama.cpp GGUF inference. CPU execution. GPU layers configurable.",
        )
