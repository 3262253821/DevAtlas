from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)


class UsernameAlreadyExistsError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class InactiveUserError(Exception):
    pass

# 注册用户
def register_user(
    db: Session,
    data: RegisterRequest,
) -> User:
    existing_user = db.scalar(
        select(User).where(User.username == data.username)
    )

    if existing_user is not None:
        raise UsernameAlreadyExistsError

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UsernameAlreadyExistsError

    db.refresh(user)

    return user

# 认证用户
def authenticate_user(
    db: Session,
    data: LoginRequest,
) -> User:
    user = db.scalar(
        select(User).where(User.username == data.username)
    )

    if user is None:
        raise AuthenticationError

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise AuthenticationError

    if not user.is_active:
        raise InactiveUserError

    return user

# 构建访问令牌响应
def build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    )