from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


# 启动前检查数据库连接是否可用
settings.require("database_url")


# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    # 每次从连接池取连接前，先检查连接是否还活着
    pool_pre_ping=True,
    # 连接使用超过 1800 秒后，允许回收并建立新连接
    pool_recycle=1800,
)

# 创建数据库会话的工厂
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    # 表示事务不会自动提交，通常由代码明确，通常由db.commit()调用
    autocommit=False,
)

# 给每个请求提供 Session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# 数据库连通性检查
def check_database_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True