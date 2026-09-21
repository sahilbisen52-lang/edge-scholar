"""
ONNX Runtime provider for local AI inference.
Fallback between QNN and llama.cpp.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

from app.ai.base_provider import AIProvider, GenerationResult, ModelInfo, RuntimeInfo
from app.core.errors import ModelLoadError, ModelNotLoadedError

logger = logging.getLogger("edge_scholar.ai.onnx")


class ONNXProvider(AIProvider):
    """
    ONNX Runtime inference provider.
    Supports QNNExecutionProvider (NPU), CUDAExecutionProvider, or CPUExecutionProvider.
    """

    def __init__(self) -> None:
        self._session = None
        self._model_info: Optional[ModelInfo] = None
        self._active_provider: str = "CPUExecutionProvider"

    @staticmethod
    def is_available() -> bool:
        try:
            import onnxruntime  # noqa
            return True
        except ImportError:
            return False

    def load_model(self, model_id: str, model_path: str = "", **kwargs: Any) -> None:
        if not self.is_available():
            raise ModelLoadError(
                "onnxruntime not installed",
                user_message="ONNX Runtime not available. Run: pip install onnxruntime",
            )
        if not model_path or not Path(model_path).exists():
            raise ModelLoadError(f"Model file not found: {model_path}")

        import onnxruntime as ort
        available = ort.get_available_providers()

        # Prefer QNN > CUDA > CPU
        if "QNNExecutionProvider" in available:
            providers = ["QNNExecutionProvider", "CPUExecutionProvider"]
            self._active_provider = "QNNExecutionProvider"
        elif "CUDAExecutionProvider" in available:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self._active_provider = "CUDAExecutionProvider"
        else:
            providers = ["CPUExecutionProvider"]
            self._active_provider = "CPUExecutionProvider"

        self._session = ort.InferenceSession(model_path, providers=providers)
        self._model_info = ModelInfo(
            model_id=model_id,
            name=Path(model_path).stem,
            provider="ONNX Runtime",
            runtime=f"ONNX ({self._active_provider})",
            target_hardware="CPU/GPU/NPU",
        )
        logger.info("ONNX model loaded. Provider: %s", self._active_provider)

    def unload_model(self) -> None:
        self._session = None
        self._model_info = None

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.15, **kwargs: Any) -> GenerationResult:
        if self._session is None:
            raise ModelNotLoadedError()
        # ONNX text generation requires model-specific input/output mapping
        # This is a placeholder — real implementation is model-specific
        raise NotImplementedError(
            "ONNX generate() is model-specific. "
            "Implement input/output mapping for your specific ONNX model."
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Use LocalEmbeddings (sentence-transformers) for embeddings.")

    def health_check(self) -> bool:
        return self._session is not None

    def get_model_info(self) -> Optional[ModelInfo]:
        return self._model_info

    def get_runtime_info(self) -> RuntimeInfo:
        npu = self._active_provider == "QNNExecutionProvider"
        return RuntimeInfo(
            provider_name="ONNXProvider",
            runtime=f"ONNX Runtime ({self._active_provider})",
            accelerator="QNN/NPU" if npu else ("CUDA" if "CUDA" in self._active_provider else "CPU"),
            accelerator_verified=npu,
            is_ready=self._session is not None,
        )
