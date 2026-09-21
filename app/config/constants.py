"""Application-wide constants."""
from __future__ import annotations

APP_NAME = "EdgeScholar"
APP_VERSION = "0.1.0"
APP_SUBTITLE = "Private On-Device AI Study Copilot"

# Chunking defaults
DEFAULT_CHUNK_SIZE = 600  # tokens
DEFAULT_CHUNK_OVERLAP = 100  # tokens
DEFAULT_TOP_K = 5

# LLM defaults
DEFAULT_TEMPERATURE = 0.15
DEFAULT_MAX_TOKENS = 512

# Embedding
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# File limits
MAX_FILE_SIZE_MB = 100
SUPPORTED_DOC_EXTENSIONS = {".pdf", ".txt", ".md"}
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}

# Model manifest
MODEL_MANIFEST_FILE = "models/model_manifest.json"

# Database
DB_FILENAME = "edge_scholar.db"

# Benchmark
DEFAULT_BENCHMARK_ITERATIONS = 3
