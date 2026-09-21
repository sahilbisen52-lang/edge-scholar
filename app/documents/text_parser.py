"""Plain text / markdown document parser."""
from __future__ import annotations

import logging
from pathlib import Path

from app.documents.metadata import DocumentMetadata, PageContent
from app.core.errors import DocumentParseError
from app.utils.hashing import sha256_file
from app.utils.timestamps import utc_now

logger = logging.getLogger("edge_scholar.documents")

CHARS_PER_VIRTUAL_PAGE = 3000


class TextParser:
    def parse(self, path: Path) -> tuple[DocumentMetadata, list[PageContent]]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            raise DocumentParseError(str(e), user_message=f"Could not read file: {path.name}")

        doc_id = sha256_file(path)[:16]
        ext = path.suffix.lower().lstrip(".")

        meta = DocumentMetadata(
            document_id=doc_id,
            filename=path.name,
            file_path=str(path),
            file_type=ext,
            file_size_bytes=path.stat().st_size,
            sha256=sha256_file(path),
            title=path.stem,
            character_count=len(text),
            import_timestamp=utc_now(),
        )

        # Split into virtual pages
        pages = []
        chunks = [text[i:i + CHARS_PER_VIRTUAL_PAGE] for i in range(0, max(len(text), 1), CHARS_PER_VIRTUAL_PAGE)]
        if not chunks:
            chunks = ["(empty document)"]

        for i, chunk in enumerate(chunks, 1):
            pages.append(PageContent(
                document_id=doc_id,
                page_number=i,
                text=chunk.strip(),
                character_count=len(chunk),
            ))

        meta.page_count = len(pages)
        logger.info("Parsed text '%s': %d virtual pages, %d chars", path.name, len(pages), len(text))
        return meta, pages
