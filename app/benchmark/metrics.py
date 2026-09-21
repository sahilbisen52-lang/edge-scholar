"""Benchmark metric dataclasses."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from app.utils.timestamps import utc_now


@dataclass
class BenchmarkRun:
    run_id: str
    timestamp: datetime = field(default_factory=utc_now)
    model: str = ""
    runtime: str = ""
    backend: str = ""
    accelerator: str = ""
    category: str = ""  # embedding | retrieval | llm_ttft | llm_tps | e2e | asr | memory | cold_start
    input_tokens: int = 0
    output_tokens: int = 0
    ttft_seconds: Optional[float] = None
    generation_seconds: Optional[float] = None
    tokens_per_second: Optional[float] = None
    total_latency_seconds: Optional[float] = None
    memory_before_mb: Optional[float] = None
    memory_after_mb: Optional[float] = None
    notes: str = ""
    system_info: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "BenchmarkRun":
        ts = data.pop("timestamp", None)
        if isinstance(ts, str):
            try:
                data["timestamp"] = datetime.fromisoformat(ts)
            except Exception:
                data["timestamp"] = utc_now()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def display_row(self) -> dict:
        """Flat dict for table display."""
        return {
            "Run ID": self.run_id[:8],
            "Category": self.category,
            "Model": self.model or "N/A",
            "Backend": self.runtime or self.backend or "N/A",
            "Accelerator": self.accelerator or "N/A",
            "TTFT (s)": f"{self.ttft_seconds:.3f}" if self.ttft_seconds is not None else "N/A",
            "Tokens/s": f"{self.tokens_per_second:.1f}" if self.tokens_per_second is not None else "N/A",
            "Total (s)": f"{self.total_latency_seconds:.3f}" if self.total_latency_seconds is not None else "N/A",
        }
