from datetime import datetime

from pydantic import BaseModel, Field


class IncidentStreamRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    content: str = Field(
        min_length=1,
        max_length=20000,
    )


class IncidentCitationResponse(BaseModel):
    citation_index: int
    document_chunk_id: int


class IncidentSummary(BaseModel):
    id: int
    knowledge_base_id: int
    title: str
    status: str
    model_name: str | None
    created_at: datetime
    completed_at: datetime | None


class IncidentDetail(IncidentSummary):
    owner_id: int
    input_content: str
    result: str | None
    error_message: str | None
    citations: list[IncidentCitationResponse]


class IncidentListResponse(BaseModel):
    items: list[IncidentSummary]
    total: int
    page: int
    page_size: int