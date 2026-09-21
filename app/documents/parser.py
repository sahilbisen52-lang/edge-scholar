"""Unified document parser dispatcher."""
from __future__ import annotations

from pathlib import Path

from app.documents.metadata import DocumentMetadata, PageContent
from app.documents.pdf_parser import PdfParser
from app.documents.text_parser import TextParser
from app.core.errors import UnsupportedFileTypeError


class DocumentParser:
    def __init__(self) -> None:
        self._pdf = PdfParser()
        self._text = TextParser()

    def parse(self, path: Path | str) -> tuple[DocumentMetadata, list[PageContent]]:
        path = Path(path)
        ext = path.suffix.lower()
        if ext == ".pdf":
            return self._pdf.parse(path)
        elif ext in (".txt", ".md", ".text"):
            return self._text.parse(path)
        else:
            raise UnsupportedFileTypeError(
                f"No parser for {ext}",
                user_message=f"Cannot parse '{ext}' files.",
            )
