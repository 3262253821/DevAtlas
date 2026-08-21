from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

# 密码哈希器, 使用argon2算法
password_hash = PasswordHash.recommended()

# 使用HS256算法，即生成Token和验证Token时使用同一个密钥，即JWT_SECRET_KEY
JWT_ALGORITHM = "HS256"
# 访问令牌过期时间为60分钟
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 密码哈希函数，将密码转换为哈希值，用于存储在数据库中
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# 密码验证函数，用于验证用户输入的密码是否与存储在数据库中的哈希值匹配，返回True或False
def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )

# create_access_token函数：创建JWT
# 用户登录后，创建JWT访问令牌，包含用户ID和过期时间
# subject通常表示用户ID，用于标识当前登录的用户，user_id
def create_access_token(
    subject: str,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    # 检查JWT密钥是否配置
    # 如果未配置，抛出RuntimeError异常
    settings.require("jwt_secret_key")

    # now 表示当前utc时间，统一使用UTC时间，避免服务器和用户时间区差异导致的过期时间错误
    now = datetime.now(timezone.utc)
    # 计算过期时间为，当前时间加上过期时间间隔
    expire_at = now + timedelta(minutes=expires_minutes)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire_at,
    }
    # 最终返回JWT访问令牌，即jwt字符串
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=JWT_ALGORITHM,
    )

# decode_access_token函数：解析JWT
# 用于验证JWT访问令牌，返回包含的用户ID
# 如果令牌无效，抛出ValueError异常
def decode_access_token(token: str) -> dict:
    settings.require("jwt_secret_key")

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
        )
    except InvalidTokenError as error:
        raise ValueError("Invalid access token") from error

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        raise ValueError("Token subject is missing")

    return payload