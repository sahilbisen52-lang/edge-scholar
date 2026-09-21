"""
Qualcomm QNN AI provider (Snapdragon production path).

This provider targets Snapdragon-powered Windows PCs with QNN runtime.
On non-Snapdragon hardware, it gracefully reports as unavailable.

IMPORTANT: This provider only reports NPU acceleration as VERIFIED when
the QNN runtime explicitly confirms it. We never fake hardware claims.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from app.ai.base_provider import AIProvider, GenerationResult, ModelInfo, RuntimeInfo
from app.core.errors import ModelLoadError, ModelNotLoadedError

logger = logging.getLogger("edge_scholar.ai.qnn")


class QNNProvider(AIProvider):
    """
    Qualcomm Neural Network (QNN) inference provider.
    
    Production path for Snapdragon X / Snapdragon 8cx and newer devices.
    Requires: onnxruntime with QNNExecutionProvider, or qai_hub runtime.
    """

    def __init__(self) -> None:
        self._model = None
        self._session = None
        self._model_info: Optional[ModelInfo] = None
        self._qnn_available = self._check_qnn_available()

    @staticmethod
    def _check_qnn_available() -> bool:
        """Check if QNN execution provider is available."""
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if "QNNExecutionProvider" in providers:
                logger.info("QNN Execution Provider DETECTED")
                return True
            logger.info("QNN Execution Provider not found. Available: %s", providers)
        except ImportError:
            logger.debug("onnxruntime not installed")
        return False

    def is_qnn_available(self) -> bool:
        return self._qnn_available

    def load_model(self, model_id: str, model_path: str = "", **kwargs: Any) -> None:
        if not self._qnn_available:
            raise ModelLoadError(
                "QNN runtime not available on this device",
                user_message="Qualcomm QNN runtime is not available. Try ONNX or llama.cpp provider.",
            )
        if not model_path:
            raise ModelLoadError("model_path required for QNN provider")
        try:
            import onnxruntime as ort
            session_options = ort.SessionOptions()
            providers = [
                ("QNNExecutionProvider", {"device_type": "NPU"}),
                "CPUExecutionProvider",
            ]
            self._session = ort.InferenceSession(model_path, providers=providers, sess_options=session_options)
            self._model_info = ModelInfo(
                model_id=model_id,
                name=model_id,
                provider="QNN",
                runtime="ONNX + QNN",
                target_hardware="Snapdragon NPU",
                precision="INT8/FP16",
            )
            logger.info("QNN model loaded: %s", model_id)
        except Exception as e:
            raise ModelLoadError(str(e), user_message=f"QNN model load failed: {e}")

    def unload_model(self) -> None:
        self._session = None
        self._model_info = None

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.15, **kwargs: Any) -> GenerationResult:
        if self._session is None:
            raise ModelNotLoadedError()
        # QNN generation would be model-specific (e.g., Llama via QNN)
        # Placeholder: real implementation depends on specific model's input/output schema
        raise NotImplementedError(
            "QNN generate() requires model-specific input/output schema. "
            "Integrate with your specific Qualcomm AI Hub model."
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("QNN embedding requires a QNN-optimized embedding model.")

    def health_check(self) -> bool:
        return self._qnn_available and self._session is not None

    def get_model_info(self) -> Optional[ModelInfo]:
        return self._model_info

    def get_runtime_info(self) -> RuntimeInfo:
        if not self._qnn_available:
            return RuntimeInfo(
                provider_name="QNNProvider",
                runtime="QNN",
                accelerator="NOT DETECTED",
                accelerator_verified=False,
                is_ready=False,
                notes="QNN runtime not available on this device. This is the Snapdragon production path.",
            )
        return RuntimeInfo(
            provider_name="QNNProvider",
            runtime="ONNX + QNNExecutionProvider",
            accelerator="Qualcomm NPU",
            accelerator_verified=True,  # Only True when QNNExecutionProvider confirmed
            is_ready=self._session is not None,
            notes="QNN Execution Provider detected. NPU acceleration available.",
        )
