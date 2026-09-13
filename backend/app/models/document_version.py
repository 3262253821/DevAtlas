from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER, CHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    # 文档ID
    # ForeignKey：外键约束，引用 documents 表的 id 字段，一个文档可以有多个版本
    # ondelete="CASCADE" 表示当文档被删除时，所有关联的文档版本也会被删除
    document_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
    )
    # 文件SHA256哈希值
    file_sha256: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
    )
    # 存储路径
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    # 文件大小
    file_size: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        nullable=False,
    )
    # pending  → 等待处理
    # indexed  → 已完成切分、向量化和入库
    # failed   → 处理失败   
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # 分块数量
    chunk_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
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
        # 表示同一个文档不能有两个相同的 version_number
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_versions_number",
        ),
        # 靠唯一约束去重：同内容再传，直接返回已有版本，不产生新版本
        UniqueConstraint(
            "document_id",
            "file_sha256",
            name="uq_document_versions_sha256",
        ),
        Index(
            "ix_document_versions_document_status",
            "document_id",
            "status",
        ),
    )