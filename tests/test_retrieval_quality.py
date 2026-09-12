import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.retrieval import retrieve_context  # noqa: E402


class _FakeDB:
    pass


class _FakeCollection:
    def __init__(self) -> None:
        self.kwargs = None

    def query(self, **kwargs):
        self.kwargs = kwargs
        return {
            "documents": [["订单服务需要检查数据库连接池。"]],
            "metadatas": [[
                {
                    "document_id": 10,
                    "document_version_id": 22,
                    "version_number": 2,
                    "chunk_index": 4,
                    "source_filename": "订单服务故障排查手册.md",
                    "page_number": None,
                }
            ]],
            "distances": [[0.18]],
        }


def test_top_k_is_forwarded_and_sources_keep_version_metadata(monkeypatch) -> None:
    collection = _FakeCollection()
    monkeypatch.setattr(
        "app.services.retrieval._get_indexed_version_ids",
        lambda _db, _kb_id: [22],
    )
    monkeypatch.setattr(
        "app.services.retrieval.embed_texts",
        lambda texts: [[0.1, 0.2] for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.retrieval.get_chroma_collection",
        lambda: collection,
    )

    result = retrieve_context(
        db=_FakeDB(),
        knowledge_base_id=3,
        question="数据库连接失败怎么办？",
        top_k=3,
    )

    assert collection.kwargs["n_results"] == 3
    assert collection.kwargs["where"]["$and"][1]["document_version_id"] == {"$in": [22]}
    assert len(result.sources) == 1
    assert result.sources[0].version_id == 22
    assert result.sources[0].version_number == 2
    assert result.sources[0].chunk_index == 4


def test_no_indexed_version_returns_no_answer_context(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.retrieval._get_indexed_version_ids",
        lambda _db, _kb_id: [],
    )

    result = retrieve_context(
        db=_FakeDB(),
        knowledge_base_id=3,
        question="与知识库无关的问题",
        top_k=5,
    )

    assert result.context == ""
    assert result.sources == []
