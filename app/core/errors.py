"""EdgeScholar custom exception hierarchy."""
from __future__ import annotations


class EdgeScholarError(Exception):
    """Base exception for all EdgeScholar errors."""
    user_message: str = "An unexpected error occurred."

    def __init__(self, message: str = "", user_message: str = "") -> None:
        super().__init__(message or self.user_message)
        if user_message:
            self.user_message = user_message


class DocumentParseError(EdgeScholarError):
    user_message = "Failed to parse the document."


class IndexError(EdgeScholarError):
    user_message = "Failed to index the document."


class EmbeddingError(EdgeScholarError):
    user_message = "Failed to generate embeddings."


class ModelNotLoadedError(EdgeScholarError):
    user_message = "No AI model is currently loaded."


class ModelLoadError(EdgeScholarError):
    user_message = "Failed to load the AI model."


class GenerationError(EdgeScholarError):
    user_message = "The AI model failed to generate a response."


class TranscriptionError(EdgeScholarError):
    user_message = "Audio transcription failed."


class FileSizeError(EdgeScholarError):
    user_message = "File exceeds the maximum allowed size."


class UnsupportedFileTypeError(EdgeScholarError):
    user_message = "This file type is not supported."


class PrivacyViolationError(EdgeScholarError):
    user_message = "Operation blocked: offline mode is enabled."


class BenchmarkError(EdgeScholarError):
    user_message = "Benchmark failed to complete."


class StorageError(EdgeScholarError):
    user_message = "Storage operation failed."
