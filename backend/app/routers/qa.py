import json
from typing import Iterator

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from starlette.responses import (
    Response,
    StreamingResponse,
)
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.qa import (
    QARequest,
    QAResponse,
    QAStreamRequest,
)
from app.schemas.retrieval import RetrievedSource
from app.services.knowledge_base import (
    KnowledgeBaseNotFoundError,
    get_knowledge_base,
)
from app.services.llm import (
    LLMServiceError,
    build_rag_messages,
    chat_with_llm,
    stream_chat_with_llm,
)
from app.services.retrieval import RetrievalError
from app.services.langchain_rag import retrieve_context_with_langchain


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

    # Pydantic 的 min_length 只能判断字符串长度，不能拦截全是空格的问题。
    if not data.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty",
        )

    try:
        retrieval_result = retrieve_context_with_langchain(
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


def _sse_event(
    event_name: str,
    data: dict[str, object],
) -> str:
    """
    生成标准 SSE 事件文本。
    """
    return (
        f"event: {event_name}\n"
        f"data: "
        f"{json.dumps(data, ensure_ascii=False)}\n\n"
    )


# 流式回答问题
@router.post(
    "/{knowledge_base_id}/qa/stream",
)
def stream_question(
    knowledge_base_id: int,
    data: QAStreamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
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

    # 后端再次校验问题是否为空，为了处理传来全是空格问题
    if not data.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty",
        )

    try:
        # 进入真正的检索函数
        retrieval_result = retrieve_context_with_langchain(
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

    messages = None

    if retrieval_result.sources:
        messages = build_rag_messages(
            question=data.question,
            context=retrieval_result.context,
        )

    def event_stream() -> Iterator[str]:
        if not retrieval_result.sources:
            yield _sse_event(
                "token",
                {
                    "text": (
                        "当前知识库中没有检索到"
                        "与该问题相关的内容。"
                    )
                },
            )

            yield _sse_event(
                "done",
                {
                    "conversation_id": (
                        data.conversation_id
                    ),
                    "message_id": None,
                },
            )
            return

        try:
            if messages is None:
                raise LLMServiceError(
                    "RAG messages are unavailable"
                )

            for token in stream_chat_with_llm(
                messages
            ):
                yield _sse_event(
                    "token",
                    {
                        "text": token,
                    },
                )

            for index, source in enumerate(
                retrieval_result.sources,
                start=1,
            ):
                yield _sse_event(
                    "citation",
                    {
                        "index": index,
                        "document_id": (
                            source.document_id
                        ),
                        "version_id": (
                            source.version_id
                        ),
                        "version_number": (
                            source.version_number
                        ),
                        "chunk_index": (
                            source.chunk_index
                        ),
                        "filename": source.filename,
                        "distance": source.distance,
                    },
                )

            yield _sse_event(
                "done",
                {
                    "conversation_id": (
                        data.conversation_id
                    ),
                    "message_id": None,
                },
            )

        except GeneratorExit:
            # 客户端主动断开连接时结束生成器。
            return

        except LLMServiceError:
            yield _sse_event(
                "error",
                {
                    "code": "LLM_SERVICE_ERROR",
                    "message": (
                        "大模型服务暂时不可用"
                    ),
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
