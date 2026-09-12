from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.services.document_ingestion import (
    DocumentIngestionResult,
    ingest_document,
)
from app.services.document_parser import DocumentParseError
from app.services.embedding import EmbeddingError
from app.services.file_storage import SavedFile
from app.services.vector_store import VectorStoreError


class _FakeSession:
    """只为版本切换回归测试提供最小 Session 行为。"""

    def __init__(self, document: Document, max_version: int) -> None:
        self.document = document
        self.max_version = max_version
        self.scalar_calls = 0
        self.pending: list[object] = []

    def scalar(self, _statement):
        self.scalar_calls += 1
        if self.scalar_calls == 1:
            return self.document
        if self.scalar_calls == 2:
            # 第二次查询是 SHA-256 重复版本检查。
            return None
        if self.scalar_calls == 3:
            # 第三次查询是当前最大版本号。
            return self.max_version
        raise AssertionError("unexpected scalar call")

    def add(self, value: object) -> None:
        self.pending.append(value)

    def add_all(self, values: list[object]) -> None:
        self.pending.extend(values)

    def flush(self) -> None:
        for value in self.pending:
            if isinstance(value, DocumentVersion) and value.id is None:
                value.id = 99

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def get(self, model, identity: int):
        if model is DocumentVersion:
            for value in self.pending:
                if isinstance(value, DocumentVersion) and value.id == identity:
                    return value
        if model is Document and identity == self.document.id:
            return self.document
        return None


def _saved_file(tmp_path: Path) -> SavedFile:
    path = tmp_path / "new-version.txt"
    path.write_text("new version", encoding="utf-8")
    return SavedFile(
        original_filename="guide.txt",
        stored_filename=path.name,
        storage_path=path,
        file_type="txt",
        file_size=11,
        file_sha256="a" * 64,
    )


def _existing_document() -> Document:
    return Document(
        id=10,
        knowledge_base_id=3,
        original_filename="guide.txt",
        normalized_filename="guide.txt",
        file_type="txt",
        current_version_id=7,
    )


def test_failed_ingestion_keeps_previous_current_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    document = _existing_document()
    db = _FakeSession(document, max_version=1)

    def fail_parse(*_args, **_kwargs):
        raise DocumentParseError("simulated parse failure")

    monkeypatch.setattr(
        "app.services.document_ingestion.parse_document",
        fail_parse,
    )

    result = ingest_document(
        db=db,
        knowledge_base_id=3,
        saved_file=_saved_file(tmp_path),
    )

    assert isinstance(result, DocumentIngestionResult)
    assert result.version.status == "failed"
    assert result.version.error_message == "simulated parse failure"
    assert document.current_version_id == 7


def test_successful_ingestion_switches_current_version_only_after_indexing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    document = _existing_document()
    db = _FakeSession(document, max_version=1)

    monkeypatch.setattr(
        "app.services.document_ingestion.parse_document",
        lambda *_args, **_kwargs: type("Parsed", (), {"text": "indexed text"})(),
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.split_text_by_sentence",
        lambda _text: ["indexed text"],
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.embed_texts",
        lambda texts: [[0.1, 0.2] for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.upsert_chunks",
        lambda **_kwargs: None,
    )

    result = ingest_document(
        db=db,
        knowledge_base_id=3,
        saved_file=_saved_file(tmp_path),
    )

    assert result.version.status == "indexed"
    assert result.version.chunk_count == 1
    assert document.current_version_id == result.version.id


def test_embedding_failure_keeps_previous_current_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    document = _existing_document()
    db = _FakeSession(document, max_version=1)

    monkeypatch.setattr(
        "app.services.document_ingestion.parse_document",
        lambda *_args, **_kwargs: type("Parsed", (), {"text": "new text"})(),
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.split_text_by_sentence",
        lambda _text: ["new text"],
    )

    def fail_embedding(_texts):
        raise EmbeddingError("simulated embedding failure")

    monkeypatch.setattr(
        "app.services.document_ingestion.embed_texts",
        fail_embedding,
    )

    result = ingest_document(
        db=db,
        knowledge_base_id=3,
        saved_file=_saved_file(tmp_path),
    )

    assert result.version.status == "failed"
    assert result.version.error_message == "simulated embedding failure"
    assert document.current_version_id == 7


def test_vector_store_failure_cleans_up_vectors_and_keeps_previous_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    document = _existing_document()
    db = _FakeSession(document, max_version=1)
    deleted_ids: list[str] = []

    monkeypatch.setattr(
        "app.services.document_ingestion.parse_document",
        lambda *_args, **_kwargs: type("Parsed", (), {"text": "new text"})(),
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.split_text_by_sentence",
        lambda _text: ["new text"],
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.embed_texts",
        lambda texts: [[0.1, 0.2] for _ in texts],
    )

    def fail_upsert(**_kwargs):
        raise VectorStoreError("simulated vector store failure")

    monkeypatch.setattr(
        "app.services.document_ingestion.upsert_chunks",
        fail_upsert,
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.delete_vectors",
        lambda vector_ids: deleted_ids.extend(vector_ids),
    )

    result = ingest_document(
        db=db,
        knowledge_base_id=3,
        saved_file=_saved_file(tmp_path),
    )

    assert result.version.status == "failed"
    assert result.version.error_message == "simulated vector store failure"
    assert deleted_ids
    assert document.current_version_id == 7


def test_duplicate_content_does_not_create_version_and_removes_temp_file(
    tmp_path: Path,
) -> None:
    document = _existing_document()
    duplicate_version = DocumentVersion(
        id=7,
        document_id=document.id,
        version_number=1,
        file_sha256="a" * 64,
        storage_path="backend/others/uploads/original.txt",
        file_size=11,
        status="indexed",
        chunk_count=1,
    )

    class _DuplicateSession(_FakeSession):
        def scalar(self, _statement):
            self.scalar_calls += 1
            if self.scalar_calls == 1:
                return self.document
            if self.scalar_calls == 2:
                return duplicate_version
            raise AssertionError("duplicate upload must stop before version creation")

    saved_file = _saved_file(tmp_path)
    db = _DuplicateSession(document, max_version=1)

    result = ingest_document(
        db=db,
        knowledge_base_id=3,
        saved_file=saved_file,
    )

    assert result.duplicate is True
    assert result.version.id == 7
    assert not saved_file.storage_path.exists()
