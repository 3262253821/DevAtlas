from pydantic import BaseModel, Field

from app.schemas.retrieval import RetrievedSource


class QARequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class QAResponse(BaseModel):
    question: str
    answer: str
    sources: list[RetrievedSource]


class QAStreamRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )
    conversation_id: int | None = None