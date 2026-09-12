import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.langchain_rag import (  # noqa: E402
    DevAtlasRetriever,
    retrieve_context_with_langchain,
)
from app.services.retrieval import (  # noqa: E402
    RetrievedChunk,
    RetrievalResult,
)
from app.services.llm import build_rag_messages  # noqa: E402


def test_retriever_adapts_sources_to_langchain_documents(monkeypatch) -> None:
    source = RetrievedChunk(
        document_id=10,
        version_id=22,
        version_number=2,
        chunk_index=4,
        filename="guide.md",
        content="数据库连接池排查步骤",
        distance=0.18,
        page_number=None,
    )
    monkeypatch.setattr(
        "app.services.langchain_rag.retrieve_context",
        lambda **_kwargs: RetrievalResult(
            context=source.content,
            sources=[source],
        ),
    )

    retriever = DevAtlasRetriever(
        db=object(),
        knowledge_base_id=3,
        top_k=3,
    )

    documents = retriever.invoke("数据库连接失败怎么办？")

    assert len(documents) == 1
    assert documents[0].page_content == source.content
    assert documents[0].metadata["version_id"] == 22
    assert documents[0].metadata["chunk_index"] == 4


def test_langchain_adapter_restores_existing_retrieval_result(monkeypatch) -> None:
    source = RetrievedChunk(
        document_id=10,
        version_id=22,
        version_number=2,
        chunk_index=4,
        filename="guide.md",
        content="数据库连接池排查步骤",
        distance=0.18,
        page_number=None,
    )
    monkeypatch.setattr(
        "app.services.langchain_rag.retrieve_context",
        lambda **_kwargs: RetrievalResult(
            context=source.content,
            sources=[source],
        ),
    )

    result = retrieve_context_with_langchain(
        db=object(),
        knowledge_base_id=3,
        question="数据库连接失败怎么办？",
        top_k=3,
    )

    assert result.context == source.content
    assert result.sources[0] == source


def test_rag_prompt_is_rendered_by_langchain_template() -> None:
    messages = build_rag_messages(
        question="如何排查？",
        context="先检查数据库连接池。",
    )

    assert [message["role"] for message in messages] == [
        "system",
        "user",
    ]
    assert "如何排查？" in messages[1]["content"]
    assert "先检查数据库连接池。" in messages[1]["content"]
