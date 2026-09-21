"""PDF document parser using PyMuPDF."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.documents.metadata import DocumentMetadata, PageContent
from app.core.errors import DocumentParseError
from app.utils.hashing import sha256_file
from app.utils.timestamps import utc_now

logger = logging.getLogger("edge_scholar.documents")


class PdfParser:
    """Parse PDF files into pages using PyMuPDF (fitz)."""

    MIN_TEXT_CHARS_PER_PAGE = 50  # Below this, page may be scanned

    def parse(self, path: Path) -> tuple[DocumentMetadata, list[PageContent]]:
        try:
            try:
                import pymupdf as fitz  # Modern PyMuPDF
            except ImportError:
                import fitz
        except ImportError:
            raise DocumentParseError(
                "PyMuPDF not installed",
                user_message="PDF parsing requires PyMuPDF. Please install it.",
            )

        try:
            doc = fitz.open(str(path))
        except Exception as e:
            raise DocumentParseError(str(e), user_message=f"Could not open PDF: {path.name}")

        pages: list[PageContent] = []
        total_chars = 0
        scanned_page_count = 0

        # Extract PDF metadata
        pdf_meta = doc.metadata or {}
        doc_id = sha256_file(path)[:16]  # Use partial hash as stable ID

        meta = DocumentMetadata(
            document_id=doc_id,
            filename=path.name,
            file_path=str(path),
            file_type="pdf",
            file_size_bytes=path.stat().st_size,
            page_count=len(doc),
            sha256=sha256_file(path),
            title=pdf_meta.get("title", "") or path.stem,
            author=pdf_meta.get("author", "") or "",
            subject=pdf_meta.get("subject", "") or "",
            import_timestamp=utc_now(),
        )

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text") or ""
            text = text.strip()

            if len(text) < self.MIN_TEXT_CHARS_PER_PAGE:
                scanned_page_count += 1
                logger.debug("Page %d appears to be scanned (low text)", page_num + 1)
                text = f"[Page {page_num + 1}: Low text detected — may be scanned image]"

            total_chars += len(text)
            pages.append(
                PageContent(
                    document_id=doc_id,
                    page_number=page_num + 1,
                    text=text,
                    character_count=len(text),
                )
            )

        doc.close()
        meta.character_count = total_chars

        if scanned_page_count > 0:
            logger.warning(
                "%d/%d pages in '%s' appear to be scanned",
                scanned_page_count, len(pages), path.name,
            )

        logger.info(
            "Parsed PDF '%s': %d pages, %d chars",
            path.name, len(pages), total_chars,
        )
        return meta, pages
