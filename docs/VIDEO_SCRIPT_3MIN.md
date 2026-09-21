# 3-Minute Video Presentation Script & Demo Guide

**Competition:** Qualcomm Snapdragon AI Lab Build & Present Challenge 2026  
**Target Duration:** Exactly 3 minutes (180 seconds)  
**Tone:** Confident, professional, technical, student-innovator

---

## Video Timeline Breakdown

| Time | Section | Screen Action | Voice-Over / Speaking Points |
|---|---|---|---|
| **0:00 – 0:25** (25s) | **The Hook & Problem** | Camera on speaker, then transition to browser showing cloud AI outage / privacy warning. | *"Every day, millions of students upload their private lecture notes, unpublished research, and textbooks to cloud AI services. But what happens when campus Wi-Fi drops, or you're studying on a flight? More importantly, why should students compromise their privacy and pay recurring subscription fees just to study? Welcome to **EdgeScholar** — a private, offline-first on-device AI study copilot designed for Snapdragon-powered Windows PCs."* |
| **0:25 – 0:50** (25s) | **App Launch & Hardware Diagnostics** | Launch `python -m app.main`. Show the **Dashboard** and **Performance Lab** screen. | *"EdgeScholar is a native desktop application built with Python and Qt6. Notice our hardware detection engine: it inspects the system architecture and runtime providers conservatively. On Snapdragon-powered HP PCs, our architecture routes inference directly through the Qualcomm Hexagon NPU using the Qualcomm QNN Execution Provider. We never fabricate benchmark metrics — every number you see is measured live on actual hardware."* |
| **0:50 – 1:30** (40s) | **Live Document Import & Grounded RAG** | Click **Library** → Import `sample_operating_systems.txt`. Show "Indexed locally". Open **Chat**. Ask: *"What is CPU scheduling?"* | *"Let's import an Operating Systems lecture note. Notice that processing, chunking, and FAISS vector indexing happen 100% locally. Now in Chat, let's ask a question: 'What is CPU scheduling?'. In real-time, EdgeScholar retrieves the most relevant semantic chunks, feeds them into our local model, and returns a grounded answer with verifiable source citations pointing directly to the exact page. If we ask something outside the document, like 'What is the capital of France?', EdgeScholar refuses to hallucinate because of our strict prompt fencing."* |
| **1:30 – 1:55** (25s) | **The Airplane Mode Test (Key Demo Moment)** | Disconnect Wi-Fi / turn on Airplane mode. Ask another question in Chat: *"Explain Round Robin."* | *"Now for the defining test: let's turn on Airplane mode and completely disconnect from the internet. Watch this: we ask another question about Round Robin scheduling. The local embeddings and inference continue running seamlessly without sending a single byte across the internet. EdgeScholar delivers true offline independence."* |
| **1:55 – 2:25** (30s) | **Interactive Study Suite & Audio Notes** | Click **Study Tools** → Click **Interactive Quiz** → Click an option (it turns green, score updates). Click **Flashcards** → Click Flip. Click **Audio Notes**. | *"Beyond chat, EdgeScholar is an interactive learning workspace. In Study Tools, students get an Interactive Quiz Player with instant scoring, feedback, and citation hints. The Flashcard deck lets students flip terms and track mastery. And in Audio Notes, our local Whisper integration transcribes classroom lectures directly from the microphone into structured revision notes."* |
| **2:25 – 2:45** (20s) | **Qualcomm AI Hub Integration & Performance** | Open **Settings** → Show Model Manifest with Qualcomm AI Hub models. Show Performance Lab with CSV export. | *"We built EdgeScholar with Qualcomm AI Hub as a first-class citizen. Our model manager integrates pre-optimized models like Llama 3.2 3B and Whisper Base formatted for the Snapdragon NPU. In our Performance Lab, students and developers can profile latency, tokens per second, and memory consumption with one click."* |
| **2:45 – 3:00** (15s) | **Closing & Impact** | Return to speaker / final slide showing EdgeScholar logo and tagline. | *"EdgeScholar proves why on-device AI matters: uncompromised privacy, zero subscription fees, offline resilience, and Snapdragon NPU acceleration. Thank you, Qualcomm and HP, for empowering the next generation of on-device AI innovation."* |

---

## Screen Recording Tips for High Scores
1. **Screen Resolution:** Record at 1080p (1920x1080) at 60 FPS for fluid UI animations.
2. **Audio:** Use a clean, crisp USB microphone with noise cancellation.
3. **Cursor:** Enable cursor highlighting so judges can follow clicks easily.
4. **Airplane Mode Visual:** Ensure the Wi-Fi disconnect icon is visibly shown in the system tray during the offline demonstration moment.
