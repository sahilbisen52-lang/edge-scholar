# Models Directory

This directory stores AI model files used by EdgeScholar.

## Important Notes

- **Do NOT commit model files to version control.** They are large binary files.
- This directory is listed in `.gitignore`.
- Models can be downloaded via the Model Manager (Settings → Model Manager).

## Supported Model Formats

- `.gguf` — GGUF format for llama.cpp
- `.onnx` — ONNX format for ONNX Runtime / QNN
- Sentence-transformers models are auto-downloaded from HuggingFace

## How to Add a Model

### llama.cpp (GGUF)

1. Download a GGUF file (e.g., from HuggingFace)
2. Place it in this directory (`models/`)
3. Restart EdgeScholar — it will be auto-detected

Example:
```
models/
└── Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

### ONNX Models

1. Download an ONNX model compatible with your device
2. Place it in this directory
3. Restart EdgeScholar

## Recommended Models

| Model | Size | Runtime | Purpose |
|-------|------|---------|---------|
| Llama 3.2 3B Instruct Q4 | ~2.1 GB | llama.cpp | Text generation |
| Whisper Base | ~74 MB | faster-whisper | Speech transcription |
| all-MiniLM-L6-v2 | ~90 MB | sentence-transformers | Embeddings (auto-download) |

## Qualcomm AI Hub Models

For Snapdragon hardware with QNN, refer to:
https://aihub.qualcomm.com

Always verify model compatibility with your specific Snapdragon chipset before downloading.
