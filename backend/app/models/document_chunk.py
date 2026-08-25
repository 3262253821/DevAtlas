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

    document_version_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "document_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        LONGTEXT(),
        nullable=False,
    )

    vector_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    page_number: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    char_start: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

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