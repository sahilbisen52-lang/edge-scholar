"""Logging configuration for EdgeScholar."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> None:
    """Configure root logger with console + optional file output."""
    handlers: list[logging.Handler] = []

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    handlers.append(console)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        handlers.append(fh)

    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Suppress noisy third-party loggers
    for name in ("urllib3", "httpx", "httpcore", "sentence_transformers", "transformers"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger("edge_scholar").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"edge_scholar.{name}")
