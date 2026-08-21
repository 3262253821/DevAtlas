from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# 注册请求模型
class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
    )
    password: str = Field(
        min_length=8,
        max_length=128,
    )

# 登录请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

# 用户公开信息模型
class UserPublic(BaseModel):
    # 表示它可以从 SQLAlchemy ORM 对象读取字段值
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

# 访问令牌响应模型
class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserPublic