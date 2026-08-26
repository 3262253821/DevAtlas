from datetime import datetime
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.models.incident import Incident
from app.models.incident_citation import IncidentCitation
from app.services.retrieval import RetrievedChunk


class IncidentNotFoundError(Exception):
    pass


class IncidentServiceError(Exception):
    pass


def create_incident(
    db: Session,
    owner_id: int,
    knowledge_base_id: int,
    title: str,
    input_content: str,
) -> Incident:
    incident = Incident(
        owner_id=owner_id,
        knowledge_base_id=knowledge_base_id,
        title=title.strip(),
        input_content=input_content.strip(),
        status="streaming",
        model_name=settings.deepseek_model,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def get_owned_incident(
    db: Session,
    owner_id: int,
    incident_id: int,
) -> Incident:
    incident = db.scalar(
        select(Incident).where(
            Incident.id == incident_id,
            Incident.owner_id == owner_id,
        )
    )

    if incident is None:
        raise IncidentNotFoundError

    return incident


def list_incidents(
    db: Session,
    owner_id: int,
    page: int,
    page_size: int,
    status_filter: str | None = None,
) -> tuple[list[Incident], int]:
    statement = select(Incident).where(
        Incident.owner_id == owner_id,
    )

    if status_filter is not None:
        statement = statement.where(
            Incident.status == status_filter,
        )

    count_statement = select(
        func.count()
    ).select_from(
        statement.subquery()
    )

    total = db.scalar(count_statement) or 0

    items = list(
        db.scalars(
            statement
            .order_by(
                Incident.created_at.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )

    return items, total


def get_incident_detail(
    db: Session,
    owner_id: int,
    incident_id: int,
) -> tuple[Incident, list[IncidentCitation]]:
    incident = get_owned_incident(
        db,
        owner_id,
        incident_id,
    )

    citations = list(
        db.scalars(
            select(IncidentCitation)
            .where(
                IncidentCitation.incident_id
                == incident.id,
            )
            .order_by(
                IncidentCitation.citation_index
            )
        ).all()
    )

    return incident, citations


def delete_incident(
    db: Session,
    owner_id: int,
    incident_id: int,
) -> None:
    incident = get_owned_incident(
        db,
        owner_id,
        incident_id,
    )

    db.delete(incident)
    db.commit()


def mark_incident_completed(
    incident_id: int,
    result: str,
    sources: Sequence[RetrievedChunk],
) -> None:
    db = SessionLocal()

    try:
        incident = db.get(
            Incident,
            incident_id,
        )

        if incident is None:
            raise IncidentServiceError(
                "Incident disappeared"
            )

        incident.status = "completed"
        incident.result = result
        incident.error_message = None
        incident.completed_at = datetime.utcnow()

        for index, source in enumerate(
            sources,
            start=1,
        ):
            chunk = db.scalar(
                select(DocumentChunk).where(
                    DocumentChunk.document_version_id
                    == source.version_id,
                    DocumentChunk.chunk_index
                    == source.chunk_index,
                )
            )

            if chunk is None:
                continue

            db.add(
                IncidentCitation(
                    incident_id=incident.id,
                    document_chunk_id=chunk.id,
                    citation_index=index,
                )
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def mark_incident_failed(
    incident_id: int,
    error_message: str,
) -> None:
    db = SessionLocal()

    try:
        incident = db.get(
            Incident,
            incident_id,
        )

        if incident is None:
            return

        incident.status = "failed"
        incident.error_message = error_message[:2000]
        incident.completed_at = datetime.utcnow()
        db.commit()

    finally:
        db.close()


def mark_incident_cancelled(
    incident_id: int,
) -> None:
    db = SessionLocal()

    try:
        incident = db.get(
            Incident,
            incident_id,
        )

        if incident is None:
            return

        incident.status = "cancelled"
        incident.completed_at = datetime.utcnow()
        db.commit()

    finally:
        db.close()