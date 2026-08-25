from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.file_security import (
    InvalidFilenameError,
    UnsupportedFileTypeError,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentReindexResponse,
    DocumentUploadResponse,
    DocumentVersionSummary,
)
from app.services.document_ingestion import ingest_document
from app.services.document_management import (
    DocumentNotFoundError,
    DocumentStorageError,
    DocumentVersionNotFoundError,
    delete_document as delete_document_record,
    get_document_detail,
    get_document_version,
    list_document_versions,
    list_documents,
)
from app.services.document_reindex import (
    ReindexNotAllowedError,
    reindex_document,
)
from app.services.file_storage import (
    EmptyFileError,
    FileTooLargeError,
    save_uploaded_file,
)
from app.services.knowledge_base import (
    KnowledgeBaseNotFoundError,
    get_knowledge_base,
)


router = APIRouter(
    prefix="/api/v1/knowledge-bases",
    tags=["documents"],
)


VALID_VERSION_STATUSES = {
    "pending",
    "indexed",
    "failed",
}


def _version_summary(
    version,
) -> DocumentVersionSummary | None:
    if version is None:
        return None

    return DocumentVersionSummary(
        id=version.id,
        version_number=version.version_number,
        file_sha256=version.file_sha256,
        file_size=version.file_size,
        status=version.status,
        error_message=version.error_message,
        chunk_count=version.chunk_count,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def _verify_knowledge_base(
    db: Session,
    current_user: User,
    knowledge_base_id: int,
) -> None:
    try:
        get_knowledge_base(
            db,
            current_user.id,
            knowledge_base_id,
        )
    except KnowledgeBaseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )


@router.post(
    "/{knowledge_base_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: int,
    response: Response,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    _verify_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
    )

    try:
        # 保存上传的文件到存储系统并计算SHA256哈希值
        saved_file = await save_uploaded_file(file)

    except UnsupportedFileTypeError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(error),
        )

    except FileTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(error),
        )

    except EmptyFileError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )

    except InvalidFilenameError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )

    # 编排 T07 和 T08
    result = ingest_document(
        db=db,
        knowledge_base_id=knowledge_base_id,
        saved_file=saved_file,
    )

    if result.duplicate:
        response.status_code = status.HTTP_200_OK

    return DocumentUploadResponse(
        id=result.document.id,
        knowledge_base_id=result.document.knowledge_base_id,
        filename=result.document.original_filename,
        file_type=result.document.file_type,
        file_size=result.version.file_size,
        status=result.version.status,
        version_number=result.version.version_number,
        chunk_count=result.version.chunk_count,
        duplicate=result.duplicate,
        error_message=result.version.error_message,
        created_at=result.version.created_at,
    )


@router.get(
    "/{knowledge_base_id}/documents",
    response_model=DocumentListResponse,
)
def get_documents(
    knowledge_base_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    _verify_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
    )

    if (
        status_filter is not None
        and status_filter not in VALID_VERSION_STATUSES
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid document status",
        )

    rows, total = list_documents(
        db=db,
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )

    items = [
        DocumentListItem(
            id=document.id,
            knowledge_base_id=document.knowledge_base_id,
            filename=document.original_filename,
            file_type=document.file_type,
            current_version=_version_summary(
                version
            ),
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        for document, version in rows
    ]

    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{knowledge_base_id}/documents/{document_id}",
    response_model=DocumentDetailResponse,
)
def get_document(
    knowledge_base_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDetailResponse:
    _verify_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
    )

    try:
        document, version = get_document_detail(
            db,
            knowledge_base_id,
            document_id,
        )
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentDetailResponse(
        id=document.id,
        knowledge_base_id=document.knowledge_base_id,
        filename=document.original_filename,
        file_type=document.file_type,
        current_version=_version_summary(
            version
        ),
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get(
    "/{knowledge_base_id}/documents/{document_id}/versions",
    response_model=list[DocumentVersionSummary],
)
def get_versions(
    knowledge_base_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentVersionSummary]:
    _verify_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
    )

    try:
        versions = list_document_versions(
            db,
            knowledge_base_id,
            document_id,
        )
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return [
        _version_summary(version)
        for version in versions
    ]


@router.get(
    "/{knowledge_base_id}/documents/{document_id}/versions/{version_id}",
    response_model=DocumentVersionSummary,
)
def get_version(
    knowledge_base_id: int,
    document_id: int,
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentVersionSummary:
    _verify_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
    )

    try:
        version = get_document_version(
            db,
            knowledge_base_id,
            document_id,
            version_id,
        )
    except (
        DocumentNotFoundError,
        DocumentVersionNotFoundError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found",
        )

    return _version_summary(version)


@router.delete(
    "/{knowledge_base_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_document(
    knowledge_base_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    _verify_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
    )

    try:
        delete_document_record(
            db,
            knowledge_base_id,
            document_id,
        )
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except DocumentStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{knowledge_base_id}/documents/{document_id}/reindex",
    response_model=DocumentReindexResponse,
)
def reindex(
    knowledge_base_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentReindexResponse:
    _verify_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
    )

    try:
        version = reindex_document(
            db,
            knowledge_base_id,
            document_id,
        )
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except ReindexNotAllowedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    return DocumentReindexResponse(
        document_id=document_id,
        version_id=version.id,
        version_number=version.version_number,
        status=version.status,
        chunk_count=version.chunk_count,
        error_message=version.error_message,
    )