"""Central application context — holds shared state and services."""
from __future__ import annotations

import logging
from pathlib import Path

from app.config.settings import EdgeScholarSettings
from app.config.constants import DB_FILENAME
from app.core.events import EventBus
from app.utils.paths import get_data_dir, get_config_dir

logger = logging.getLogger("edge_scholar.core")


class AppContext:
    """Shared application context passed to all major components."""

    def __init__(self) -> None:
        self.data_dir = get_data_dir()
        self.config_dir = get_config_dir()
        self.settings_path = self.config_dir / "settings.json"
        self.db_path = self.data_dir / DB_FILENAME
        self.log_path = self.data_dir / "logs" / "edge_scholar.log"

        # Ensure directories exist
        for d in [
            self.data_dir / "documents",
            self.data_dir / "indexes",
            self.data_dir / "transcripts",
            self.data_dir / "exports",
            self.data_dir / "benchmarks",
            self.data_dir / "cache",
            self.data_dir / "logs",
            self.config_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

        # Load settings
        self.settings = EdgeScholarSettings.load(self.settings_path)

        # Event bus
        self.events = EventBus()

        # Services (lazy-initialized singletons)
        self._document_store = None
        self._vector_store = None
        self._embeddings = None
        self._ai_provider = None
        self._model_manager = None

        logger.info("AppContext initialized. Data dir: %s", self.data_dir)

    def get_document_store(self):
        if self._document_store is None:
            from app.documents.document_store import DocumentStore
            self._document_store = DocumentStore(self.db_path)
        return self._document_store

    def get_vector_store(self):
        if self._vector_store is None:
            from app.retrieval.vector_store import VectorStore
            self._vector_store = VectorStore(self.data_dir / "indexes")
        return self._vector_store

    def get_embeddings(self):
        if self._embeddings is None:
            from app.retrieval.embeddings import LocalEmbeddings
            self._embeddings = LocalEmbeddings(self.settings.selected_embedding_model)
        return self._embeddings

    def get_ai_provider(self, force_refresh: bool = False):
        if self._ai_provider is None or force_refresh:
            from app.ai.provider_factory import ProviderFactory
            from app.utils.paths import get_models_dir
            factory = ProviderFactory(
                preferred=self.settings.preferred_runtime,
                models_dir=get_models_dir(),
            )
            self._ai_provider = factory.create()
        return self._ai_provider

    def save_settings(self) -> None:
        self.settings.save(self.settings_path)
        self.events.publish("settings.changed")
