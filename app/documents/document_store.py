"""SQLite-backed document store."""
from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

from app.documents.metadata import DocumentMetadata, PageContent
from app.core.errors import StorageError

logger = logging.getLogger("edge_scholar.documents")


CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size_bytes INTEGER,
    page_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    indexed INTEGER DEFAULT 0,
    import_timestamp TEXT,
    sha256 TEXT,
    title TEXT,
    author TEXT,
    subject TEXT,
    metadata_json TEXT
)
"""

CREATE_PAGES_TABLE = """
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    character_count INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
)
"""

CREATE_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_estimate INTEGER,
    hash TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
)
"""

CREATE_STATS_TABLE = """
CREATE TABLE IF NOT EXISTS stats (
    key TEXT PRIMARY KEY,
    value TEXT
)
"""


class DocumentStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(CREATE_DOCUMENTS_TABLE)
            conn.execute(CREATE_PAGES_TABLE)
            conn.execute(CREATE_CHUNKS_TABLE)
            conn.execute(CREATE_STATS_TABLE)
            conn.commit()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def upsert_document(self, meta: DocumentMetadata) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents
                (document_id, filename, file_path, file_type, file_size_bytes,
                 page_count, character_count, chunk_count, indexed,
                 import_timestamp, sha256, title, author, subject)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    meta.document_id, meta.filename, meta.file_path, meta.file_type,
                    meta.file_size_bytes, meta.page_count, meta.character_count,
                    meta.chunk_count, int(meta.indexed), meta.import_timestamp.isoformat(),
                    meta.sha256, meta.title, meta.author, meta.subject,
                ),
            )
            conn.commit()

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id=?", (document_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_meta(row)

    def list_documents(self) -> List[DocumentMetadata]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY import_timestamp DESC"
            ).fetchall()
        return [self._row_to_meta(r) for r in rows]

    def delete_document(self, document_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM pages WHERE document_id=?", (document_id,))
            conn.execute("DELETE FROM chunks WHERE document_id=?", (document_id,))
            conn.execute("DELETE FROM documents WHERE document_id=?", (document_id,))
            conn.commit()
        logger.info("Deleted document %s from store", document_id)

    def save_pages(self, pages: list[PageContent]) -> None:
        if not pages:
            return
        doc_id = pages[0].document_id
        with self._conn() as conn:
            conn.execute("DELETE FROM pages WHERE document_id=?", (doc_id,))
            conn.executemany(
                "INSERT INTO pages (document_id, page_number, text, character_count) VALUES (?,?,?,?)",
                [(p.document_id, p.page_number, p.text, p.character_count) for p in pages],
            )
            conn.commit()

    def get_pages(self, document_id: str) -> list[PageContent]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM pages WHERE document_id=? ORDER BY page_number",
                (document_id,),
            ).fetchall()
        return [PageContent(document_id=r["document_id"], page_number=r["page_number"], text=r["text"], character_count=r["character_count"]) for r in rows]

    def save_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        doc_id = chunks[0]["document_id"]
        with self._conn() as conn:
            conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
            conn.executemany(
                "INSERT OR REPLACE INTO chunks (chunk_id, document_id, page_number, text, token_estimate, hash) VALUES (?,?,?,?,?,?)",
                [(c["chunk_id"], c["document_id"], c["page_number"], c["text"], c.get("token_estimate", 0), c.get("hash", "")) for c in chunks],
            )
            conn.commit()

    def get_chunks(self, document_id: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE document_id=? ORDER BY page_number",
                (document_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_chunks(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM chunks ORDER BY document_id, page_number").fetchall()
        return [dict(r) for r in rows]

    def get_total_questions_answered(self) -> int:
        with self._conn() as conn:
            row = conn.execute("SELECT value FROM stats WHERE key='questions_answered'").fetchone()
        if row:
            try:
                return int(row["value"])
            except Exception:
                return 0
        return 0

    def increment_questions_answered(self) -> None:
        current = self.get_total_questions_answered()
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO stats (key, value) VALUES ('questions_answered', ?)",
                (str(current + 1),),
            )
            conn.commit()

    @staticmethod
    def _row_to_meta(row: sqlite3.Row) -> DocumentMetadata:
        from datetime import datetime
        ts = row["import_timestamp"]
        try:
            import_ts = datetime.fromisoformat(ts) if ts else utc_now()
        except Exception:
            from app.utils.timestamps import utc_now
            import_ts = utc_now()
        from app.utils.timestamps import utc_now
        return DocumentMetadata(
            document_id=row["document_id"],
            filename=row["filename"],
            file_path=row["file_path"],
            file_type=row["file_type"],
            file_size_bytes=row["file_size_bytes"] or 0,
            page_count=row["page_count"] or 0,
            character_count=row["character_count"] or 0,
            chunk_count=row["chunk_count"] or 0,
            indexed=bool(row["indexed"]),
            import_timestamp=import_ts,
            sha256=row["sha256"] or "",
            title=row["title"] or "",
            author=row["author"] or "",
            subject=row["subject"] or "",
        )
