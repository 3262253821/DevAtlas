from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class RetrievedSource(BaseModel):
    document_id: int
    version_id: int
    version_number: int
    chunk_index: int
    filename: str
    content: str
    distance: float
    page_number: int | None = None


class RetrievalResponse(BaseModel):
    question: str
    context: str
    sources: list[RetrievedSource]