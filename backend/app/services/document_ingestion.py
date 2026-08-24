from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.file_security import normalize_filename
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.services.document_parser import (
    DocumentParseError,
    parse_document,
)
from app.services.file_storage import SavedFile
from app.services.text_splitter import (
    InvalidChunkConfigError,
    split_text_by_sentence,
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


def _delete_duplicate_file(saved_file: SavedFile) -> None:
    """
    重复内容不需要保留新文件。
    """
    saved_file.storage_path.unlink(
        missing_ok=True
    )


def ingest_document(
    db: Session,
    knowledge_base_id: int,
    saved_file: SavedFile,
) -> DocumentIngestionResult:
    """
    把 T06 保存成功的文件接入 T07 文档处理流程。
    """
    # 规范化文件名
    normalized_filename = normalize_filename(
        saved_file.original_filename
    ).casefold()

    document = db.scalar(
        # 在当前知识库中，找这个规范化文件名对应的逻辑文档
        select(Document).where(
            Document.knowledge_base_id
            == knowledge_base_id,
            Document.normalized_filename
            == normalized_filename,
        )
    )

    if document is not None:
        # 检查是否有重复版本，判断条件是同一个逻辑文件名和相同文件内容
        duplicate_version = db.scalar(
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

    # 第一次上传时，数据库中还没有这个逻辑文档，就创建一个
    if document is None:
        document = Document(
            knowledge_base_id=knowledge_base_id,
            original_filename=saved_file.original_filename,
            normalized_filename=normalized_filename,
            file_type=saved_file.file_type,
        )
        db.add(document)
        # flush() 会把 INSERT 发送给数据库，并取得自增的 document.id，但事务还没有最终提交，
        # 所以这里需要先提交事务，才能使用 document.id
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
    # flush() 会把 INSERT 发送给数据库，并取得自增的 version.id，但事务还没有最终提交，
    # 所以这里需要先提交事务，才能使用 version.id
    db.flush()

    # 当前版本先指向本次处理版本。
    # 默认检索会在后续 T08 只使用 indexed 版本。
    document.current_version_id = version.id

    try:
        # 解析文档内容
        parsed_document = parse_document(
            saved_file.storage_path,
            saved_file.file_type,
        )

        #  切分 chunk
        chunks = split_text_by_sentence(
            parsed_document.text
        )

        if not chunks:
            raise DocumentParseError(
                "Document produced no chunks"
            )

        version.chunk_count = len(chunks)

        # T07 只完成解析和切分。
        # 写入 Embedding/Chroma 后，T08 再更新为 indexed。
        version.status = "pending"
        version.error_message = None

        db.commit()

    except (
        DocumentParseError,
        InvalidChunkConfigError,
    ) as error:
        # 保留失败版本，便于之后查询失败原因和重新处理。
        version.status = "failed"
        version.error_message = str(error)[:2000]
        version.chunk_count = 0

        db.commit()

    return DocumentIngestionResult(
        document=document,
        version=version,
        duplicate=False,
    )