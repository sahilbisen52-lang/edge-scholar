"""Persistent benchmark storage using JSON."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

from app.benchmark.metrics import BenchmarkRun

logger = logging.getLogger("edge_scholar.benchmark")


class BenchmarkStore:
    def __init__(self, benchmarks_dir: Path) -> None:
        self.dir = benchmarks_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self._path = self.dir / "benchmark_results.json"
        self._runs: List[BenchmarkRun] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self._runs = [BenchmarkRun.from_dict(d) for d in data]
            except Exception as e:
                logger.warning("Could not load benchmarks: %s", e)
                self._runs = []

    def _save(self) -> None:
        self._path.write_text(
            json.dumps([r.to_dict() for r in self._runs], indent=2),
            encoding="utf-8",
        )

    def add(self, run: BenchmarkRun) -> None:
        self._runs.append(run)
        self._save()
        logger.info("Saved benchmark run: %s (category=%s)", run.run_id, run.category)

    def list_runs(self) -> List[BenchmarkRun]:
        return list(reversed(self._runs))

    def clear(self) -> None:
        self._runs = []
        self._save()

    def export_csv(self) -> str:
        """Export all runs as CSV string."""
        import csv
        import io
        if not self._runs:
            return ""
        rows = [r.display_row() for r in self._runs]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()

    def export_json(self) -> str:
        return json.dumps([r.to_dict() for r in self._runs], indent=2)
