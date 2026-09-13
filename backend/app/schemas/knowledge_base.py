from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# 知识库创建请求模型
class KnowledgeBaseCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )

# 知识库公开模型模型
class KnowledgeBasePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime