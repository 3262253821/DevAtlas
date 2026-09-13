from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.retrieval import (
    RetrievedSource,
    RetrievalRequest,
    RetrievalResponse,
)
from app.services.knowledge_base import (
    KnowledgeBaseNotFoundError,
    get_knowledge_base,
)
from app.services.retrieval import RetrievalError
from app.services.langchain_rag import retrieve_context_with_langchain


router = APIRouter(
    prefix="/api/v1/knowledge-bases",
    tags=["retrieval"],
)


@router.post(
    "/{knowledge_base_id}/search",
    response_model=RetrievalResponse,
)
def search_knowledge_base(
    knowledge_base_id: int,
    data: RetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RetrievalResponse:
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

    # Pydantic 的 min_length 只能判断字符串长度，不能拦截全是空格的问题。
    if not data.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty",
        )

    try:
        result = retrieve_context_with_langchain(
            db=db,
            knowledge_base_id=knowledge_base_id,
            question=data.question,
            top_k=data.top_k,
        )
    except RetrievalError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        )

    return RetrievalResponse(
        question=data.question,
        context=result.context,
        sources=[
            RetrievedSource(
                document_id=source.document_id,
                version_id=source.version_id,
                version_number=source.version_number,
                chunk_index=source.chunk_index,
                filename=source.filename,
                content=source.content,
                distance=source.distance,
                page_number=source.page_number,
            )
            for source in result.sources
        ],
    )
