from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.file_security import normalize_filename
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_version import DocumentVersion
from app.services.document_parser import (
    DocumentParseError,
    parse_document,
)
from app.services.embedding import (
    EmbeddingError,
    embed_texts,
)
from app.services.file_storage import SavedFile
from app.services.text_splitter import (
    InvalidChunkConfigError,
    split_text_by_sentence,
)
from app.services.vector_store import (
    VectorStoreError,
    build_vector_id,
    delete_vectors,
    upsert_chunks,
)


@dataclass(frozen=True)
class DocumentIngestionResult:
    document: Document
    version: DocumentVersion
    duplicate: bool


def _relative_storage_path(file_path: Path) -> str:
    """
    数据库只保存项目根目录下的相对路径，
    不把本机绝对路径暴露给 API。
    """
    try:
        return file_path.resolve().relative_to(
            PROJECT_ROOT.resolve()
        ).as_posix()
    except ValueError:
        return file_path.as_posix()


def _delete_duplicate_file(
    saved_file: SavedFile,
) -> None:
    """
    重复内容不需要保留新文件。
    """
    saved_file.storage_path.unlink(
        missing_ok=True
    )


def _build_chunk_metadata(
    *,
    knowledge_base_id: int,
    document_id: int,
    version_id: int,
    version_number: int,
    filename: str,
    chunk_count: int,
) -> list[dict[str, int | str | bool | None]]:
    return [
        {
            "knowledge_base_id": knowledge_base_id,
            "document_id": document_id,
            "document_version_id": version_id,
            "version_number": version_number,
            "chunk_index": index,
            "source_filename": filename,
            "page_number": None,
            "is_searchable": True,
        }
        for index in range(chunk_count)
    ]


def ingest_document(
    db: Session,
    knowledge_base_id: int,
    saved_file: SavedFile,
) -> DocumentIngestionResult:
    """
    把 T06 保存成功的文件接入 T07/T08 文档处理流程。
    """
    normalized_filename = normalize_filename(
        saved_file.original_filename
    ).casefold()

    document = db.scalar(
        # 先查找逻辑文档
        select(Document).where(
            Document.knowledge_base_id
            == knowledge_base_id,
            Document.normalized_filename
            == normalized_filename,
        )
    )

    if document is not None:
        duplicate_version = db.scalar(
            # 检查是否有相同文件 SHA256 的版本
            select(DocumentVersion).where(
                DocumentVersion.document_id
                == document.id,
                DocumentVersion.file_sha256
                == saved_file.file_sha256,
            )
        )

        if duplicate_version is not None:
            _delete_duplicate_file(saved_file)

            return DocumentIngestionResult(
                document=document,
                version=duplicate_version,
                duplicate=True,
            )

    if document is None:
        document = Document(
            knowledge_base_id=knowledge_base_id,
            original_filename=saved_file.original_filename,
            normalized_filename=normalized_filename,
            file_type=saved_file.file_type,
        )
        db.add(document)
        db.flush()

    max_version_number = db.scalar(
        select(
            func.max(
                DocumentVersion.version_number
            )
        ).where(
            DocumentVersion.document_id
            == document.id
        )
    )

    version = DocumentVersion(
        document_id=document.id,
        version_number=(max_version_number or 0) + 1,
        file_sha256=saved_file.file_sha256,
        storage_path=_relative_storage_path(
            saved_file.storage_path
        ),
        file_size=saved_file.file_size,
        status="pending",
        chunk_count=0,
    )

    db.add(version)
    # flush是为了确保 version.id 被分配值
    db.flush()

    document_id = document.id
    version_id = version.id
    version_number = version.version_number

    # 先提交 pending 版本。
    # 这样后续 Embedding 或 Chroma 失败时，
    # 仍然可以保留 failed 记录。
    db.commit()

    vector_ids: list[str] = []

    try:
        parsed_document = parse_document(
            saved_file.storage_path,
            saved_file.file_type,
        )

        chunks = split_text_by_sentence(
            parsed_document.text
        )

        if not chunks:
            raise DocumentParseError(
                "Document produced no chunks"
            )

        # 生成文档块的向量表示
        embeddings = embed_texts(chunks)
        # 生成文档块的 vector_id
        # 每个 vector_id 都是唯一的，用于后续的检索
        vector_ids = [
            build_vector_id(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
                version_id=version_id,
                chunk_index=index,
            )
            for index in range(len(chunks))
        ]
        # 生成文档块的 metadata
        metadatas = _build_chunk_metadata(
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            version_id=version_id,
            version_number=version_number,
            filename=saved_file.original_filename,
            chunk_count=len(chunks),
        )
        # 把文档块、向量和 metadata 一起写入 Chroma
        upsert_chunks(
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            version_id=version_id,
            chunks=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        # 把文档块写入 MySQL
        db.add_all(
            [
                DocumentChunk(
                    document_version_id=version_id,
                    chunk_index=index,
                    content=chunk,
                    vector_id=vector_ids[index],
                )
                for index, chunk in enumerate(chunks)
            ]
        )

        current_version = db.get(
            DocumentVersion,
            version_id,
        )
        current_document = db.get(
            Document,
            document_id,
        )

        if current_version is None:
            raise DocumentParseError(
                "Document version disappeared"
            )

        if current_document is None:
            raise DocumentParseError(
                "Document disappeared"
            )

        current_version.chunk_count = len(chunks)
        # 更新版本状态为 indexed
        current_version.status = "indexed"
        current_version.error_message = None
        current_document.current_version_id = version_id

        db.commit()

        return DocumentIngestionResult(
            document=current_document,
            version=current_version,
            duplicate=False,
        )

    except (
        DocumentParseError,
        InvalidChunkConfigError,
        EmbeddingError,
        VectorStoreError,
    ) as error:
        db.rollback()

        # MySQL 和 Chroma 不是同一个事务系统。
        # MySQL 失败时，要删除已经写入的向量。
        if vector_ids:
            try:
                delete_vectors(vector_ids)
            except VectorStoreError:
                # 保留主失败状态，清理失败留给日志和后续补偿。
                pass

        failed_version = db.get(
            DocumentVersion,
            version_id,
        )
        # 失败补偿,更新版本状态为 failed
        if failed_version is not None:
            failed_version.status = "failed"
            failed_version.error_message = str(error)[:2000]
            failed_version.chunk_count = 0
            db.commit()

        failed_document = db.get(
            Document,
            document_id,
        )

        if failed_document is None:
            raise

        return DocumentIngestionResult(
            document=failed_document,
            version=failed_version,
            duplicate=False,
        )