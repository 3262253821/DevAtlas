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