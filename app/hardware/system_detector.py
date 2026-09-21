"""System hardware and software environment detector."""
from __future__ import annotations

import logging
import platform
import sys
from typing import Any

logger = logging.getLogger("edge_scholar.hardware")

# Status constants — conservative detection
VERIFIED = "VERIFIED"
PRESENT = "PRESENT"
NOT_DETECTED = "NOT DETECTED"
UNKNOWN = "UNKNOWN"

_CACHED_SYSTEM_INFO: dict[str, Any] | None = None


def detect_system(force_refresh: bool = False) -> dict[str, Any]:
    """Return comprehensive system information with caching for high performance."""
    global _CACHED_SYSTEM_INFO
    if _CACHED_SYSTEM_INFO is not None and not force_refresh:
        return _CACHED_SYSTEM_INFO

    info: dict[str, Any] = {}

    # OS
    info["os"] = platform.system()
    info["os_version"] = platform.version()
    info["os_release"] = platform.release()
    info["architecture"] = platform.machine()
    info["processor"] = platform.processor() or UNKNOWN

    # Python
    info["python_version"] = sys.version.split()[0]

    # RAM
    try:
        import psutil
        mem = psutil.virtual_memory()
        info["ram_gb"] = round(mem.total / (1024 ** 3), 1)
        info["ram_available_gb"] = round(mem.available / (1024 ** 3), 1)
    except Exception:
        info["ram_gb"] = UNKNOWN
        info["ram_available_gb"] = UNKNOWN

    # CPU cores
    try:
        import os
        info["cpu_cores_logical"] = os.cpu_count() or UNKNOWN
    except Exception:
        info["cpu_cores_logical"] = UNKNOWN

    # Snapdragon detection
    info.update(_detect_snapdragon(info))

    # Runtimes
    info["runtimes"] = _detect_runtimes()

    _CACHED_SYSTEM_INFO = info
    return info


def _detect_snapdragon(info: dict) -> dict:
    result = {}
    proc = str(info.get("processor", "")).lower()
    arch = str(info.get("architecture", "")).lower()
    os_name = str(info.get("os", ""))

    indicators = []
    if "snapdragon" in proc:
        indicators.append("'Snapdragon' in processor name")
    if "qualcomm" in proc:
        indicators.append("'Qualcomm' in processor name")
    if arch in ("arm64", "aarch64") and os_name == "Windows":
        indicators.append("ARM64 architecture on Windows")

    result["snapdragon_indicators"] = indicators
    result["snapdragon_status"] = PRESENT if indicators else NOT_DETECTED

    # QNN detection
    qnn_status = NOT_DETECTED
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        if "QNNExecutionProvider" in providers:
            qnn_status = VERIFIED
        else:
            qnn_status = NOT_DETECTED
    except ImportError:
        qnn_status = NOT_DETECTED
    result["qnn_status"] = qnn_status

    # NPU detection based on QNN (conservative)
    if qnn_status == VERIFIED:
        result["npu_status"] = "Available through QNN runtime"
    elif indicators:
        result["npu_status"] = "Possible (Snapdragon indicators present, QNN not confirmed)"
    else:
        result["npu_status"] = NOT_DETECTED

    return result


def _detect_runtimes() -> dict[str, str]:
    runtimes = {}

    # ONNX Runtime
    try:
        import onnxruntime as ort
        runtimes["onnxruntime"] = ort.__version__
        runtimes["onnx_providers"] = ", ".join(ort.get_available_providers())
    except ImportError:
        runtimes["onnxruntime"] = NOT_DETECTED

    # llama.cpp
    try:
        import llama_cpp
        runtimes["llama_cpp"] = getattr(llama_cpp, "__version__", PRESENT)
    except ImportError:
        runtimes["llama_cpp"] = NOT_DETECTED

    # sentence-transformers
    try:
        import sentence_transformers
        runtimes["sentence_transformers"] = sentence_transformers.__version__
    except ImportError:
        runtimes["sentence_transformers"] = NOT_DETECTED

    # PyMuPDF
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        runtimes["pymupdf"] = fitz.version[0]
    except ImportError:
        runtimes["pymupdf"] = NOT_DETECTED

    # FAISS
    try:
        import faiss
        runtimes["faiss"] = getattr(faiss, "__version__", PRESENT)
    except ImportError:
        runtimes["faiss"] = NOT_DETECTED

    # faster-whisper
    try:
        import faster_whisper
        runtimes["faster_whisper"] = getattr(faster_whisper, "__version__", PRESENT)
    except ImportError:
        runtimes["faster_whisper"] = NOT_DETECTED

    # openai-whisper
    try:
        import whisper
        runtimes["openai_whisper"] = getattr(whisper, "__version__", PRESENT)
    except ImportError:
        runtimes["openai_whisper"] = NOT_DETECTED

    return runtimes
