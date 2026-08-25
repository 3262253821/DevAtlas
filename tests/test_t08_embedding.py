import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


from app.services.embedding import (
    EmbeddingError,
    embed_texts,
)


def test_embed_texts_returns_vectors() -> None:
    texts = [
        "忘记密码后，可以通过登录页面重置。",
        "员工工作满一年，可以享受带薪年假。",
    ]

    vectors = embed_texts(texts)

    assert len(vectors) == 2
    assert len(vectors[0]) > 0
    assert len(vectors[0]) == len(vectors[1])
    assert all(
        isinstance(value, float)
        for value in vectors[0]
    )


def test_empty_texts_returns_empty_list() -> None:
    assert embed_texts([]) == []


def test_empty_text_is_rejected() -> None:
    try:
        embed_texts([""])
    except EmbeddingError:
        assert True
    else:
        assert False