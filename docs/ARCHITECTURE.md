# EdgeScholar — Technical Architecture

## 1. System Overview

**EdgeScholar** is an offline-first, private on-device study copilot designed for Snapdragon-powered Windows PCs. It provides grounded PDF question answering, document summarization, interactive quiz & flashcard generation, and audio lecture transcription without relying on cloud services.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        EdgeScholar Presentation Layer                  │
│                     (PySide6 / Qt6 Native Desktop GUI)                 │
├──────────────┬──────────────┬──────────────┬─────────────┬─────────────┤
│  Dashboard   │   Library    │  Chat & RAG  │ Study Tools │ Audio Notes │
│ System Stats │ Documents DB │ Citations UI │ Quiz/Notes  │ Transcription│
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬──────┴──────┬──────┘
       │              │              │              │             │
┌──────▼──────────────▼──────────────▼──────────────▼─────────────▼──────┐
│                        Application Services Layer                      │
├─────────────────────┬──────────────────────┬───────────────────────────┤
│   Documents Module  │   Retrieval Module   │        RAG Pipeline       │
│ • PyMuPDF Parsing   │ • Text Chunker       │ • Grounded Prompting      │
│ • Page Metadata     │ • FAISS Vector Index │ • Anti-Prompt Injection   │
│ • SQLite Store      │ • MiniLM Embeddings  │ • Page Citation Formatter │
├─────────────────────┴──────────────────────┴───────────────────────────┤
│                          Study & Audio Services                        │
│ • Summarizer • QuizGenerator • FlashcardGenerator • NotesGenerator      │
│ • AudioRecorder (16kHz WAV) • WhisperProvider (ASR)                    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                    Hardware-Aware AI Provider Layer                    │
│                        (ProviderFactory Dispatch)                      │
├───────────────────────┬────────────────────────┬───────────────────────┤
│     Qualcomm QNN      │     ONNX Runtime       │       llama.cpp       │
│ • QNNExecutionProvider│ • CPU/GPU/NPU Fallback │ • Local CPU / NEON    │
│ • Hexagon NPU Target  │ • Cross-Platform       │ • GGUF Model Loader   │
│ (Snapdragon Windows)  │ (Linux/macOS/Windows)  │ (Universal Fallback)  │
└───────────────────────┴────────────────────────┴───────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                  Hardware Detection & Platform Diagnostics             │
│   • CPU Architecture • NPU Reporting • psutil Metrics • NetworkGuard   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Document Processing (`app/documents/`)
- **Parsers:** `PdfParser` (utilizing PyMuPDF/`fitz`) extracts selectable text while preserving physical page boundaries. If text density falls below a minimum threshold, it tags the page as potentially scanned. `TextParser` supports `.txt` and `.md` files by chunking into virtual pages of 3,000 characters.
- **Store:** `DocumentStore` uses SQLite to record document metadata (filename, page count, SHA-256 fingerprint, timestamps) and page contents.

### 2.2 Local Retrieval & Indexing (`app/retrieval/`)
- **Chunker:** `Chunker` creates overlapping token-estimated chunks (default: 600 tokens with 100-token overlap). Every chunk retains its originating `document_id` and physical `page_number`. Deterministic hashes prevent duplicate vectors.
- **Embeddings:** `LocalEmbeddings` wraps `sentence-transformers` (`all-MiniLM-L6-v2`) generating 384-dimensional normalized vectors locally.
- **Vector Index:** `VectorStore` manages a local FAISS `IndexFlatIP` index with cosine similarity over normalized embeddings. Supports atomic document deletion and index persistence on disk.

### 2.3 Grounded RAG Pipeline (`app/rag/`)
- Formulates strict prompts restricting LLM generation to retrieved excerpts only.
- Injects explicit prompt boundary fences:
  `=== DOCUMENT EXCERPTS (untrusted) ===` to mitigate indirect prompt injection attacks.
- `CitationBuilder` matches retrieved chunks to page numbers and surfaces clickable citations with excerpts and confidence statuses.

### 2.4 AI Provider Abstraction (`app/ai/`)
EdgeScholar avoids vendor lock-in through the abstract `AIProvider` base class:
- `QNNProvider`: Snapdragon NPU runtime via ONNX Runtime `QNNExecutionProvider`. Only reports NPU acceleration when the runtime confirms execution.
- `LlamaCppProvider`: CPU inference with ARM64 NEON SIMD optimizations supporting standard GGUF quantizations.
- `ONNXProvider`: Standard ONNX runtime fallback.
- `MockProvider`: Standalone development and automated UI testing provider requiring zero external models.
- `ProviderFactory`: Inspects runtime environment at startup, determines highest-priority available accelerator, and provisions the provider.

### 2.5 Audio Transcription (`app/audio/`)
- `AudioRecorder`: Captures 16kHz mono audio via `sounddevice` into temporary local WAV files.
- `WhisperProvider`: Transcribes speech using local Whisper models (faster-whisper/openai-whisper) with timestamped segments.
- Transcripts feed directly into `Summarizer` and `NotesGenerator` to produce lecture notes.

### 2.6 Hardware & Benchmarking (`app/hardware/`, `app/benchmark/`)
- High-precision benchmarking using `time.perf_counter()` and `psutil` memory tracking.
- Measures cold start, warm start, TTFT (Time to First Token), tokens/second, and embedding throughput.
- Persists all benchmarks in structured JSON and exports CSV/JSON.

---

## 3. Storage Hierarchy

```
<LocalAppData>/EdgeScholar/data/  (Windows)
~/Library/Application Support/EdgeScholar/data/ (macOS)
~/.local/share/EdgeScholar/data/ (Linux)
│
├── edge_scholar.db     # SQLite document, page, and chunk metadata
├── indexes/            # FAISS vector index & metadata pickle
├── documents/          # Sandboxed copies of imported study files
├── transcripts/        # Generated lecture audio and text transcripts
├── benchmarks/         # Benchmark results history
├── exports/            # Student exports (notes, quizzes, flashcards)
└── logs/               # Privacy-preserving operational logs
```
