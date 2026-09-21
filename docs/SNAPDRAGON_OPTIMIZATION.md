# Snapdragon Optimization Guide

## Overview

This document explains EdgeScholar's Snapdragon optimization strategy, clearly separating:
- ✅ **VERIFIED** — Confirmed by runtime
- 🔵 **ARCHITECTURE PRESENT** — Code path exists, unverified on dev machine
- ⚠️ **ESTIMATED** — Theoretical based on Snapdragon documentation
- ❌ **NOT APPLICABLE** — Does not apply

---

## Target Hardware

**Production target:** Qualcomm Snapdragon X Elite / Snapdragon X Plus (and compatible series)  
**Form factor:** Snapdragon-powered Windows PCs (ARM64)  
**Example devices:** HP OmniBook X, HP EliteBook Ultra, Dell Inspiron 14 Plus

---

## Development Environment

| Property | Value |
|---|---|
| Current dev OS | macOS ARM64 (Apple Silicon) |
| Dev architecture | ARM64 (Apple M-series) |
| Snapdragon NPU available | ❌ Not applicable on macOS |
| QNN runtime available | ❌ Not available on macOS |
| llama.cpp (CPU) | 🔵 Available when installed |
| sentence-transformers | ✅ Verified on macOS dev |
| FAISS | ✅ Verified on macOS dev |

---

## Runtime Priority on Snapdragon Windows

```
Priority 1: QNN / NPU
   ↓ (if QNNExecutionProvider detected)
   ONNX Runtime + QNNExecutionProvider
   → Qualcomm NPU inference
   → Verified ONLY when runtime reports QNNExecutionProvider

Priority 2: ONNX Runtime CPU/GPU
   ↓ (if onnxruntime installed, no QNN)
   ONNX Runtime + CPUExecutionProvider (or CUDAExecutionProvider)
   → CPU/GPU inference

Priority 3: llama.cpp
   ↓ (if llama-cpp-python installed + .gguf model present)
   llama.cpp inference
   → CPU inference (ARM64 NEON optimized)
   → May use GPU layers if available

Priority 4: Mock Provider
   → Development fallback only
   → Never for production use
```

---

## QNN Integration Path

### Requirements
- Windows ARM64 (Snapdragon X series device)
- Qualcomm AI Stack / QNN SDK installed
- onnxruntime with QNN execution provider
- ONNX-format model compatible with Snapdragon

### Detection Code
```python
import onnxruntime as ort
providers = ort.get_available_providers()
qnn_available = "QNNExecutionProvider" in providers
```

EdgeScholar runs this check at startup. If `QNNExecutionProvider` is present:
- Provider factory selects `QNNProvider`
- UI displays: `LOCAL • QNN/NPU`
- Hardware panel shows: `QNN: VERIFIED`

If not present:
- Falls through to llama.cpp or ONNX CPU
- UI displays: `LOCAL • CPU` or `LOCAL • llama.cpp`
- Hardware panel shows: `QNN: NOT DETECTED`

### Compatible Models (from Qualcomm AI Hub)
- Llama 3.2 3B Instruct — Check AI Hub for Snapdragon X compatibility
- Whisper Base — Check AI Hub for ARM64 support
- All-MiniLM-L6-v2 (embedding) — ONNX compatible

> **Always verify model compatibility at:** https://aihub.qualcomm.com

---

## NPU Usage Claims Policy

EdgeScholar follows a strict policy on hardware claims:

| Statement | Allowed? |
|---|---|
| "NPU accelerated" | ✅ Only when QNNExecutionProvider confirmed |
| "CPU inference" | ✅ Always accurate |
| "Possible NPU" | ✅ When Snapdragon indicators present but QNN unconfirmed |
| "NPU active" | ❌ Never without verification |
| "X TOPS" | ❌ Never fabricated |
| "Faster than cloud" | ❌ Only if measured |

---

## Embedding Model on Snapdragon

The `all-MiniLM-L6-v2` embedding model via sentence-transformers:
- Runs on CPU on all platforms ✅
- On Snapdragon ARM64: ARM NEON SIMD acceleration applies automatically
- ONNX backend can be used for further optimization

Measured (development, macOS ARM64 — not Snapdragon):
- 3 texts: ~50-200ms (sentence-transformers, CPU)
- Snapdragon performance: not yet measured on target hardware

---

## Windows ARM64 Packaging

To package EdgeScholar for Snapdragon Windows:

1. Use a Windows ARM64 machine or cross-compile environment
2. Install PySide6 for Windows ARM64 (verify Qt6 ARM64 availability)
3. Install llama.cpp with ARM64 NEON flags
4. Bundle GGUF model with the installer
5. Optional: bundle QNN SDK and ONNX model for NPU path

```bash
# Windows ARM64 install (on-device)
pip install PySide6 PyMuPDF faiss-cpu sentence-transformers
pip install llama-cpp-python  # ARM64 build
pip install onnxruntime       # With QNN EP
```

---

## What We Do NOT Claim

- ❌ We do not claim specific TOPS numbers
- ❌ We do not claim NPU is always faster
- ❌ We do not claim "zero latency"
- ❌ We do not fabricate benchmark results
- ❌ We do not present dev-machine metrics as Snapdragon metrics
