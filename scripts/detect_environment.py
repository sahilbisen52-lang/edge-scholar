"""
EdgeScholar — Environment Detection Script

Run with: python scripts/detect_environment.py

Displays a comprehensive report of the current environment,
hardware detection results, and AI runtime availability.
Clearly separates verified from unverified capabilities.
"""
from __future__ import annotations

import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.hardware.system_detector import detect_system, VERIFIED, PRESENT, NOT_DETECTED, UNKNOWN


def separator(char: str = "─", width: int = 60) -> str:
    return char * width


def main() -> None:
    print(separator("═"))
    print("  EdgeScholar — Environment Detection")
    print(separator("═"))

    info = detect_system()

    print("\n📊 SYSTEM INFORMATION")
    print(separator())
    print(f"  OS:               {info.get('os')} {info.get('os_release')}")
    print(f"  Architecture:     {info.get('architecture')}")
    print(f"  Processor:        {info.get('processor')}")
    print(f"  RAM:              {info.get('ram_gb')} GB ({info.get('ram_available_gb')} GB available)")
    print(f"  CPU cores:        {info.get('cpu_cores_logical')}")
    print(f"  Python:           {info.get('python_version')}")

    print("\n🔍 SNAPDRAGON DETECTION")
    print(separator())
    snap = info.get("snapdragon_status", NOT_DETECTED)
    indicators = info.get("snapdragon_indicators", [])
    qnn = info.get("qnn_status", NOT_DETECTED)
    npu = info.get("npu_status", NOT_DETECTED)

    print(f"  Snapdragon:       {snap}")
    if indicators:
        for ind in indicators:
            print(f"    ✓ {ind}")
    else:
        print("    (no Snapdragon indicators detected)")
    print(f"  QNN Runtime:      {qnn}")
    print(f"  NPU:              {npu}")
    print()
    if snap == NOT_DETECTED:
        print("  ℹ️  Running on non-Snapdragon hardware.")
        print("     Snapdragon features (QNN, NPU) will use development fallbacks.")
        print("     On Snapdragon Windows PCs, QNN and NPU paths will activate automatically.")

    print("\n🛠️  RUNTIME AVAILABILITY")
    print(separator())
    runtimes = info.get("runtimes", {})
    runtime_display = [
        ("sentence-transformers", "sentence_transformers", "Local embeddings"),
        ("PyMuPDF",               "pymupdf",               "PDF parsing"),
        ("FAISS",                 "faiss",                 "Vector index"),
        ("ONNX Runtime",          "onnxruntime",           "ONNX inference"),
        ("llama.cpp",             "llama_cpp",             "LLM inference"),
        ("faster-whisper",        "faster_whisper",        "Fast ASR"),
        ("openai-whisper",        "openai_whisper",        "ASR fallback"),
    ]
    for display_name, key, description in runtime_display:
        value = runtimes.get(key, NOT_DETECTED)
        status = "✅" if value != NOT_DETECTED else "❌"
        ver = f" ({value})" if value not in (NOT_DETECTED, PRESENT) else ""
        print(f"  {status} {display_name:<22} {description}{ver}")

    onnx_providers = runtimes.get("onnx_providers", "")
    if onnx_providers:
        print(f"\n     ONNX Providers: {onnx_providers}")
        if "QNNExecutionProvider" in onnx_providers:
            print("     ✅ QNN Execution Provider VERIFIED — NPU acceleration available")
        else:
            print("     ℹ️  QNN Execution Provider not in available providers")

    print("\n📋 INFERENCE PATH SELECTION")
    print(separator())
    if qnn == VERIFIED:
        print("  Recommended: QNN / NPU (Qualcomm AI Hub compatible)")
    elif runtimes.get("llama_cpp", NOT_DETECTED) != NOT_DETECTED:
        print("  Recommended: llama.cpp (CPU)")
    elif runtimes.get("onnxruntime", NOT_DETECTED) != NOT_DETECTED:
        print("  Recommended: ONNX Runtime (CPU)")
    else:
        print("  Recommended: Mock Provider (development fallback)")
        print("  To enable real LLM inference, install llama-cpp-python and download a GGUF model")

    print("\n⚠️  CAPABILITY STATUS KEY")
    print(separator())
    print("  VERIFIED    = Confirmed by runtime reporting")
    print("  PRESENT     = Detected by indicator (not confirmed)")
    print("  NOT DETECTED= Not found on this device")
    print("  UNKNOWN     = Could not determine")
    print()
    print("  Never assume PRESENT = VERIFIED for NPU/hardware claims.")

    print(separator("═"))
    print("  Detection complete.")
    print(separator("═"))


if __name__ == "__main__":
    main()
