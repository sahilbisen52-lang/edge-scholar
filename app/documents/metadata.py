"""Document metadata models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.utils.timestamps import utc_now


@dataclass
class DocumentMetadata:
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    file_path: str = ""
    file_type: str = ""  # pdf, txt, md
    file_size_bytes: int = 0
    page_count: int = 0
    character_count: int = 0
    chunk_count: int = 0
    indexed: bool = False
    import_timestamp: datetime = field(default_factory=utc_now)
    sha256: str = ""
    title: str = ""
    author: str = ""
    subject: str = ""

    @property
    def size_mb(self) -> float:
        return self.file_size_bytes / (1024 * 1024)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "character_count": self.character_count,
            "chunk_count": self.chunk_count,
            "indexed": self.indexed,
            "import_timestamp": self.import_timestamp.isoformat(),
            "sha256": self.sha256,
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentMetadata":
        from datetime import datetime
        ts = data.get("import_timestamp", "")
        if isinstance(ts, str):
            try:
                data["import_timestamp"] = datetime.fromisoformat(ts)
            except Exception:
                data["import_timestamp"] = utc_now()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PageContent:
    document_id: str
    page_number: int
    text: str
    character_count: int = 0

    def __post_init__(self) -> None:
        if not self.character_count:
            self.character_count = len(self.text)
