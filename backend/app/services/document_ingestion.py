from dataclasses import dataclass
import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.file_security import normalize_filename
from app.core.statuses import (
    DOCUMENT_VERSION_FAILED,
    DOCUMENT_VERSION_INDEXED,
    DOCUMENT_VERSION_PENDING,
)
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


logger = logging.getLogger(__name__)


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


# 命名约定,_build_ 前面的下划线表示 这是模块内部使用的辅助函数,不建议其他模块直接调用
def _build_chunk_metadata(
    # 这里的 * 表示后面的参数必须通过“参数名”传入
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

    logger.info(
        "document_ingestion_started kb_id=%s filename=%s",
        knowledge_base_id,
        saved_file.original_filename,
    )

    # 文件名规范化
    normalized_filename = normalize_filename(
        saved_file.original_filename
    ).casefold()

    # 先查找逻辑文档
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
            # 通过SHA-256检查是否有相同文件的版本
            # 这样可以避免重复导入相同文件
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
                # 如果找到相同版本，将duplicate=True返回给前端
                duplicate=True,
            )

    # 如果是新内容，创建新文档
    if document is None:
        document = Document(
            knowledge_base_id=knowledge_base_id,
            original_filename=saved_file.original_filename,
            normalized_filename=normalized_filename,
            file_type=saved_file.file_type,
        )
        db.add(document)
        # flush()会把当前对象同步到数据库，让数据库生成自增 ID，但还没有真正提交事务
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

    # 创建新版本
    # 每个版本的 version_number 都是唯一的，用于后续的检索
    # 每个版本的 chunk_count 都是 0，因为新版本还没有被解析
    version = DocumentVersion(
        document_id=document.id,
        version_number=(max_version_number or 0) + 1,
        file_sha256=saved_file.file_sha256,
        storage_path=_relative_storage_path(
            saved_file.storage_path
        ),
        file_size=saved_file.file_size,
        status=DOCUMENT_VERSION_PENDING,
        chunk_count=0,
    )

    db.add(version)
    # flush是为了确保 version.id 被分配值
    db.flush()

    document_id = document.id
    version_id = version.id
    version_number = version.version_number

    # 项目不是先完成全部解析和向量化，最后才创建数据库记录
    # 而是先创建版本记录，状态设为pending，再提交，在执行解析、切分、Embedding、Chroma 写入
    # 这里故意不提前切换 current_version_id：只有新版本完整处理成功后，
    # 才能替换旧的可检索版本，失败时旧版本仍然保持可用。
    db.commit()

    vector_ids: list[str] = []

    try:
        # 解析文档
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
        # 每个 vector_id 都是唯一的，对应一个文档块的向量表示
        # 这份id是用于MySQL的 DocumentChunk.vector_id,失败时调用delete_vectors(vector_ids) 清理 Chroma
        vector_ids = [
            build_vector_id(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
                version_id=version_id,
                chunk_index=index,
            )
            for index in range(len(chunks))
        ]
        # 生成文档块的 metadata,相当于是文档块的元数据，用于后续的检索
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

        # 更新版本记录
        current_version = db.get(
            DocumentVersion,
            version_id,
        )
        # 更新文档记录
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
        current_version.status = DOCUMENT_VERSION_INDEXED
        current_version.error_message = None
        current_document.current_version_id = version_id

        # 这才是真正提交事务，确保所有操作都成功
        db.commit()

        logger.info(
            "document_ingestion_indexed kb_id=%s document_id=%s version_id=%s chunks=%s",
            knowledge_base_id,
            document_id,
            version_id,
            len(chunks),
        )

        return DocumentIngestionResult(
            document=current_document,
            version=current_version,
            duplicate=False,
        )

    except Exception as error:
    # 如果出现异常,回滚事务,仅针对MySQL操作
        db.rollback()

        # MySQL 和 Chroma 不是同一个事务系统。
        # 如果失败发生在Chroma写入之后,就需要删掉刚刚写入的向量,否则会出现Chroma中有向量而MySQL中没有对应的chunk记录
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
            failed_version.status = DOCUMENT_VERSION_FAILED
            # [:2000]表示最多存储2000个字符,超过部分截断
            failed_version.error_message = str(error)[:2000]
            failed_version.chunk_count = 0
            db.commit()

        logger.exception(
            "document_ingestion_failed kb_id=%s document_id=%s version_id=%s",
            knowledge_base_id,
            document_id,
            version_id,
        )

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
