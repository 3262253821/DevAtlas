from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    knowledge_base_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        # ForeignKey：外键约束，引用 knowledge_bases 表的 id 字段，一个知识库可以有多个文档
        # ondelete="CASCADE" 表示当知识库被删除时，所有关联的文档也会被删除
        ForeignKey(
            "knowledge_bases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    # 原始文件名
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    # 经过规范化处理的文件名
    normalized_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    # 文件类型
    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    # 当前这个逻辑文档，哪一个版本正在生效
    # ForeignKey：外键约束，引用 document_versions 表的 id 字段，一个文档可以有多个版本
    # ondelete="SET NULL" 表示当文档版本被删除时，将当前版本ID设置为 NULL
    current_version_id: Mapped[int | None] = mapped_column(  
        BIGINT(unsigned=True),
        ForeignKey(
            "document_versions.id",
            ondelete="SET NULL",
        ),
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

    __table_args__ = (
        # 表示同一个知识库中不能出现两个同名逻辑文档
        UniqueConstraint(
            "knowledge_base_id",
            "normalized_filename",
            name="uq_documents_knowledge_base_filename",
        ),
        Index(
            "ix_documents_knowledge_base_updated",
            "knowledge_base_id",
            "updated_at",
        ),
    )