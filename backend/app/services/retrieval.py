from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.services.embedding import (
    EmbeddingError,
    embed_texts,
)
from app.services.vector_store import (
    VectorStoreError,
    get_chroma_collection,
)


class RetrievalError(Exception):
    """RAG 检索过程失败。"""


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: int
    version_id: int
    version_number: int
    chunk_index: int
    filename: str
    content: str
    distance: float
    page_number: int | None


@dataclass(frozen=True)
class RetrievalResult:
    context: str
    sources: list[RetrievedChunk]


def _get_indexed_version_ids(
    db: Session,
    knowledge_base_id: int,
) -> list[int]:
    """
    查询当前知识库中允许参与检索的 indexed 版本。
    """
    statement = (
        select(DocumentVersion.id)
        .join(
            Document,
            DocumentVersion.document_id
            == Document.id,
        )
        .where(
            Document.knowledge_base_id
            == knowledge_base_id,
            DocumentVersion.status == "indexed",
        )
    )

    return list(db.scalars(statement).all())


def _build_where_filter(
    knowledge_base_id: int,
    indexed_version_ids: list[int],
) -> dict[str, Any]:
    """
    生成 Chroma metadata 过滤条件。
    """
    return {
        "$and": [
            {
                "knowledge_base_id": knowledge_base_id,
            },
            {
                "document_version_id": {
                    "$in": indexed_version_ids,
                },
            },
            {
                "is_searchable": True,
            },
        ],
    }


def retrieve_context(
    db: Session,
    knowledge_base_id: int,
    question: str,
    top_k: int = 5,
) -> RetrievalResult:
    """
    将问题向量化，在当前知识库的 indexed 版本中检索 Top-K 文档块。
    """
    normalized_question = question.strip()

    if not normalized_question:
        raise RetrievalError(
            "Question cannot be empty"
        )

    indexed_version_ids = _get_indexed_version_ids(
        db,
        knowledge_base_id,
    )

    if not indexed_version_ids:
        return RetrievalResult(
            context="",
            sources=[],
        )

    try:
        question_embedding = embed_texts(
            [normalized_question]
        )[0]

        collection = get_chroma_collection()

        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=top_k,
            where=_build_where_filter(
                knowledge_base_id,
                indexed_version_ids,
            ),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

    except EmbeddingError as error:
        raise RetrievalError(
            "Failed to embed retrieval question"
        ) from error

    except VectorStoreError as error:
        raise RetrievalError(
            "Failed to access vector store"
        ) from error

    except Exception as error:
        raise RetrievalError(
            "Failed to query vector store"
        ) from error

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]

    document_items = documents[0] if documents else []
    metadata_items = metadatas[0] if metadatas else []
    distance_items = distances[0] if distances else []

    sources: list[RetrievedChunk] = []

    for content, metadata, distance in zip(
        document_items,
        metadata_items,
        distance_items,
    ):
        if not content or not metadata:
            continue

        try:
            source = RetrievedChunk(
                document_id=int(
                    metadata["document_id"]
                ),
                version_id=int(
                    metadata["document_version_id"]
                ),
                version_number=int(
                    metadata["version_number"]
                ),
                chunk_index=int(
                    metadata["chunk_index"]
                ),
                filename=str(
                    metadata["source_filename"]
                ),
                content=str(content),
                distance=float(distance),
                page_number=(
                    int(metadata["page_number"])
                    if metadata.get("page_number")
                    is not None
                    else None
                ),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

        sources.append(source)

    context = "\n\n".join(
        source.content
        for source in sources
    )

    return RetrievalResult(
        context=context,
        sources=sources,
    )