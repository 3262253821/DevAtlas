from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth import (
    AuthenticationError,
    InactiveUserError,
    UsernameAlreadyExistsError,
    authenticate_user,
    build_token_response,
    register_user,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)

# 注册
@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    try:
        return register_user(db, data)
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

# 登录
@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        user = authenticate_user(db, data)
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            # 认证失败，不返回username & password错误，而是返回通用错误，防止进行枚举攻击
            detail="Incorrect username or password",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return build_token_response(user)


@router.get(
    "/me",
    response_model=UserPublic,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user