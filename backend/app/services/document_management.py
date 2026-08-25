from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_version import DocumentVersion
from app.services.vector_store import delete_vectors


class DocumentNotFoundError(Exception):
    pass


class DocumentVersionNotFoundError(Exception):
    pass


class DocumentStorageError(Exception):
    pass


def get_owned_document(
    db: Session,
    knowledge_base_id: int,
    document_id: int,
) -> Document:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.knowledge_base_id
            == knowledge_base_id,
        )
    )

    if document is None:
        raise DocumentNotFoundError

    return document


def list_documents(
    db: Session,
    knowledge_base_id: int,
    page: int,
    page_size: int,
    status_filter: str | None = None,
) -> tuple[list[tuple[Document, DocumentVersion | None]], int]:
    statement = (
        select(Document, DocumentVersion)
        .outerjoin(
            DocumentVersion,
            Document.current_version_id
            == DocumentVersion.id,
        )
        .where(
            Document.knowledge_base_id
            == knowledge_base_id
        )
    )

    if status_filter is not None:
        statement = statement.where(
            DocumentVersion.status == status_filter
        )

    count_statement = select(
        func.count()
    ).select_from(
        statement.subquery()
    )

    total = db.scalar(count_statement) or 0

    rows = list(
        db.execute(
            statement
            .order_by(Document.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )

    return rows, total


def get_document_detail(
    db: Session,
    knowledge_base_id: int,
    document_id: int,
) -> tuple[Document, DocumentVersion | None]:
    document = get_owned_document(
        db,
        knowledge_base_id,
        document_id,
    )

    current_version = None

    if document.current_version_id is not None:
        current_version = db.get(
            DocumentVersion,
            document.current_version_id,
        )

    return document, current_version


def list_document_versions(
    db: Session,
    knowledge_base_id: int,
    document_id: int,
) -> list[DocumentVersion]:
    get_owned_document(
        db,
        knowledge_base_id,
        document_id,
    )

    statement = (
        select(DocumentVersion)
        .where(
            DocumentVersion.document_id
            == document_id
        )
        .order_by(
            DocumentVersion.version_number.desc()
        )
    )

    return list(db.scalars(statement).all())


def get_document_version(
    db: Session,
    knowledge_base_id: int,
    document_id: int,
    version_id: int,
) -> DocumentVersion:
    get_owned_document(
        db,
        knowledge_base_id,
        document_id,
    )

    version = db.scalar(
        select(DocumentVersion).where(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id
            == document_id,
        )
    )

    if version is None:
        raise DocumentVersionNotFoundError

    return version


def _resolve_storage_path(
    storage_path: str,
) -> Path:
    project_root = PROJECT_ROOT.resolve()
    target_path = (
        project_root / storage_path
    ).resolve()

    try:
        target_path.relative_to(project_root)
    except ValueError as error:
        raise DocumentStorageError(
            "Document storage path is outside project root"
        ) from error

    return target_path


def delete_document(
    db: Session,
    knowledge_base_id: int,
    document_id: int,
) -> None:
    document = get_owned_document(
        db,
        knowledge_base_id,
        document_id,
    )

    versions = list(
        db.scalars(
            select(DocumentVersion).where(
                DocumentVersion.document_id
                == document.id
            )
        ).all()
    )

    version_ids = [
        version.id
        for version in versions
    ]

    chunks: list[DocumentChunk] = []

    if version_ids:
        chunks = list(
            db.scalars(
                select(DocumentChunk).where(
                    DocumentChunk.document_version_id.in_(
                        version_ids
                    )
                )
            ).all()
        )

    vector_ids = [
        chunk.vector_id
        for chunk in chunks
    ]

    # 先清理 Chroma，避免 MySQL 删除后失去 vector_id。
    delete_vectors(vector_ids)

    # 再删除原始文件。
    for version in versions:
        file_path = _resolve_storage_path(
            version.storage_path
        )
        file_path.unlink(missing_ok=True)

    # 最后删除 MySQL 业务数据。
    db.delete(document)
    db.commit()