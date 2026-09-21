# Qualcomm Snapdragon AI Lab Build & Present Challenge — Submission Notes

## 1. Project Identification
- **Project Name:** EdgeScholar
- **Subtitle:** Private On-Device AI Study Copilot
- **Submission Type:** Independent Student Project
- **Challenge:** Qualcomm Snapdragon AI Lab Build & Present Challenge
- **Core Positioning:** PRIVATE • LOCAL • OFFLINE • EDGE AI • SNAPDRAGON OPTIMIZATION

---

## 2. Executive Summary

EdgeScholar solves the growing student dilemma of uploading sensitive class notes, proprietary textbooks, and private lecture recordings to cloud AI services. By hosting document parsing, vector indexing, retrieval-augmented generation (RAG), and speech-to-text inference entirely on the local device, students benefit from:
1. **Zero Cloud Leakage:** Documents never leave the computer.
2. **Offline Resilience:** Complete functionality during flights, library dead zones, or campus network outages.
3. **Hardware Acceleration:** Native architectural pathway for Qualcomm Hexagon NPU execution via QNN and ONNX Runtime.
4. **Honest Benchmarking:** Live high-resolution timers measuring actual latency without fabricated performance claims.

---

## 3. Evaluation Criteria Alignment

### 3.1 Technical Implementation
- **Modular Desktop Architecture:** Written in modern Python 3.11+ using PySide6 (Qt6) native desktop interface with responsive worker threading.
- **Full RAG Pipeline:** PyMuPDF text extraction preserving physical page boundaries, deterministic chunking, local sentence-transformers embeddings, and local FAISS vector index.
- **Provider Abstraction:** Dynamic switching across Qualcomm QNN, ONNX Runtime, llama.cpp, and development mock providers.
- **Local Speech-to-Text:** Local Whisper ASR integration with timestamped audio transcript generation.

### 3.2 Application Use Case & Innovation
- Dedicated academic workflow tailored to students:
  - Factual question answering with verifiable page citations.
  - Automatic executive summaries and exam revision points.
  - Multi-format quiz generation (MCQ, True/False, Short Answer).
  - Revision flashcards with front/back study prompts.
  - Lecture audio conversion to structured revision notes.
- **Anti-Prompt Injection Fencing:** Untrusted document excerpts are quarantined from system instructions.

### 3.3 Deployment & Accessibility
- Runs across platforms with automated hardware diagnostics.
- Clear step-by-step ARM64 Windows deployment documentation targeting HP OmniBook X and Snapdragon X series laptops.
- Offline mode toggle with visual badge and complete local data purging controls.

### 3.4 Presentation & Documentation
- Comprehensive documentation suite:
  - `ARCHITECTURE.md` — Detailed system and component diagrams
  - `SNAPDRAGON_OPTIMIZATION.md` — Honest categorization of verified vs unverified capabilities
  - `BENCHMARK_PROTOCOL.md` — Transparent testing methodology
  - `PRIVACY.md` & `THREAT_MODEL.md` — Complete privacy & security analysis
  - `DEMO_SCRIPT.md` — Live presentation walkthrough
  - `SETUP_WINDOWS_ARM64.md` — Native Windows on ARM instructions

---

## 4. Hardware Integrity & Attribution Notice

EdgeScholar strictly adheres to competition integrity guidelines:
- **No Fabricated Benchmarks:** All benchmark metrics are measured using high-resolution hardware timers (`time.perf_counter()`) and `psutil`.
- **Honest Hardware Reporting:** The application uses conservative status flags (`VERIFIED`, `PRESENT`, `NOT_DETECTED`, `UNKNOWN`). NPU acceleration is reported as `VERIFIED` only when the underlying runtime (`QNNExecutionProvider`) explicitly confirms execution.
- **Non-Endorsement Disclaimer:** EdgeScholar is an independent student project and is not officially endorsed or sponsored by Qualcomm Technologies, Inc. or HP Inc.
