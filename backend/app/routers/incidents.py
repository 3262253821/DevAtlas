import json
from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from starlette.responses import Response, StreamingResponse

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.incident import (
    IncidentCitationResponse,
    IncidentDetail,
    IncidentListResponse,
    IncidentStreamRequest,
    IncidentSummary,
)
from app.services.incident import (
    IncidentNotFoundError,
    create_incident,
    delete_incident,
    get_incident_detail,
    list_incidents,
    mark_incident_cancelled,
    mark_incident_completed,
    mark_incident_failed,
)
from app.services.knowledge_base import (
    KnowledgeBaseNotFoundError,
    get_knowledge_base,
)
from app.services.llm import (
    LLMServiceError,
    build_incident_messages,
    stream_chat_with_llm,
)
from app.services.retrieval import (
    RetrievalError,
    retrieve_context,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["incidents"],
)


VALID_INCIDENT_STATUSES = {
    "streaming",
    "completed",
    "failed",
    "cancelled",
}


def _sse_event(
    event_name: str,
    data: dict[str, object],
) -> str:
    """
    生成标准 SSE 事件。
    """
    return (
        f"event: {event_name}\n"
        f"data: "
        f"{json.dumps(data, ensure_ascii=False)}\n\n"
    )


def _summary(incident) -> IncidentSummary:
    """
    把 ORM Incident 对象转换成列表摘要。
    """
    return IncidentSummary(
        id=incident.id,
        knowledge_base_id=incident.knowledge_base_id,
        title=incident.title,
        status=incident.status,
        model_name=incident.model_name,
        created_at=incident.created_at,
        completed_at=incident.completed_at,
    )


def _verify_knowledge_base(
    db: Session,
    current_user: User,
    knowledge_base_id: int,
) -> None:
    """
    验证当前用户是否拥有目标知识库。
    """
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
    "/knowledge-bases/{knowledge_base_id}/incidents/stream",
)
def stream_incident_analysis(
    knowledge_base_id: int,
    data: IncidentStreamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    _verify_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
    )

    incident = create_incident(
        db=db,
        owner_id=current_user.id,
        knowledge_base_id=knowledge_base_id,
        title=data.title,
        input_content=data.content,
    )

    try:
        retrieval_result = retrieve_context(
            db=db,
            knowledge_base_id=knowledge_base_id,
            question=(
                f"{data.title}\n"
                f"{data.content}"
            ),
            top_k=5,
        )

    except RetrievalError as error:
        mark_incident_failed(
            incident.id,
            str(error),
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge retrieval failed",
        )

    messages = build_incident_messages(
        title=data.title,
        input_content=data.content,
        context=retrieval_result.context,
    )

    def event_stream() -> Iterator[str]:
        if not retrieval_result.sources:
            answer = (
                "当前知识库中没有检索到与该故障相关的内容，"
                "暂时无法提供有依据的分析。"
            )

            mark_incident_completed(
                incident.id,
                answer,
                [],
            )

            yield _sse_event(
                "token",
                {
                    "text": answer,
                },
            )

            yield _sse_event(
                "done",
                {
                    "incident_id": incident.id,
                    "status": "completed",
                },
            )

            return

        result_parts: list[str] = []

        try:
            for token in stream_chat_with_llm(messages):
                result_parts.append(token)

                yield _sse_event(
                    "token",
                    {
                        "text": token,
                    },
                )

            result = "".join(
                result_parts
            ).strip()

            mark_incident_completed(
                incident.id,
                result,
                retrieval_result.sources,
            )

            for index, source in enumerate(
                retrieval_result.sources,
                start=1,
            ):
                yield _sse_event(
                    "citation",
                    {
                        "index": index,
                        "document_id": source.document_id,
                        "version_id": source.version_id,
                        "version_number": (
                            source.version_number
                        ),
                        "chunk_index": source.chunk_index,
                        "filename": source.filename,
                        "distance": source.distance,
                    },
                )

            yield _sse_event(
                "done",
                {
                    "incident_id": incident.id,
                    "status": "completed",
                },
            )

        except GeneratorExit:
            mark_incident_cancelled(
                incident.id
            )
            return

        except LLMServiceError as error:
            mark_incident_failed(
                incident.id,
                str(error),
            )

            yield _sse_event(
                "error",
                {
                    "code": "LLM_SERVICE_ERROR",
                    "message": "大模型服务暂时不可用",
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


@router.get(
    "/incidents",
    response_model=IncidentListResponse,
)
def get_incident_list(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IncidentListResponse:
    if (
        status_filter is not None
        and status_filter
        not in VALID_INCIDENT_STATUSES
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid incident status",
        )

    items, total = list_incidents(
        db=db,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )

    return IncidentListResponse(
        items=[
            _summary(item)
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentDetail,
)
def get_incident(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IncidentDetail:
    try:
        incident, citations = get_incident_detail(
            db,
            current_user.id,
            incident_id,
        )

    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return IncidentDetail(
        **_summary(incident).model_dump(),
        owner_id=incident.owner_id,
        input_content=incident.input_content,
        result=incident.result,
        error_message=incident.error_message,
        citations=[
            IncidentCitationResponse(
                citation_index=citation.citation_index,
                document_chunk_id=(
                    citation.document_chunk_id
                ),
            )
            for citation in citations
        ],
    )


@router.delete(
    "/incidents/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_incident(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_incident(
            db,
            current_user.id,
            incident_id,
        )

    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )