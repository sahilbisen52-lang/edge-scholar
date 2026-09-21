"""Simple in-process event bus for decoupled communication between components."""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger("edge_scholar.events")


class EventBus:
    """Lightweight publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable[..., Any]) -> None:
        self._subscribers[event].append(handler)

    def unsubscribe(self, event: str, handler: Callable[..., Any]) -> None:
        self._subscribers[event] = [
            h for h in self._subscribers[event] if h is not handler
        ]

    def publish(self, event: str, **kwargs: Any) -> None:
        for handler in list(self._subscribers.get(event, [])):
            try:
                handler(**kwargs)
            except Exception as exc:
                logger.exception("Event handler error for '%s': %s", event, exc)


# Event name constants
class Events:
    DOCUMENT_IMPORTED = "document.imported"
    DOCUMENT_INDEXED = "document.indexed"
    DOCUMENT_DELETED = "document.deleted"
    MODEL_LOADED = "model.loaded"
    MODEL_UNLOADED = "model.unloaded"
    GENERATION_STARTED = "generation.started"
    GENERATION_COMPLETE = "generation.complete"
    TRANSCRIPTION_COMPLETE = "transcription.complete"
    BENCHMARK_COMPLETE = "benchmark.complete"
    SETTINGS_CHANGED = "settings.changed"
    OFFLINE_MODE_CHANGED = "offline_mode.changed"
    ERROR_OCCURRED = "error.occurred"
    STATUS_MESSAGE = "status.message"
