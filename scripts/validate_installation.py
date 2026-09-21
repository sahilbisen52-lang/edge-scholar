"""
EdgeScholar — Installation Validator

Checks that all required dependencies are installed and functional.
Run with: python scripts/validate_installation.py
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CHECKS = []


def check(name: str, critical: bool = True):
    """Decorator to register a check function."""
    def decorator(fn):
        CHECKS.append((name, fn, critical))
        return fn
    return decorator


@check("Python >= 3.11")
def check_python():
    major, minor = sys.version_info[:2]
    assert (major, minor) >= (3, 11), f"Python {major}.{minor} < 3.11"
    return f"{major}.{minor}"


@check("PySide6")
def check_pyside6():
    import PySide6
    return PySide6.__version__


@check("PyMuPDF (PDF parsing)")
def check_pymupdf():
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    return fitz.version[0]


@check("FAISS (vector index)")
def check_faiss():
    import faiss
    return getattr(faiss, "__version__", "installed")


@check("sentence-transformers (embeddings)")
def check_sentence_transformers():
    import sentence_transformers
    return sentence_transformers.__version__


@check("numpy")
def check_numpy():
    import numpy
    return numpy.__version__


@check("pydantic")
def check_pydantic():
    import pydantic
    return pydantic.__version__


@check("psutil")
def check_psutil():
    import psutil
    return psutil.__version__


@check("SQLite (stdlib)")
def check_sqlite():
    import sqlite3
    return sqlite3.sqlite_version


@check("EdgeScholar core modules")
def check_core_imports():
    from app.config.constants import APP_NAME
    from app.config.settings import EdgeScholarSettings
    from app.core.errors import EdgeScholarError
    from app.core.events import EventBus
    from app.utils.paths import get_data_dir
    return f"OK ({APP_NAME})"


@check("Document parsing modules")
def check_document_modules():
    from app.documents.parser import DocumentParser
    from app.documents.metadata import DocumentMetadata
    from app.documents.document_store import DocumentStore
    return "OK"


@check("Retrieval modules")
def check_retrieval_modules():
    from app.retrieval.chunker import Chunker
    from app.retrieval.embeddings import LocalEmbeddings
    from app.retrieval.vector_store import VectorStore
    from app.retrieval.retriever import Retriever
    return "OK"


@check("AI provider modules")
def check_ai_modules():
    from app.ai.base_provider import AIProvider
    from app.ai.mock_provider import MockProvider
    from app.ai.provider_factory import ProviderFactory
    from app.ai.model_manager import ModelManager
    return "OK"


@check("RAG modules")
def check_rag_modules():
    from app.rag.pipeline import RAGPipeline
    from app.rag.citation_builder import build_citations
    from app.rag.prompt_templates import rag_qa_prompt
    return "OK"


@check("Study modules")
def check_study_modules():
    from app.study.summarizer import Summarizer
    from app.study.quiz_generator import QuizGenerator
    from app.study.flashcards import FlashcardGenerator
    from app.study.notes_generator import NotesGenerator
    return "OK"


@check("Hardware detection")
def check_hardware():
    from app.hardware.system_detector import detect_system
    info = detect_system()
    return f"OS={info['os']}, Arch={info['architecture']}"


@check("Benchmark modules")
def check_benchmark():
    from app.benchmark.metrics import BenchmarkRun
    from app.benchmark.benchmark_store import BenchmarkStore
    return "OK"


@check("llama-cpp-python (optional)", critical=False)
def check_llama_cpp():
    import llama_cpp
    return getattr(llama_cpp, "__version__", "installed")


@check("faster-whisper (optional)", critical=False)
def check_faster_whisper():
    import faster_whisper
    return getattr(faster_whisper, "__version__", "installed")


@check("sounddevice (optional)", critical=False)
def check_sounddevice():
    import sounddevice
    return sounddevice.__version__


def main() -> None:
    print("=" * 60)
    print("  EdgeScholar — Installation Validation")
    print("=" * 60)

    passed = 0
    failed = 0
    optional_failed = 0

    for name, fn, critical in CHECKS:
        try:
            result = fn()
            print(f"  ✅ {name:<40} {result}")
            passed += 1
        except ImportError as e:
            if critical:
                print(f"  ❌ {name:<40} MISSING: {e}")
                failed += 1
            else:
                print(f"  ⚠️  {name:<40} Not installed (optional)")
                optional_failed += 1
        except AssertionError as e:
            if critical:
                print(f"  ❌ {name:<40} FAIL: {e}")
                failed += 1
            else:
                print(f"  ⚠️  {name:<40} {e} (optional)")
                optional_failed += 1
        except Exception as e:
            if critical:
                print(f"  ❌ {name:<40} ERROR: {e}")
                failed += 1
            else:
                print(f"  ⚠️  {name:<40} {e} (optional)")
                optional_failed += 1

    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed, {optional_failed} optional skipped")
    if failed == 0:
        print("  ✅ Installation is valid. EdgeScholar is ready to run.")
    else:
        print(f"  ❌ {failed} critical check(s) failed. Please install missing dependencies.")
        print("     Run: pip install -e '.[dev]' in the project root")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
