from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.qa import QARequest, QAResponse
from app.schemas.retrieval import RetrievedSource
from app.services.knowledge_base import (
    KnowledgeBaseNotFoundError,
    get_knowledge_base,
)
from app.services.llm import (
    LLMServiceError,
    build_rag_messages,
    chat_with_llm,
)
from app.services.retrieval import (
    RetrievalError,
    retrieve_context,
)


router = APIRouter(
    prefix="/api/v1/knowledge-bases",
    tags=["qa"],
)


@router.post(
    "/{knowledge_base_id}/qa",
    response_model=QAResponse,
)
def answer_question(
    knowledge_base_id: int,
    data: QARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QAResponse:
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
        retrieval_result = retrieve_context(
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

    if not retrieval_result.sources:
        return QAResponse(
            question=data.question,
            answer=(
                "当前知识库中没有检索到与该问题相关的内容。"
            ),
            sources=[],
        )

    messages = build_rag_messages(
        question=data.question,
        context=retrieval_result.context,
    )

    try:
        answer = chat_with_llm(messages)
    except LLMServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        )

    sources = [
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
        for source in retrieval_result.sources
    ]

    return QAResponse(
        question=data.question,
        answer=answer,
        sources=sources,
    )