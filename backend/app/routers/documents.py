from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
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
from app.schemas.document import DocumentUploadResponse
from app.services.document_ingestion import ingest_document
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
    # 先校验当前用户是否拥有这个知识库。
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
    # 编排 T07
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
        file_type=result.version.storage_path.rsplit(
            ".",
            maxsplit=1,
        )[-1],
        file_size=result.version.file_size,
        status=result.version.status,
        version_number=result.version.version_number,
        chunk_count=result.version.chunk_count,
        duplicate=result.duplicate,
        error_message=result.version.error_message,
        created_at=result.version.created_at,
    )