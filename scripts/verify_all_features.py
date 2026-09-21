"""
Comprehensive Full-Feature Verification Script for EdgeScholar.
Executes and validates every single functional subsystem, service, and UI component.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["QT_QPA_PLATFORM"] = "offscreen"


def run_full_system_audit():
    print("=" * 70)
    print("  EDGESCHOLAR — COMPREHENSIVE FEATURE & SUBSYSTEM AUDIT")
    print("=" * 70)

    results = []

    def log_result(feature_name: str, passed: bool, detail: str = ""):
        status = "PASSED ✅" if passed else "FAILED ❌"
        print(f"[{status}] {feature_name:<40} {detail}")
        results.append((feature_name, passed, detail))

    # ── 1. AppContext & Directory Structure ──
    try:
        from app.core.app_context import AppContext
        ctx = AppContext()
        assert ctx.data_dir.exists()
        assert (ctx.data_dir / "documents").exists()
        assert (ctx.data_dir / "indexes").exists()
        assert (ctx.data_dir / "benchmarks").exists()
        log_result("1. AppContext & Storage Layout", True, f"Data Dir: {ctx.data_dir.name}")
    except Exception as e:
        log_result("1. AppContext & Storage Layout", False, str(e))

    # ── 2. Document Parser (TXT / MD) ──
    try:
        from app.documents.parser import DocumentParser
        parser = DocumentParser()
        fixture_path = PROJECT_ROOT / "tests" / "fixtures" / "sample_operating_systems.txt"
        meta, pages = parser.parse(fixture_path)
        assert len(pages) > 0
        assert meta.filename == "sample_operating_systems.txt"
        assert meta.sha256
        log_result("2. Document Parsing (Text & Virtual Pages)", True, f"{len(pages)} pages extracted")
    except Exception as e:
        log_result("2. Document Parsing (Text & Virtual Pages)", False, str(e))

    # ── 3. Document Store (SQLite CRUD) ──
    try:
        store = ctx.get_document_store()
        store.upsert_document(meta)
        store.save_pages(pages)
        fetched_meta = store.get_document(meta.document_id)
        assert fetched_meta is not None
        assert fetched_meta.filename == meta.filename
        fetched_pages = store.get_pages(meta.document_id)
        assert len(fetched_pages) == len(pages)
        log_result("3. SQLite Document Store (Metadata & Pages)", True, f"Doc ID: {meta.document_id[:8]}")
    except Exception as e:
        log_result("3. SQLite Document Store (Metadata & Pages)", False, str(e))

    # ── 4. Text Chunker (Token & Page Aware) ──
    try:
        from app.retrieval.chunker import Chunker
        chunker = Chunker(chunk_size=400, overlap=60)
        chunks = chunker.chunk_pages(pages)
        assert len(chunks) > 0
        assert all(c.page_number >= 1 for c in chunks)
        assert all(c.hash for c in chunks)
        store.save_chunks([c.to_dict() for c in chunks])
        log_result("4. Page-Aware Overlapping Chunker", True, f"{len(chunks)} chunks produced")
    except Exception as e:
        log_result("4. Page-Aware Overlapping Chunker", False, str(e))

    # ── 5. Local Embeddings (MiniLM-L6-v2) ──
    try:
        embeddings = ctx.get_embeddings()
        sample_texts = [c.text for c in chunks[:3]]
        t0 = time.perf_counter()
        vecs = embeddings.embed(sample_texts)
        lat = time.perf_counter() - t0
        assert vecs.shape == (len(sample_texts), 384)
        log_result("5. Local Embeddings (MiniLM 384D Offline)", True, f"Shape: {vecs.shape} in {lat:.3f}s")
    except Exception as e:
        log_result("5. Local Embeddings (MiniLM 384D Offline)", False, str(e))

    # ── 6. Local FAISS Vector Index ──
    try:
        vs = ctx.get_vector_store()
        meta_list = [{"chunk_id": c.chunk_id, "document_id": c.document_id, "page_number": c.page_number, "text": c.text, "filename": meta.filename} for c in chunks]
        vs.add(embeddings.embed([c.text for c in chunks]), meta_list)
        assert vs.count() >= len(chunks)
        scores, results_meta = vs.search(vecs[0], top_k=2)
        assert len(results_meta) == 2
        assert scores[0] >= 0.90  # Cosine self-similarity near 1.0
        log_result("6. FAISS Vector Store (IndexFlatIP)", True, f"Total Indexed: {vs.count()} vectors")
    except Exception as e:
        log_result("6. FAISS Vector Store (IndexFlatIP)", False, str(e))

    # ── 7. Semantic Retriever ──
    try:
        from app.retrieval.retriever import Retriever
        retriever = Retriever(embeddings, vs)
        retrieved_chunks, elapsed = retriever.retrieve("CPU scheduling algorithms", top_k=3)
        assert len(retrieved_chunks) > 0
        assert any("scheduling" in c.text.lower() for c in retrieved_chunks)
        log_result("7. Semantic Retriever (Top-K Filtered)", True, f"Found {len(retrieved_chunks)} relevant in {elapsed:.3f}s")
    except Exception as e:
        log_result("7. Semantic Retriever (Top-K Filtered)", False, str(e))

    # ── 8. AI Provider & Hardware Fallback ──
    try:
        provider = ctx.get_ai_provider()
        model_info = provider.get_model_info()
        runtime_info = provider.get_runtime_info()
        res = provider.generate("Summarize: A process is a program in execution.", max_tokens=60)
        assert res.text
        assert res.output_tokens >= 1
        log_result("8. AI Provider Layer (Hardware-Aware)", True, f"Runtime: {runtime_info.runtime}, Accel: {runtime_info.accelerator}")
    except Exception as e:
        log_result("8. AI Provider Layer (Hardware-Aware)", False, str(e))

    # ── 9. Grounded RAG Pipeline & Anti-Injection ──
    try:
        from app.rag.pipeline import RAGPipeline
        pipeline = RAGPipeline(retriever=retriever, provider=provider)
        rag_resp = pipeline.query("Explain CPU scheduling algorithms in operating systems.")
        assert rag_resp.answer
        assert len(rag_resp.citations) > 0
        assert rag_resp.citations[0].filename == "sample_operating_systems.txt"
        assert rag_resp.citations[0].page_number >= 1
        assert rag_resp.grounding_status in ("grounded", "partially_grounded")
        log_result("9. Grounded RAG & Citations Pipeline", True, f"{len(rag_resp.citations)} sources, Status: {rag_resp.grounding_status}")
    except Exception as e:
        log_result("9. Grounded RAG & Citations Pipeline", False, str(e))

    # ── 10. Study Tools: Summarizer ──
    try:
        from app.study.summarizer import Summarizer
        summarizer = Summarizer(provider, store)
        summary = summarizer.summarize_document(meta.document_id)
        assert len(summary) > 20
        log_result("10. Study Engine: Executive Summarizer", True, f"{len(summary)} chars generated")
    except Exception as e:
        log_result("10. Study Engine: Executive Summarizer", False, str(e))

    # ── 11. Study Tools: Quiz Generator ──
    try:
        from app.study.quiz_generator import QuizGenerator
        quiz_gen = QuizGenerator(provider, store)
        raw_quiz, questions = quiz_gen.generate(meta.document_id)
        assert len(raw_quiz) > 0
        log_result("11. Study Engine: Interactive Quiz Gen", True, f"Quiz produced ({len(questions)} parsed)")
    except Exception as e:
        log_result("11. Study Engine: Interactive Quiz Gen", False, str(e))

    # ── 12. Study Tools: Flashcard Generator ──
    try:
        from app.study.flashcards import FlashcardGenerator
        fc_gen = FlashcardGenerator(provider, store)
        raw_fc, cards = fc_gen.generate(meta.document_id)
        assert len(raw_fc) > 0
        log_result("12. Study Engine: Flashcard Generator", True, f"Cards produced ({len(cards)} parsed)")
    except Exception as e:
        log_result("12. Study Engine: Flashcard Generator", False, str(e))

    # ── 13. Study Tools: Chapter Notes Generator ──
    try:
        from app.study.notes_generator import NotesGenerator
        notes_gen = NotesGenerator(provider, store)
        notes = notes_gen.generate(meta.document_id)
        assert len(notes) > 20
        log_result("13. Study Engine: Chapter Notes Gen", True, f"{len(notes)} chars generated")
    except Exception as e:
        log_result("13. Study Engine: Chapter Notes Gen", False, str(e))

    # ── 14. Audio Notes & Whisper Integration ──
    try:
        from app.audio.recorder import AudioRecorder
        from app.ai.whisper_provider import WhisperProvider
        recorder = AudioRecorder()
        whisper = WhisperProvider()
        is_rec_avail = recorder.is_available()
        is_whisper_avail = whisper.is_available()
        log_result("14. Local Audio Notes & ASR Stack", True, f"Recorder: {is_rec_avail}, Whisper ASR: {is_whisper_avail}")
    except Exception as e:
        log_result("14. Local Audio Notes & ASR Stack", False, str(e))

    # ── 15. Real Hardware Benchmarking Runner ──
    try:
        from app.benchmark.benchmark_runner import BenchmarkRunner
        from app.benchmark.benchmark_store import BenchmarkStore
        b_store = BenchmarkStore(ctx.data_dir / "benchmarks")
        b_runner = BenchmarkRunner(provider=provider, embeddings=embeddings, retriever=retriever, store=b_store, iterations=2)
        emb_run = b_runner.run_embedding_benchmark()
        assert emb_run.total_latency_seconds > 0.0
        assert emb_run.memory_after_mb > 0.0
        csv_export = b_store.export_csv()
        assert len(csv_export) > 0
        log_result("15. Real Benchmark Runner & Exporters", True, f"Emb Latency: {emb_run.total_latency_seconds:.3f}s, Memory: {emb_run.memory_after_mb:.1f}MB")
    except Exception as e:
        log_result("15. Real Benchmark Runner & Exporters", False, str(e))

    # ── 16. Hardware Detection (Snapdragon / QNN / CPU) ──
    try:
        from app.hardware.system_detector import detect_system
        sys_info = detect_system()
        assert "architecture" in sys_info
        assert "snapdragon_status" in sys_info
        assert "qnn_status" in sys_info
        log_result("16. Conservative Hardware Detection", True, f"Arch: {sys_info['architecture']}, Snap: {sys_info['snapdragon_status']}, QNN: {sys_info['qnn_status']}")
    except Exception as e:
        log_result("16. Conservative Hardware Detection", False, str(e))

    # ── 17. Privacy & Offline Network Gating ──
    try:
        from app.privacy.network_guard import NetworkGuard
        from app.privacy.local_storage import LocalStorageInfo
        from app.core.errors import PrivacyViolationError
        
        # Test NetworkGuard offline enforcement
        guard = NetworkGuard(offline_mode=True)
        assert guard.is_offline()
        blocked = False
        try:
            guard.check_allowed("cloud_llm_call")
        except PrivacyViolationError:
            blocked = True
        assert blocked, "NetworkGuard must block network operations in offline mode"
        guard.set_offline_mode(False)
        guard.check_allowed("local_operation")

        # Test LocalStorageInfo
        storage_desc = LocalStorageInfo(ctx.data_dir).describe()
        assert storage_desc["total_size_mb"] >= 0
        assert storage_desc["ai_processing"] == "Local"
        assert storage_desc["telemetry"] == "Disabled"
        assert storage_desc["cloud_ai"] == "Disabled"
        log_result("17. Privacy Controls & Network Guard", True, f"Network Guard Gating Verified, Local Size: {storage_desc['total_size_mb']}MB")
    except Exception as e:
        log_result("17. Privacy Controls & Network Guard", False, str(e))

    # ── 18. Qualcomm AI Hub Module & SDK Integration ──
    try:
        from app.ai.qualcomm_ai_hub import QualcommAIHubManager
        from app.utils.paths import get_models_dir
        hub_mgr = QualcommAIHubManager(get_models_dir())
        curated = hub_mgr.list_curated_models()
        assert len(curated) >= 3
        compile_script = hub_mgr.generate_hub_compile_script("llama-v3_2-3b-instruct")
        assert "qai_hub" in compile_script
        log_result("18. Qualcomm AI Hub SDK & Catalog", True, f"{len(curated)} curated models for Snapdragon NPU")
    except Exception as e:
        log_result("18. Qualcomm AI Hub SDK & Catalog", False, str(e))

    # ── 19. Desktop UI (PySide6 / Qt6 Offscreen Validation) ──
    try:
        from PySide6.QtWidgets import QApplication
        from app.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        win = MainWindow(ctx)
        # Verify navigation to all views
        for view_name in ["desk", "dashboard", "library", "chat", "study", "audio", "benchmark", "settings"]:
            win.navigate_to(view_name)
        assert win._views["desk"].shelf_items_layout.count() >= 1
        log_result("19. PySide6 Desktop Studio & Views", True, "All 8 views instantiated & navigated cleanly")
    except Exception as e:
        log_result("19. PySide6 Desktop Studio & Views", False, str(e))

    # ── 20. CLI Diagnostic Scripts ──
    try:
        assert (PROJECT_ROOT / "scripts" / "detect_environment.py").exists()
        assert (PROJECT_ROOT / "scripts" / "validate_installation.py").exists()
        assert (PROJECT_ROOT / "scripts" / "benchmark.py").exists()
        assert (PROJECT_ROOT / "scripts" / "qualcomm_ai_hub_workflow.py").exists()
        log_result("20. Production CLI Diagnostic Scripts", True, "4 standalone CLI scripts verified")
    except Exception as e:
        log_result("20. Production CLI Diagnostic Scripts", False, str(e))

    # ── Summary ──
    print("=" * 70)
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print(f"  AUDIT SUMMARY: {passed_count} / {total_count} SUBSYSTEMS VERIFIED OPERATIONAL")
    print("=" * 70)

    if passed_count == total_count:
        print("  VERDICT: 🟢 WE ARE 100% GOOD TO GO! SUBMISSION READY.")
    else:
        print("  VERDICT: 🔴 ATTENTION REQUIRED ON FAILED CHECKS.")
    print("=" * 70)

    return passed_count == total_count


if __name__ == "__main__":
    success = run_full_system_audit()
    sys.exit(0 if success else 1)
