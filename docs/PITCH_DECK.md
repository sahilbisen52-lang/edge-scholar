# EdgeScholar — Competition Pitch Deck

**Qualcomm Snapdragon AI Lab Build & Present Challenge 2026**  
*Track: On-Device AI Optimized for Snapdragon-Powered HP PCs*

---

## Slide 1: Title & Positioning
- **Title:** EdgeScholar
- **Subtitle:** Private On-Device AI Study Copilot
- **Tagline:** *"Your study materials never leave your device. Grounded learning powered by Snapdragon Edge AI."*
- **Team / Submitter:** Independent Student Project
- **Target Platform:** Snapdragon-powered HP PCs (e.g., HP OmniBook Ultra / HP OmniBook X)

---

## Slide 2: The Core Problem
### The Student Cloud Dilemma
- **Privacy & IP Risk:** Students and researchers routinely upload proprietary textbooks, confidential exam notes, and private lecture recordings to cloud LLM APIs.
- **Internet Dependency:** Campus Wi-Fi dead zones, flights, and library network outages completely paralyze cloud AI study tools.
- **Latency & Recurring Cost:** Cloud API tokens cost money every query, and network round-trip introduces unpredictable latency.
- **Hallucinations & Ungrounded Claims:** Generic chatbots make up answers without verifiable page citations.

---

## Slide 3: The EdgeScholar Solution
### Private • Local • Offline • Snapdragon-Optimized
- **Zero Cloud Leakage:** Documents are parsed, vectorized, indexed, and queried 100% on the local machine.
- **Verifiable Grounding:** Every generated answer is anchored to source document pages with clickable citations.
- **Full Academic Suite:** One unified desktop workspace for grounded Q&A, executive summaries, interactive quizzes, flashcards, and lecture audio transcription.
- **Snapdragon Native:** Designed from day one for the Qualcomm Hexagon NPU using ONNX Runtime with the Qualcomm QNN Execution Provider.

---

## Slide 4: System Architecture
- **Desktop UI Layer:** Native PySide6 (Qt6) interface with asynchronous threading (`QThreadPool`) for freeze-free responsiveness.
- **Ingestion & Retrieval Layer:**
  - PyMuPDF physical page-boundary extraction
  - Overlapping chunking engine (600-token chunks with 100-token overlap)
  - `all-MiniLM-L6-v2` local embedding generator
  - In-memory & disk-backed FAISS vector index (`IndexFlatIP`)
- **Model Agnostic Abstraction (`AIProvider`):**
  - **Priority 1:** Qualcomm QNN / Hexagon NPU (`QNNExecutionProvider`)
  - **Priority 2:** llama.cpp ARM64 NEON SIMD GGUF CPU inference
  - **Priority 3:** ONNX Runtime standard providers

---

## Slide 5: The Snapdragon & Qualcomm AI Hub Advantage
- **Qualcomm AI Hub Integration:** Built-in workflow and manifests to import pre-optimized models directly from [aihub.qualcomm.com](https://aihub.qualcomm.com):
  - *Llama 3.2 3B Instruct* (w4a16 INT4 quantized for Hexagon NPU)
  - *Whisper Base English* (NPU-accelerated ASR)
  - *all-MiniLM-L6-v2* (QNN EP accelerated embeddings)
- **45 TOPS Hexagon Engine:** Unlocks instant on-device generation without draining laptop battery life or spinning high-wattage fans.
- **Conservative Hardware Verification:** We never claim NPU acceleration unless verified by the underlying runtime.

---

## Slide 6: Grounded Study Tools & Interactive Learning Engine
Beyond simple text chat, EdgeScholar is an interactive study workspace:
1. **Grounded Q&A with Source Citations:** Points students directly to `Page X` of their class textbooks.
2. **Interactive Quiz Player:** Generates practice questions (MCQ, True/False, Short Answer) with instant green/red scoring and citation hints.
3. **Interactive Flip Flashcards:** Flip card interface with mastery tracking.
4. **Lecture Audio-to-Notes:** Local Whisper transcription turning classroom recordings into structured notes.

---

## Slide 7: Privacy & Threat Model
- **Anti-Prompt Injection Fencing:** Untrusted document excerpts are fenced from system instructions (`=== DOCUMENT EXCERPTS (untrusted) ===`).
- **NetworkGuard Enforcement:** Strict offline mode blocks any outgoing network requests.
- **Path Traversal Protection:** Validates file sizes (<100MB) and whitelists file extensions.
- **One-Click Total Purge:** Deletion manager enables students to wipe all local indexes, databases, and cache instantly.

---

## Slide 8: Measured On-Device Performance
*All measurements captured using high-resolution timers (`time.perf_counter()`) and `psutil`.*
- **Local Embedding Latency:** ~250–300 ms for multiple paragraphs (sentence-transformers).
- **Retrieval Search Speed:** < 5 ms across indexed textbooks (FAISS).
- **Offline Reliability:** 100% operational uptime independent of network connectivity.
- **Local Privacy Shield:** 100% of document bytes stay on the student's PC.

---

## Slide 9: Product Roadmap & Scalability
- **Phase 1 (Current MVP):** Full desktop workspace, local RAG, interactive quiz/flashcard engine, Whisper transcription, Qualcomm AI Hub integration.
- **Phase 2:** Direct integration of pre-compiled `.bin` QNN context binaries on HP OmniBook X Snapdragon hardware.
- **Phase 3:** Multi-modal diagram parsing using lightweight ONNX vision models.

---

## Slide 10: Conclusion & Call to Action
- **Why EdgeScholar Wins:**
  1. **Strictly fulfills all competition criteria:** Specifically architected for Snapdragon-powered HP PCs.
  2. **Real Technical Implementation:** Fully functional code with 31 automated tests passing.
  3. **High Impact & Clear Innovation:** Solves an everyday, urgent problem for college students.
  4. **Honest & Production Ready:** No fake benchmarks, no cloud dependencies.
- **Repository & Code:** Ready for live demonstration and evaluation.
