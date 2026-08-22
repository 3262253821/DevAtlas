from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    # T06 临时响应：T07 接入文档版本后会扩展为正式文档响应
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    file_sha256: str
    status: str = "uploaded"