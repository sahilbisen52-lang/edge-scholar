# EdgeScholar

**Private On-Device AI Study Copilot**

> *"Your study material stays on your device. Always."*

---

## What is EdgeScholar?

EdgeScholar is a private, offline-first AI study assistant designed to run entirely on your local machine — with no cloud dependency for its core features.

Students can import PDFs and notes, ask grounded questions about them, generate summaries, create quizzes and flashcards, and transcribe lecture audio — all using local AI models with zero data leaving the device.

**Primary target hardware:** Snapdragon-powered HP PCs (e.g., HP OmniBook Ultra / HP OmniBook X, Windows 11 ARM64)  
**Hardware Accelerators:** Qualcomm Hexagon NPU (via Qualcomm QNN Execution Provider) & ARM64 CPU (NEON)  
**Development environment:** Any Python 3.11+ compatible machine (with automated cross-platform fallback)  
**Architecture:** Python + PySide6 native desktop application (Offline-First Studio)

---

## Why On-Device AI?

| Problem (Cloud AI) | EdgeScholar Solution |
|---|---|
| Internet dependency | Works fully offline |
| Data leaves device | All processing is local |
| Network latency | Instant local inference |
| Monthly API cost | One-time model download |
| Privacy concerns | Documents never transmitted |
| Cloud outages | No external dependencies |

---

## Core Features

### ✅ Document Library
- Import PDF and TXT documents
- Local parsing with PyMuPDF
- Page-aware text extraction
- SQLite-backed metadata store

### ✅ RAG Question Answering
- Semantic search using FAISS vector index
- Local embeddings (sentence-transformers)
- Grounded answers with page citations
- Prompt injection protection

### ✅ Study Tools
- Document summarization
- Quiz generation (MCQ, true/false, short answer)
- Flashcard generation
- Structured notes

### ✅ Audio Transcription
- Local speech-to-text with Whisper
- Microphone recording
- Audio file import
- Lecture summarization

### ✅ Performance Lab
- Real latency benchmarking (no fake numbers)
- Embedding, retrieval, LLM, and ASR benchmarks
- Export results as CSV/JSON
- Hardware-honest reporting

### ✅ Privacy Controls
- No telemetry by default
- No cloud AI (configurable)
- Offline mode toggle
- Complete data deletion

### ✅ Hardware Detection
- Conservative Snapdragon detection
- QNN runtime detection
- Never claims NPU unless QNNExecutionProvider is verified
- Clear VERIFIED / PRESENT / NOT DETECTED status

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EdgeScholar Desktop App                   │
│                    (PySide6 / Qt6)                          │
├────────────┬──────────────┬──────────┬──────────────────────┤
│  Documents │   Retrieval  │   RAG    │    Study Tools       │
│  PDF/TXT   │   Chunker    │ Pipeline │  Quiz/Flash/Notes    │
│  parsing   │   FAISS      │ Prompts  │  Summarizer          │
│  SQLite    │   Embeddings │ Citations│                      │
├────────────┴──────────────┴──────────┴──────────────────────┤
│                    AI Provider Layer                         │
│  QNN Provider → ONNX Provider → llama.cpp → Mock           │
│  (Snapdragon)   (CPU/GPU)        (CPU)      (Dev)          │
├─────────────────────────────────────────────────────────────┤
│              Hardware / Benchmark / Privacy                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone or download the project
cd edge-scholar

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Optional: for real LLM inference
pip install llama-cpp-python

# Optional: for audio transcription
pip install faster-whisper
```

### Run the App

```bash
python -m app.main
```

### Detect Environment

```bash
python scripts/detect_environment.py
```

### Validate Installation

```bash
python scripts/validate_installation.py
```

### Run Tests

```bash
pytest tests/ -v
```

---

## Using a Local LLM

To enable real LLM inference (instead of the mock provider):

1. Install llama-cpp-python:
   ```bash
   pip install llama-cpp-python
   ```

2. Download a GGUF model file (e.g., Llama 3.2 3B Instruct Q4):
   - Source: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
   - Place the `.gguf` file in the `models/` directory

3. Restart EdgeScholar — the app auto-detects GGUF files.

---

## Snapdragon / QNN Support

On Snapdragon-powered Windows PCs with QNN runtime installed:

1. Install `onnxruntime` with QNN support:
   ```bash
   pip install onnxruntime
   ```

2. The app automatically detects `QNNExecutionProvider` and selects the QNN path.

3. Compatible models from Qualcomm AI Hub can be placed in `models/` as ONNX files.

See [`docs/SNAPDRAGON_OPTIMIZATION.md`](docs/SNAPDRAGON_OPTIMIZATION.md) for full details.

> **Important:** EdgeScholar only reports NPU acceleration as VERIFIED when `QNNExecutionProvider` 
> is confirmed by ONNX Runtime. We never fabricate hardware claims.

---

## Project Structure

```
edge-scholar/
├── app/                    # Application source
│   ├── main.py            # Entry point
│   ├── config/            # Settings and constants
│   ├── core/              # App context, events, logging, errors
│   ├── ui/                # PySide6 views and components
│   ├── documents/         # PDF/TXT parsing and storage
│   ├── retrieval/         # Chunking, embeddings, FAISS
│   ├── ai/                # Provider abstraction layer
│   ├── rag/               # RAG pipeline and citations
│   ├── study/             # Study tools (quiz, flashcards, etc.)
│   ├── audio/             # Recording and transcription
│   ├── hardware/          # System detection and diagnostics
│   ├── benchmark/         # Benchmark runner and storage
│   ├── privacy/           # Local storage, deletion, network guard
│   └── utils/             # Shared utilities
├── tests/                 # Unit and integration tests
├── models/                # AI model files (not committed)
├── data/                  # Runtime data (not committed)
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

---

## Documentation & Presentation Suite

- [Submission Notes & Executive Summary](docs/SUBMISSION_NOTES.md)
- [Competition Pitch Deck (10 Slides)](docs/PITCH_DECK.md)
- [3-Minute Video Presentation Script](docs/VIDEO_SCRIPT_3MIN.md)
- [Architecture & System Design](docs/ARCHITECTURE.md)
- [Snapdragon Optimization Guide](docs/SNAPDRAGON_OPTIMIZATION.md)
- [Setup Guide for Snapdragon Windows PCs](docs/SETUP_WINDOWS_ARM64.md)
- [Threat Model & Security](docs/THREAT_MODEL.md)
- [Privacy Architecture](docs/PRIVACY.md)
- [Benchmark Protocol](docs/BENCHMARK_PROTOCOL.md)
- [Live Demo Script](docs/DEMO_SCRIPT.md)

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Competition Context

This project is an **independent student project** submitted to the Qualcomm Snapdragon AI Lab Build & Present Challenge.

- EdgeScholar is not affiliated with, endorsed by, or sponsored by Qualcomm or HP.
- Qualcomm, Snapdragon, and QNN are trademarks of Qualcomm Technologies, Inc.
- All benchmark results presented are measured on actual hardware — no fabrication.
