from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBasePublic,
)
from app.services.knowledge_base import (
    DuplicateKnowledgeBaseError,
    KnowledgeBaseNotFoundError,
    create_knowledge_base,
    delete_knowledge_base,
    get_knowledge_base,
    list_knowledge_bases,
)


router = APIRouter(
    prefix="/api/v1/knowledge-bases",
    tags=["knowledge-bases"],
)

# 创建知识库, 仅返回用户创建的知识库
@router.post(
    "",
    response_model=KnowledgeBasePublic,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeBase:
    try:
        return create_knowledge_base(
            db,
            current_user.id,
            data,
        )
    except DuplicateKnowledgeBaseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Knowledge base name already exists",
        )

# 获取用户所有知识库, 仅返回用户创建的知识库
@router.get(
    "",
    response_model=list[KnowledgeBasePublic],
)
def list_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[KnowledgeBase]:
    return list_knowledge_bases(
        db,
        current_user.id,
    )

# 获取知识库详情, 仅返回用户创建的知识库
@router.get(
    "/{knowledge_base_id}",
    response_model=KnowledgeBasePublic,
)
def get_one(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeBase:
    try:
        return get_knowledge_base(
            db,
            current_user.id,
            knowledge_base_id,
        )
    # 这里返回的是404而不是403,是对当前用户不可见的资源，统一表现为不存在，避免泄露其他用户是否拥有这个资源。
    except KnowledgeBaseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

# 删除知识库
@router.delete(
    "/{knowledge_base_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_knowledge_base(
            db,
            current_user.id,
            knowledge_base_id,
        )
    except KnowledgeBaseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)