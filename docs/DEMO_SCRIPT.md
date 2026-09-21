# EdgeScholar Demo Script

## Competition Demo Walkthrough

This document describes the recommended live demonstration flow for the Qualcomm Snapdragon AI Lab Build & Present Challenge.

---

## Pre-Demo Checklist

- [ ] EdgeScholar installed and launching cleanly
- [ ] At least one demo document in `tests/fixtures/` (sample_operating_systems.txt)
- [ ] If Snapdragon hardware: QNN runtime installed, model downloaded
- [ ] If non-Snapdragon: llama.cpp + GGUF model, or acknowledge mock fallback
- [ ] Network disconnected (or airplane mode ready) for offline demo
- [ ] Benchmark results pre-populated (optional)

---

## Demo Flow (10-12 minutes)

### Scene 1: Problem Statement (1 min)

> "Students routinely upload lecture notes and textbooks to cloud AI services.
> This creates several problems: internet dependency, privacy concerns, latency,
> and recurring API costs.
> 
> What if the AI ran entirely on the student's own device?"

### Scene 2: Launch EdgeScholar (30 sec)

1. Launch: `python -m app.main`
2. Point to the Dashboard:
   - "Your Private AI Study Workspace"
   - System status showing local runtime
   - Privacy status: "AI Processing: Local"

### Scene 3: Import a Document (2 min)

1. Click **Library** → **Import Document**
2. Select `tests/fixtures/sample_operating_systems.txt`
3. Watch status: "Parsing document..." → "Generating embeddings..." → "Indexed locally"
4. Point to the document card: filename, page count, indexed status ✅

### Scene 4: Ask a Grounded Question (3 min)

1. Click **Chat**
2. Select the imported document from the dropdown
3. Ask: _"What is a process in operating systems?"_
4. Watch the response appear:
   - Answer with citations
   - "Sources: sample_operating_systems.txt — Page 1"
   - Runtime badge: `LOCAL • llama.cpp` (or `LOCAL • QNN/NPU` on Snapdragon)
5. Ask a follow-up: _"Explain CPU scheduling algorithms."_
6. **KEY DEMO MOMENT:** Ask something NOT in the document:
   - _"What is the capital of France?"_
   - Expected: "The document does not contain enough information to answer this."

### Scene 5: The Offline Demo (1 min)

> "Now let's prove this is genuinely offline."

1. Disconnect from internet / enable airplane mode
2. Ask another question in Chat
3. Response appears normally
4. Point out: **OFFLINE MODE** indicator (or show Settings → enable Offline Mode)

### Scene 6: Study Tools (2 min)

1. Navigate to **Study Tools**
2. Select the imported document
3. Click **Generate Summary** → show structured summary
4. Click **Generate Quiz** → show MCQ questions
5. Click **Generate Flashcards** → show front/back cards

### Scene 7: Performance Lab (1 min)

1. Navigate to **Performance**
2. Click **Run All Benchmarks**
3. Show real measured latency numbers
4. Explain what each metric means
5. Point out: "All measurements are real — no fabricated numbers"
6. If on Snapdragon: show NPU vs CPU comparison (if available)

### Scene 8: Privacy Screen (30 sec)

1. Navigate to **Settings**
2. Show Privacy section:
   - AI Processing: Local
   - Telemetry: Disabled
   - Cloud AI: Disabled
3. Show "Delete All Data" option

### Scene 9: Hardware Detection (30 sec)

1. Still in Settings, show Hardware tab
2. Point out:
   - Architecture: ARM64 (or x86_64 on dev machine)
   - QNN: VERIFIED (if Snapdragon) or NOT DETECTED (if dev)
   - NPU: Available / Not Detected
3. Emphasize: "We never claim NPU unless the runtime confirms it"

---

## Talking Points

### On Privacy
> "Every document you import stays on your device. We parse it locally, embed it locally,
> search it locally, and generate answers locally. Nothing touches a cloud server."

### On Offline
> "That's not just theoretical — we just proved it. The AI continued working with no internet."

### On Snapdragon
> "On Snapdragon-powered PCs, the QNN runtime can route inference through the NPU.
> EdgeScholar detects this automatically and shows you exactly what's being used."

### On Honest Benchmarks
> "Every number on the Performance screen is a real measurement from this machine.
> We don't fabricate throughput claims or TOPS figures."

---

## Fallback for Non-Snapdragon Hardware

If demoing on non-Snapdragon hardware (e.g., macOS, Intel PC):

- Acknowledge: "I'm on a development machine, not a Snapdragon device."
- Explain: "The architecture is Snapdragon-ready — QNN/NPU path activates automatically on target hardware."
- Show hardware panel displaying NOT DETECTED honestly.
- Use measured dev-machine performance as a baseline.

---

## Q&A Preparation

**Q: Is this faster than cloud AI?**
A: "On Snapdragon with NPU: potentially yes for short queries.
    On CPU-only dev hardware: slower throughput but zero latency variance and no network.
    We can't generalize — it depends on hardware, model size, and query length."

**Q: What models does it use?**
A: "Any GGUF-compatible model via llama.cpp (e.g., Llama 3.2 3B), or ONNX models via QNN.
    We ship with a mock fallback for development. Real models are user-downloaded."

**Q: Is this production ready?**
A: "This is a student project MVP demonstrating the on-device AI architecture.
    It's fully functional for personal study use."
