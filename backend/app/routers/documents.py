from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
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
from app.schemas.document_upload import FileUploadResponse
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
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileUploadResponse:
    # 先校验当前用户是否拥有这个知识库
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

    return FileUploadResponse(
        original_filename=saved_file.original_filename,
        stored_filename=saved_file.stored_filename,
        file_type=saved_file.file_type,
        file_size=saved_file.file_size,
        file_sha256=saved_file.file_sha256,
    )