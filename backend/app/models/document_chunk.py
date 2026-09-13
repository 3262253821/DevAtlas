from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import (
    BIGINT,
    DATETIME,
    INTEGER,
    LONGTEXT,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    # 文档版本ID
    # ForeignKey：外键约束，引用 document_versions 表的 id 字段，一个文档版本可以有多个分块
    # ondelete="CASCADE" 表示当文档版本被删除时，所有关联的文档分块也会被删除
    document_version_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "document_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    # 当前切片在版本中的序号
    chunk_index: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
    )
    # 当前切片的内容
    content: Mapped[str] = mapped_column(
        LONGTEXT(),
        nullable=False,
    )
    # Chroma 向量库中的向量 ID
    # 它很关键，作为MySQL和Chroma两个库的关联标识
    # MySQL：保存 chunk 的完整业务信息、原文、版本、页码
    # Chroma：保存向量，用于相似度检索
    vector_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    # 当前切片所在页码
    page_number: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )
    # 当前切片在原文中的起始字符位置
    char_start: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )
    # 当前切片在原文中的结束字符位置
    char_end: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        # 保证同一个版本中不会有两个相同编号的切片
        UniqueConstraint(
            "document_version_id",
            "chunk_index",
            name="uq_document_chunks_version_index",
        ),
        Index(
            "ix_document_chunks_version_index",
            "document_version_id",
            "chunk_index",
        ),
    )