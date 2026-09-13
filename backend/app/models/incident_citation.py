from datetime import datetime

from sqlalchemy import ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IncidentCitation(Base):
    __tablename__ = "incident_citations"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    # 关联的事件ID
    incident_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 关联的文档切片ID
    document_chunk_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 关联的文档切片在事件中的序号
    citation_index: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "incident_id",
            "citation_index",
            name="uq_incident_citations_index",
        ),
        Index(
            "ix_incident_citations_chunk",
            "document_chunk_id",
        ),
    )