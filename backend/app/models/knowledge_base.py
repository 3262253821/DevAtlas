from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    owner_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        # ForeignKey：外键约束，引用 users 表的 id 字段，一个用户可以创建多个知识库
        # ondelete="CASCADE" 表示当用户被删除时，所有关联的知识库也会被删除
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
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

    # __table_args__：集中定义表级约束和索引
    __table_args__ = (
        # 创建唯一约束，防止重复数据：保证知识库名称在每个用户下是唯一的
        UniqueConstraint(
            "owner_id",
            "name",
            name="uq_knowledge_bases_owner_name",
        ),
        # 创建索引，加快查询
        Index(
            # 索引名称：ix_knowledge_bases_owner_updated
            # 索引字段：owner_id, updated_at
            # 索引类型：BTREE
            "ix_knowledge_bases_owner_updated",
            "owner_id",
            "updated_at",
        ),
    )