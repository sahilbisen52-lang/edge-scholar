# Setup & Deployment Guide: Snapdragon-Powered Windows PCs (ARM64)

This document provides setup instructions for deploying EdgeScholar on **Snapdragon X Elite / Snapdragon X Plus** powered Windows PCs (such as the HP OmniBook X).

---

## 1. Prerequisites

- **Device:** Windows 11 on ARM64 (Snapdragon X Elite, Snapdragon X Plus, or 8cx Gen 3)
- **RAM:** Minimum 8 GB (16 GB or 32 GB recommended for 3B/7B models)
- **Python:** Python 3.11 or 3.12 (ARM64 Windows native build)
- **Compiler tools (optional for building llama.cpp):** Visual Studio 2022 Community with ARM64 C++ build tools

---

## 2. Installation Steps

### Step 1: Clone or Copy Repository
```cmd
git clone https://github.com/sahilbisen52-lang/edge-scholar.git
cd edge-scholar
```

### Step 2: Create ARM64 Virtual Environment
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Core Dependencies
```cmd
pip install -e ".[dev]"
```

### Step 4: Configure Qualcomm QNN / ONNX Runtime Execution Provider (NPU Path)

To leverage the Qualcomm Hexagon NPU:
```cmd
pip install onnxruntime
```
*Note:* Verify that `QNNExecutionProvider` is listed when checking available providers:
```cmd
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```
If `QNNExecutionProvider` is available, EdgeScholar will detect it automatically and report:
`LOCAL • ONNX + QNN/NPU (VERIFIED)`.

### Step 5: (Alternative) Install llama.cpp ARM64 Native (CPU / NEON Path)
For running GGUF models directly:
```cmd
pip install llama-cpp-python
```
Place your quantized GGUF model (e.g., `Llama-3.2-3B-Instruct-Q4_K_M.gguf`) in the `models/` directory.

### Step 6: Validate Environment
```cmd
python scripts\detect_environment.py
python scripts\validate_installation.py
```

### Step 7: Launch Application
```cmd
python -m app.main
```

---

## 3. Recommended Models for Snapdragon Windows

| Workload | Recommended Model | Format | Target Accelerator |
|---|---|---|---|
| Text Q&A & Quiz | Llama 3.2 3B Instruct | ONNX (Qualcomm AI Hub) / GGUF Q4 | Hexagon NPU / ARM64 CPU |
| Embeddings | all-MiniLM-L6-v2 | PyTorch / ONNX | CPU (NEON optimized) |
| Audio Notes | Whisper Base / Small | ONNX / INT8 | NPU / CPU |

Download Qualcomm AI Hub validated models from:  
https://aihub.qualcomm.com
