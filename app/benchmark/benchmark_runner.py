"""Benchmark runner — real timing measurements only. No fabricated data."""
from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

import psutil

from app.ai.base_provider import AIProvider
from app.benchmark.metrics import BenchmarkRun
from app.benchmark.benchmark_store import BenchmarkStore
from app.hardware.system_detector import detect_system
from app.retrieval.embeddings import LocalEmbeddings
from app.retrieval.retriever import Retriever

logger = logging.getLogger("edge_scholar.benchmark")

TEST_TEXTS = [
    "Explain the concept of process scheduling in operating systems.",
    "What is virtual memory and how does paging work?",
    "Describe the differences between a set, multiset, and sequence in discrete mathematics.",
]


class BenchmarkRunner:
    def __init__(
        self,
        provider: AIProvider,
        embeddings: LocalEmbeddings,
        retriever: Optional[Retriever],
        store: BenchmarkStore,
        iterations: int = 3,
    ) -> None:
        self.provider = provider
        self.embeddings = embeddings
        self.retriever = retriever
        self.store = store
        self.iterations = iterations
        self._sys_info = detect_system()

    def _get_runtime_info(self) -> tuple[str, str, str]:
        rt = self.provider.get_runtime_info()
        model = self.provider.get_model_info()
        return (
            model.model_id if model else "none",
            rt.runtime,
            rt.accelerator if rt.accelerator_verified else f"{rt.accelerator} (unverified)",
        )

    def _memory_mb(self) -> float:
        try:
            proc = psutil.Process()
            return proc.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def run_embedding_benchmark(self) -> BenchmarkRun:
        model_id, runtime, acc = self._get_runtime_info()
        latencies = []
        mem_before = self._memory_mb()

        for _ in range(self.iterations):
            t0 = time.perf_counter()
            self.embeddings.embed(TEST_TEXTS)
            latencies.append(time.perf_counter() - t0)

        mem_after = self._memory_mb()
        avg = sum(latencies) / len(latencies)

        run = BenchmarkRun(
            run_id=str(uuid.uuid4()),
            model=model_id,
            runtime="sentence-transformers",
            backend="sentence-transformers",
            accelerator=acc,
            category="embedding",
            input_tokens=sum(len(t.split()) for t in TEST_TEXTS),
            total_latency_seconds=avg,
            memory_before_mb=mem_before,
            memory_after_mb=mem_after,
            notes=f"avg over {self.iterations} iterations",
            system_info=self._sys_info,
        )
        self.store.add(run)
        return run

    def run_llm_benchmark(self) -> BenchmarkRun:
        model_id, runtime, acc = self._get_runtime_info()
        test_prompt = "In one paragraph, explain what an operating system process is."

        mem_before = self._memory_mb()
        t0 = time.perf_counter()
        try:
            result = self.provider.generate(test_prompt, max_tokens=150, temperature=0.15)
            total = time.perf_counter() - t0
            ttft = result.ttft_seconds
            tps = result.tokens_per_second
            output_tokens = result.output_tokens
        except Exception as e:
            total = time.perf_counter() - t0
            ttft = None
            tps = None
            output_tokens = 0
            logger.warning("LLM benchmark generation error: %s", e)

        mem_after = self._memory_mb()

        run = BenchmarkRun(
            run_id=str(uuid.uuid4()),
            model=model_id,
            runtime=runtime,
            backend=runtime,
            accelerator=acc,
            category="llm",
            input_tokens=len(test_prompt.split()),
            output_tokens=output_tokens,
            ttft_seconds=ttft,
            tokens_per_second=tps,
            total_latency_seconds=total,
            memory_before_mb=mem_before,
            memory_after_mb=mem_after,
            system_info=self._sys_info,
        )
        self.store.add(run)
        return run

    def run_all(self) -> list[BenchmarkRun]:
        runs = []
        logger.info("Running embedding benchmark...")
        try:
            runs.append(self.run_embedding_benchmark())
        except Exception as e:
            logger.error("Embedding benchmark failed: %s", e)

        logger.info("Running LLM benchmark...")
        try:
            runs.append(self.run_llm_benchmark())
        except Exception as e:
            logger.error("LLM benchmark failed: %s", e)

        return runs
