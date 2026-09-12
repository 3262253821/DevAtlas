"""LangChain 编排适配层。

底层版本过滤、权限边界和 Chroma 查询仍由 DevAtlas 自己控制；
本模块只把已有检索结果适配成 LangChain Retriever 的标准 Document。
"""

from typing import Any

from langchain_core.documents import Document as LangChainDocument
from langchain_core.retrievers import BaseRetriever
from pydantic import Field
from sqlalchemy.orm import Session

from app.services.retrieval import (
    RetrievalError,
    RetrievedChunk,
    RetrievalResult,
    retrieve_context,
)


class DevAtlasRetriever(BaseRetriever):
    """保留 DevAtlas 版本过滤规则的 LangChain Retriever。"""

    db: Any = Field(exclude=True)
    knowledge_base_id: int
    top_k: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager,
    ) -> list[LangChainDocument]:
        result = retrieve_context(
            db=self.db,
            knowledge_base_id=self.knowledge_base_id,
            question=query,
            top_k=self.top_k,
        )

        return [
            LangChainDocument(
                page_content=source.content,
                metadata={
                    "document_id": source.document_id,
                    "version_id": source.version_id,
                    "version_number": source.version_number,
                    "chunk_index": source.chunk_index,
                    "filename": source.filename,
                    "distance": source.distance,
                    "page_number": source.page_number,
                },
            )
            for source in result.sources
        ]


def retrieve_context_with_langchain(
    db: Session,
    knowledge_base_id: int,
    question: str,
    top_k: int = 5,
) -> RetrievalResult:
    """通过 LangChain Retriever 执行检索，并还原为现有 API 使用的结果结构。"""

    retriever = DevAtlasRetriever(
        db=db,
        knowledge_base_id=knowledge_base_id,
        top_k=top_k,
    )

    documents = retriever.invoke(question)
    sources: list[RetrievedChunk] = []

    for document in documents:
        metadata = document.metadata
        try:
            sources.append(
                RetrievedChunk(
                    document_id=int(metadata["document_id"]),
                    version_id=int(metadata["version_id"]),
                    version_number=int(metadata["version_number"]),
                    chunk_index=int(metadata["chunk_index"]),
                    filename=str(metadata["filename"]),
                    content=document.page_content,
                    distance=float(metadata["distance"]),
                    page_number=(
                        int(metadata["page_number"])
                        if metadata.get("page_number") is not None
                        else None
                    ),
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            raise RetrievalError(
                "LangChain retriever returned invalid metadata"
            ) from error

    return RetrievalResult(
        context="\n\n".join(source.content for source in sources),
        sources=sources,
    )
