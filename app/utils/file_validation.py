"""File validation and security checks."""
from __future__ import annotations

from pathlib import Path

from app.config.constants import MAX_FILE_SIZE_MB, SUPPORTED_DOC_EXTENSIONS, SUPPORTED_AUDIO_EXTENSIONS
from app.core.errors import FileSizeError, UnsupportedFileTypeError


def validate_document_file(path: Path) -> None:
    """Validate a document file before ingestion. Raises on failure."""
    _check_extension(path, SUPPORTED_DOC_EXTENSIONS)
    _check_size(path)
    _check_path_traversal(path)


def validate_audio_file(path: Path) -> None:
    _check_extension(path, SUPPORTED_AUDIO_EXTENSIONS)
    _check_size(path)
    _check_path_traversal(path)


def _check_extension(path: Path, allowed: set[str]) -> None:
    if path.suffix.lower() not in allowed:
        raise UnsupportedFileTypeError(
            f"Extension '{path.suffix}' not in {allowed}",
            user_message=f"File type '{path.suffix}' is not supported.",
        )


def _check_size(path: Path) -> None:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise FileSizeError(
            f"File size {size_mb:.1f}MB exceeds {MAX_FILE_SIZE_MB}MB limit",
            user_message=f"File is too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB.",
        )


def _check_path_traversal(path: Path) -> None:
    resolved = path.resolve()
    # Ensure the path doesn't contain traversal sequences
    if ".." in str(path):
        raise ValueError(f"Path traversal detected in: {path}")
