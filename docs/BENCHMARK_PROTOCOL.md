# Benchmark Protocol

## Principles

1. **All measurements are real.** No fabricated numbers.
2. **Hardware is clearly identified.** Never present dev-machine results as Snapdragon results.
3. **Units are explicit.** Seconds, milliseconds, tokens/second — never ambiguous.
4. **N/A is used honestly.** When a metric cannot be measured, it is reported as N/A.
5. **Iterations are documented.** Results show the number of runs averaged.

---

## Benchmark Categories

### A. Embedding Latency
- **Metric:** Time to embed N text strings (seconds)
- **Input:** 3 fixed test prompts (~15-30 tokens each)
- **Model:** all-MiniLM-L6-v2 (sentence-transformers)
- **Reported:** average over N iterations

### B. Retrieval Latency
- **Metric:** Time from query embedding to FAISS search result (seconds)
- **Input:** 1 query, index with K documents
- **Reported:** single run (fast enough not to need averaging)

### C. LLM Time to First Token (TTFT)
- **Metric:** Time from prompt submission to first token (seconds)
- **Reported:** available only when streaming; marked N/A for non-streaming models

### D. LLM Tokens per Second
- **Metric:** Output tokens generated per second
- **Reported:** from provider if available; "Not reported by runtime" if unavailable

### E. End-to-End Response Time
- **Metric:** Total time from user question to complete answer (seconds)
- **Includes:** embedding + retrieval + LLM generation

### F. Cold Start
- **Metric:** Time from app launch to first inference ready (seconds)
- **Reported:** manual measurement

### G. Memory Usage
- **Metric:** RSS memory before and after inference (MB)
- **Tool:** psutil

---

## Standard Test Inputs

Fixed prompts used for all LLM benchmarks:
1. "In one paragraph, explain what an operating system process is."
2. "What is the difference between a set and a multiset?"
3. "Explain function composition in mathematics."

These are intentionally short to allow reproducible measurement.

---

## Result Format

```json
{
  "run_id": "...",
  "timestamp": "2024-01-01T12:00:00Z",
  "model": "Llama-3.2-3B-Q4",
  "runtime": "llama.cpp",
  "backend": "llama.cpp",
  "accelerator": "CPU (unverified)",
  "category": "llm",
  "input_tokens": 25,
  "output_tokens": 87,
  "ttft_seconds": null,
  "generation_seconds": 10.4,
  "tokens_per_second": 8.4,
  "total_latency_seconds": 10.6,
  "memory_before_mb": 420.1,
  "memory_after_mb": 2100.4,
  "system_info": {
    "os": "macOS",
    "architecture": "arm64",
    "ram_gb": 16
  }
}
```

---

## Comparison Table Format

| Run | Backend | Accelerator | TTFT | Tokens/s | Total |
|-----|---------|-------------|------|----------|-------|
| 1   | llama.cpp | CPU       | N/A  | 8.4      | 10.6s |
| 2   | QNN     | NPU (VERIFIED) | 0.7s | 21.4  | 2.1s  |

> Row 2 would only appear on a Snapdragon device with QNN confirmed.

---

## What We Do NOT Report

- ❌ TOPS (Tera Operations Per Second) — requires vendor-reported hardware spec, not runtime measurement
- ❌ Energy efficiency — not measured
- ❌ Theoretical throughput — only measured throughput
- ❌ Comparative claims without both measurements available
