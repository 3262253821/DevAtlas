from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_version import DocumentVersion
from app.services.document_ingestion import (
    _build_chunk_metadata,
)
from app.services.document_management import (
    get_owned_document,
    _resolve_storage_path,
)
from app.services.document_parser import (
    DocumentParseError,
    parse_document,
)
from app.services.embedding import (
    EmbeddingError,
    embed_texts,
)
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


class ReindexNotAllowedError(Exception):
    pass


def reindex_document(
    db: Session,
    knowledge_base_id: int,
    document_id: int,
) -> DocumentVersion:
    document = get_owned_document(
        db,
        knowledge_base_id,
        document_id,
    )

    # 选择该文档最新的 failed 版本。
    version = db.scalar(
        select(DocumentVersion)
        .where(
            DocumentVersion.document_id
            == document.id,
            DocumentVersion.status == "failed",
        )
        .order_by(
            desc(DocumentVersion.version_number)
        )
    )

    if version is None:
        raise ReindexNotAllowedError(
            "No failed version is available for reindex"
        )

    file_path = _resolve_storage_path(
        version.storage_path
    )

    old_chunks = list(
        db.scalars(
            select(DocumentChunk).where(
                DocumentChunk.document_version_id
                == version.id
            )
        ).all()
    )

    old_vector_ids = [
        chunk.vector_id
        for chunk in old_chunks
    ]

    # 重新索引前清理该版本可能残留的旧向量和 chunk。
    delete_vectors(old_vector_ids)

    db.execute(
        delete(DocumentChunk).where(
            DocumentChunk.document_version_id
            == version.id
        )
    )

    version.status = "pending"
    version.error_message = None
    version.chunk_count = 0
    document.current_version_id = version.id

    db.commit()

    vector_ids: list[str] = []

    try:
        parsed_document = parse_document(
            file_path,
            document.file_type,
        )

        chunks = split_text_by_sentence(
            parsed_document.text
        )

        if not chunks:
            raise DocumentParseError(
                "Document produced no chunks"
            )

        embeddings = embed_texts(chunks)

        vector_ids = [
            build_vector_id(
                knowledge_base_id=knowledge_base_id,
                document_id=document.id,
                version_id=version.id,
                chunk_index=index,
            )
            for index in range(len(chunks))
        ]

        metadatas = _build_chunk_metadata(
            knowledge_base_id=knowledge_base_id,
            document_id=document.id,
            version_id=version.id,
            version_number=version.version_number,
            filename=document.original_filename,
            chunk_count=len(chunks),
        )

        upsert_chunks(
            knowledge_base_id=knowledge_base_id,
            document_id=document.id,
            version_id=version.id,
            chunks=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        db.add_all(
            [
                DocumentChunk(
                    document_version_id=version.id,
                    chunk_index=index,
                    content=chunk,
                    vector_id=vector_ids[index],
                )
                for index, chunk in enumerate(chunks)
            ]
        )

        version.chunk_count = len(chunks)
        version.status = "indexed"
        version.error_message = None

        db.commit()

    except (
        DocumentParseError,
        InvalidChunkConfigError,
        EmbeddingError,
        VectorStoreError,
    ) as error:
        db.rollback()

        if vector_ids:
            try:
                delete_vectors(vector_ids)
            except VectorStoreError:
                pass

        failed_version = db.get(
            DocumentVersion,
            version.id,
        )

        if failed_version is None:
            raise

        failed_version.status = "failed"
        failed_version.error_message = str(error)[:2000]
        failed_version.chunk_count = 0

        db.commit()

        version = failed_version

    return version