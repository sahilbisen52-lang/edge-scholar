"""
Provider factory: detects environment and selects the best available AI provider.

Priority order:
1. QNN (Snapdragon NPU) — if QNNExecutionProvider detected
2. llama.cpp — if installed and model file present
3. ONNX Runtime — if installed
4. Mock — always available fallback

The factory never fabricates hardware capabilities.
"""
from __future__ import annotations

import logging
import platform
import sys
from pathlib import Path
from typing import Optional

from app.ai.base_provider import AIProvider, RuntimeInfo
from app.ai.mock_provider import MockProvider

logger = logging.getLogger("edge_scholar.ai.factory")


class ProviderFactory:
    """Detects environment and returns the best available AIProvider."""

    def __init__(self, preferred: str = "auto", models_dir: Optional[Path] = None) -> None:
        self.preferred = preferred
        self.models_dir = models_dir or Path("models")
        self._diagnostics: dict[str, str] = {}

    def create(self) -> AIProvider:
        """Return the best available provider, loading mock as fallback."""
        provider = self._select_provider()
        logger.info("Selected AI provider: %s", provider.__class__.__name__)
        # Auto-load mock immediately
        if isinstance(provider, MockProvider):
            provider.load_model("mock")
        return provider

    def _select_provider(self) -> AIProvider:
        if self.preferred == "mock":
            return MockProvider()

        if self.preferred == "qnn" or self.preferred == "auto":
            qnn = self._try_qnn()
            if qnn:
                return qnn

        if self.preferred in ("llama_cpp", "auto"):
            llama = self._try_llama_cpp()
            if llama:
                return llama

        if self.preferred in ("onnx", "auto"):
            onnx = self._try_onnx()
            if onnx:
                return onnx

        logger.info("No capable provider found. Using MockProvider.")
        self._diagnostics["provider"] = "mock"
        return MockProvider()

    def _try_qnn(self) -> Optional[AIProvider]:
        try:
            from app.ai.qnn_provider import QNNProvider
            provider = QNNProvider()
            if provider.is_qnn_available():
                logger.info("QNN provider available (Snapdragon NPU detected)")
                self._diagnostics["provider"] = "qnn"
                return provider
            else:
                self._diagnostics["qnn"] = "QNNExecutionProvider not detected"
        except Exception as e:
            self._diagnostics["qnn_error"] = str(e)
        return None

    def _try_llama_cpp(self) -> Optional[AIProvider]:
        try:
            from app.ai.llama_cpp_provider import LlamaCppProvider
            if LlamaCppProvider.is_available():
                # Check if any GGUF model file exists
                gguf_files = list(self.models_dir.glob("**/*.gguf"))
                if gguf_files:
                    provider = LlamaCppProvider()
                    model_path = str(gguf_files[0])
                    logger.info("Auto-loading llama.cpp model: %s", model_path)
                    provider.load_model(gguf_files[0].stem, model_path=model_path)
                    self._diagnostics["provider"] = "llama_cpp"
                    return provider
                else:
                    self._diagnostics["llama_cpp"] = "No .gguf model files found in models/"
            else:
                self._diagnostics["llama_cpp"] = "llama-cpp-python not installed"
        except Exception as e:
            self._diagnostics["llama_cpp_error"] = str(e)
        return None

    def _try_onnx(self) -> Optional[AIProvider]:
        try:
            from app.ai.onnx_provider import ONNXProvider
            if ONNXProvider.is_available():
                onnx_files = list(self.models_dir.glob("**/*.onnx"))
                if onnx_files:
                    provider = ONNXProvider()
                    provider.load_model(onnx_files[0].stem, model_path=str(onnx_files[0]))
                    self._diagnostics["provider"] = "onnx"
                    return provider
                self._diagnostics["onnx"] = "No .onnx model files found"
        except Exception as e:
            self._diagnostics["onnx_error"] = str(e)
        return None

    def get_diagnostics(self) -> dict[str, str]:
        return dict(self._diagnostics)

    def get_environment_summary(self) -> dict:
        """Return a summary of the current environment for the hardware panel."""
        import platform
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor() or "Unknown",
            "python_version": sys.version.split()[0],
        }

        # Try psutil for memory
        try:
            import psutil
            mem = psutil.virtual_memory()
            info["ram_gb"] = round(mem.total / (1024 ** 3), 1)
        except Exception:
            info["ram_gb"] = "Unknown"

        # Check runtimes
        runtimes = {}
        try:
            import onnxruntime as ort
            runtimes["onnxruntime"] = ort.__version__
            runtimes["onnx_providers"] = ", ".join(ort.get_available_providers())
        except ImportError:
            runtimes["onnxruntime"] = "Not installed"

        try:
            import llama_cpp
            runtimes["llama_cpp"] = getattr(llama_cpp, "__version__", "installed")
        except ImportError:
            runtimes["llama_cpp"] = "Not installed"

        try:
            import sentence_transformers
            runtimes["sentence_transformers"] = sentence_transformers.__version__
        except ImportError:
            runtimes["sentence_transformers"] = "Not installed"

        info["runtimes"] = runtimes

        # Snapdragon detection
        snapdragon_indicators = []
        proc = info["processor"].lower()
        arch = info["architecture"].lower()
        if "snapdragon" in proc:
            snapdragon_indicators.append("Processor name contains 'Snapdragon'")
        if "qualcomm" in proc:
            snapdragon_indicators.append("Processor name contains 'Qualcomm'")
        if arch in ("arm64", "aarch64") and platform.system() == "Windows":
            snapdragon_indicators.append("ARM64 architecture on Windows (likely Snapdragon)")

        info["snapdragon_indicators"] = snapdragon_indicators
        info["snapdragon_detected"] = len(snapdragon_indicators) > 0

        return info
