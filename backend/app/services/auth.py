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
    # 检查用户名是否已存在
    # 如果存在，抛出异常 UsernameAlreadyExistsError
    existing_user = db.scalar(
        select(User).where(User.username == data.username)
    )

    if existing_user is not None:
        raise UsernameAlreadyExistsError

    # 创建用户对象，密码进行哈希处理，默认是active用户
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

    # 刷新用户对象，确保返回的是最新的数据库状态
    # 重新从数据库读取对象，让自增 ID、创建时间等字段更新到 Python 对象中
    db.refresh(user)

    return user

# 认证用户
def authenticate_user(
    db: Session,
    data: LoginRequest,
) -> User:
    # 根据用户名查询用户
    # 如果用户不存在，抛出异常 AuthenticationError
    user = db.scalar(
        select(User).where(User.username == data.username)
    )

    if user is None:
        raise AuthenticationError

    # 验证密码是否匹配
    # 如果密码不匹配，抛出异常 AuthenticationError
    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise AuthenticationError

    # 检查用户是否已激活
    # 如果未激活，抛出异常 InactiveUserError
    if not user.is_active:
        raise InactiveUserError

    return user

# 构建访问令牌响应
def build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        # 访问令牌过期时间，单位：秒
        # 配置里是 60 分钟，但接口返回的是秒，所以是：60min * 60s
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    )