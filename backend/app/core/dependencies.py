from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# Bearer 认证方案,负责读取 HTTP 请求头中的 Authorization 字段
# 例如：Authorization: Bearer eyJ...，然后注入credentials参数
bearer_scheme = HTTPBearer(
    auto_error=False,
)

# 获取当前用户
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        # 表示缺少认证信息时，不让 FastAPI 立刻自动报错，而是交给下面的代码统一处理
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    # 没有token时，返回401错误
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # credentials.scheme 是 "Bearer" 或 "bearer" 都可以接受
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # credentials.credentials 是访问令牌，是Bearer eyJ...，即Bearer后面的jwt字符串
    # 它是 Bearer 认证方案的令牌部分
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # 根据用户 ID 查数据库，返回用户对象
    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # 检查用户是否启用，未启用则返回403错误
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user