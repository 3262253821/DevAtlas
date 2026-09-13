from datetime import datetime

from sqlalchemy import Boolean, String, func
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        # BIGINT(unsigned=True) 表示无符号整数，用于存储用户ID
        BIGINT(unsigned=True),
        primary_key=True,
        # autoincrement=True 表示数据库会自动为每个新记录生成一个唯一的ID
        autoincrement=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        # default：SQLAlchemy 在 Python 代码层面提供默认值
        default="user",
        # server_default：数据库 MySQL 自己提供默认值
        server_default="user",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )