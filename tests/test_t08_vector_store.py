import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


from app.services.vector_store import (
    build_vector_id,
    delete_vectors,
    get_chroma_collection,
    upsert_chunks,
)


def test_build_vector_id_is_stable() -> None:
    vector_id = build_vector_id(
        knowledge_base_id=1,
        document_id=10,
        version_id=21,
        chunk_index=0,
    )

    assert vector_id == (
        "kb:1:doc:10:version:21:chunk:0"
    )


def test_upsert_and_delete_chunks(
    tmp_path: Path,
) -> None:
    chunks = [
        "忘记密码后，可以通过登录页面重置。",
        "员工工作满一年，可以享受带薪年假。",
    ]

    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]

    metadatas = [
        {
            "knowledge_base_id": 1,
            "document_id": 10,
            "document_version_id": 21,
            "chunk_index": 0,
            "source_filename": "handbook.txt",
            "is_searchable": True,
        },
        {
            "knowledge_base_id": 1,
            "document_id": 10,
            "document_version_id": 21,
            "chunk_index": 1,
            "source_filename": "handbook.txt",
            "is_searchable": True,
        },
    ]

    vector_ids = upsert_chunks(
        knowledge_base_id=1,
        document_id=10,
        version_id=21,
        chunks=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        persist_dir=tmp_path / "chroma",
    )

    assert vector_ids == [
        "kb:1:doc:10:version:21:chunk:0",
        "kb:1:doc:10:version:21:chunk:1",
    ]

    collection = get_chroma_collection(
        tmp_path / "chroma"
    )

    result = collection.get(
        ids=vector_ids,
        include=[
            "documents",
            "metadatas",
        ],
    )

    assert len(result["ids"]) == 2
    assert set(result["documents"]) == set(chunks)

    delete_vectors(
        vector_ids,
        persist_dir=tmp_path / "chroma",
    )

    deleted_result = collection.get(
        ids=vector_ids,
        include=[
            "documents",
            "metadatas",
        ],
    )

    assert deleted_result["ids"] == []