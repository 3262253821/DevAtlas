from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    version_number: int
    chunk_count: int
    duplicate: bool
    error_message: str | None
    created_at: datetime


class DocumentVersionSummary(BaseModel):
    id: int
    version_number: int
    file_sha256: str
    file_size: int
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentListItem(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    file_type: str
    current_version: DocumentVersionSummary | None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentListItem]
    total: int
    page: int
    page_size: int


class DocumentDetailResponse(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    file_type: str
    current_version: DocumentVersionSummary | None
    created_at: datetime
    updated_at: datetime


class DocumentReindexResponse(BaseModel):
    document_id: int
    version_id: int
    version_number: int
    status: str
    chunk_count: int
    error_message: str | None