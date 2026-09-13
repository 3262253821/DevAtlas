from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb

from app.core.config import settings


COLLECTION_NAME = "devatlas_knowledge_chunks"


class VectorStoreError(Exception):
    """Chroma 初始化或写入失败。"""


def _resolve_persist_dir(
    persist_dir: Path | None = None,
) -> Path:
    # 如果调用者传了 persist_dir,就用它,否则用配置文件里的 chroma_persist_dir
    directory = (
        persist_dir
        if persist_dir is not None
        else settings.chroma_persist_dir
    )

    resolved_dir = directory.resolve()
    resolved_dir.mkdir(
        # 父目录不存在也一起创建
        parents=True,
        # 目录已经存在时不报错
        exist_ok=True,
    )

    return resolved_dir


# 初始化 Chroma 集合
# 第一次调用时初始化，后续调用直接复用缓存集合
# maxsize表示缓存集合的最大数量，超过数量的集合会被移除
@lru_cache(maxsize=8)
def _get_collection(
    persist_dir_string: str,
):
    """
    根据持久化目录创建或获取 Chroma 集合。
    同一个目录在当前进程内只初始化一次。
    """
    try:
        # 把 Chroma 数据持久化到本地目录
        client = chromadb.PersistentClient(
            path=persist_dir_string,
        )

        # 获取集合,不存在就创建,并设置空间为余弦相似度
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                # 表示使用余弦距离作为向量比较空间
                # 余弦相似度用于计算向量之间的角度余弦值，范围在 -1 到 1 之间
                # 1 表示完全相似，-1 表示完全相反
                "hnsw:space": "cosine",
            },
        )

    except Exception as error:
        raise VectorStoreError(
            "Failed to initialize Chroma collection"
        ) from error


def get_chroma_collection(
    persist_dir: Path | None = None,
):
    resolved_dir = _resolve_persist_dir(
        persist_dir
    )

    return _get_collection(
        str(resolved_dir)
    )


def build_vector_id(
    knowledge_base_id: int,
    document_id: int,
    version_id: int,
    chunk_index: int,
) -> str:
    """
    生成稳定且可重复计算的向量 ID。
    """
    return (
        f"kb:{knowledge_base_id}"
        f":doc:{document_id}"
        f":version:{version_id}"
        f":chunk:{chunk_index}"
    )


# 写入文档块到 Chroma 集合
def upsert_chunks(
    *,
    knowledge_base_id: int,
    document_id: int,
    version_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
    # 表示 Chroma 持久化目录
    persist_dir: Path | None = None,
) -> list[str]:
    """
    把文档块、向量和 metadata 一起写入 Chroma。
    返回本次写入的稳定 vector_id 列表。
    """
    if not chunks:
        return []
    # 检查文档块、向量和 metadata 数量是否匹配
    # 如果不匹配，抛出异常
    if len(chunks) != len(embeddings):
        raise VectorStoreError(
            "Chunks and embeddings count do not match"
        )

    if len(chunks) != len(metadatas):
        raise VectorStoreError(
            "Chunks and metadatas count do not match"
        )

    # 这份 ID 实际传给 Chroma 作为文档块的唯一标识
    # 每个 ID 都是唯一的，对应一个文档块的向量表示
    ids = [
        build_vector_id(
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            version_id=version_id,
            chunk_index=index,
        )
        for index in range(len(chunks))
    ]

    try:
        collection = get_chroma_collection(
            persist_dir
        )
        # upsert表示如果 ID 存在则更新，不存在就新增
        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    except VectorStoreError:
        raise

    except Exception as error:
        raise VectorStoreError(
            "Failed to upsert document chunks"
        ) from error

    return ids


# 删除指定向量
def delete_vectors(
    vector_ids: list[str],
    persist_dir: Path | None = None,
) -> None:
    """
    删除指定向量，供后续重新索引和文档删除使用。
    """
    if not vector_ids:
        return

    try:
        collection = get_chroma_collection(
            persist_dir
        )
        collection.delete(ids=vector_ids)

    except VectorStoreError:
        raise

    except Exception as error:
        raise VectorStoreError(
            "Failed to delete vectors"
        ) from error