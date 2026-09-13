import sys
from pathlib import Path

from sqlalchemy.dialects import sqlite


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


from app.services.retrieval import _get_indexed_version_ids  # noqa: E402


class _FakeResult:
    def __init__(self, values: list[int]) -> None:
        self._values = values

    def all(self) -> list[int]:
        return self._values


class _FakeSession:
    def __init__(self, values: list[int]) -> None:
        self.values = values
        self.statement = None

    def scalars(self, statement):
        self.statement = statement
        return _FakeResult(self.values)


def test_get_indexed_version_ids_only_returns_current_indexed_versions() -> None:
    db = _FakeSession([21])

    result = _get_indexed_version_ids(db, 3)

    assert result == [21]

    compiled_sql = str(
        db.statement.compile(
            dialect=sqlite.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "documents.current_version_id = document_versions.id" in compiled_sql
    assert "documents.knowledge_base_id = 3" in compiled_sql
    assert "document_versions.status = 'indexed'" in compiled_sql
