from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    # 谁发起的事件，关联用户表
    owner_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 关联的知识库，用于事件处理
    knowledge_base_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 故障标题
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    # 用户输入的故障信息
    input_content: Mapped[str] = mapped_column(
        LONGTEXT(),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="streaming",
        server_default="streaming",
    )
    # 处理结果
    result: Mapped[str | None] = mapped_column(
        LONGTEXT(),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # 使用的模型名称
    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DATETIME(fsp=6),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_incidents_owner_created",
            "owner_id",
            "created_at",
        ),
        Index(
            "ix_incidents_knowledge_base_created",
            "knowledge_base_id",
            "created_at",
        ),
        Index(
            "ix_incidents_status",
            "status",
        ),
    )