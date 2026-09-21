"""
CLI Benchmark Runner for EdgeScholar.

Run with:
    python scripts/benchmark.py --category all
    python scripts/benchmark.py --category embedding --iterations 5
    python scripts/benchmark.py --category llm
"""
from __future__ import annotations

import argparse
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.app_context import AppContext
from app.benchmark.benchmark_runner import BenchmarkRunner
from app.benchmark.benchmark_store import BenchmarkStore
from app.retrieval.embeddings import LocalEmbeddings
from app.retrieval.vector_store import VectorStore
from app.retrieval.retriever import Retriever
from app.ai.provider_factory import ProviderFactory
from app.utils.paths import get_models_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="EdgeScholar CLI Benchmark Runner")
    parser.add_argument(
        "--category",
        choices=["embedding", "llm", "all"],
        default="all",
        help="Benchmark workload to execute (default: all)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations for embedding benchmark (default: 3)",
    )
    args = parser.parse_args()

    print("=" * 65)
    print("  EdgeScholar — On-Device Performance Benchmark")
    print("=" * 65)

    ctx = AppContext()
    store = BenchmarkStore(ctx.data_dir / "benchmarks")

    print("Initializing local embeddings & providers...")
    embeddings = LocalEmbeddings(ctx.settings.selected_embedding_model)
    vs = VectorStore(ctx.data_dir / "indexes")
    retriever = Retriever(embeddings, vs)

    factory = ProviderFactory(
        preferred=ctx.settings.preferred_runtime,
        models_dir=get_models_dir(),
    )
    provider = factory.create()

    runner = BenchmarkRunner(
        provider=provider,
        embeddings=embeddings,
        retriever=retriever,
        store=store,
        iterations=args.iterations,
    )

    print(f"Executing category: {args.category.upper()} (iterations: {args.iterations})...\n")

    runs = []
    if args.category == "embedding":
        runs.append(runner.run_embedding_benchmark())
    elif args.category == "llm":
        runs.append(runner.run_llm_benchmark())
    elif args.category == "all":
        runs = runner.run_all()

    print("-" * 65)
    print(f"{'Category':<12} | {'Backend':<20} | {'Latency':<10} | {'Tokens/s'}")
    print("-" * 65)

    for r in runs:
        lat = f"{r.total_latency_seconds:.3f}s" if r.total_latency_seconds is not None else "N/A"
        tps = f"{r.tokens_per_second:.1f}" if r.tokens_per_second is not None else "N/A"
        print(f"{r.category.upper():<12} | {r.backend[:20]:<20} | {lat:<10} | {tps}")

    print("-" * 65)
    print(f"✅ Benchmark finished! Results saved to: {store._path}")


if __name__ == "__main__":
    main()
