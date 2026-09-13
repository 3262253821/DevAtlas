from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingError(Exception):
    """Embedding 模型加载或向量生成失败。"""


# 第一次调用时加载模型，后续调用直接复用缓存模型
@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    加载并缓存 Embedding 模型。
    同一个进程内只加载一次，避免每次请求重复加载模型。
    """
    try:
        return SentenceTransformer(
            settings.embedding_model
        )
    except Exception as error:
        raise EmbeddingError(
            "Failed to load embedding model"
        ) from error

# 文本向量化
def embed_texts(
    texts: list[str],
) -> list[list[float]]:
    """
    把多段文本转换为向量列表。
    返回结果的顺序与输入 texts 保持一致。
    """
    if not texts:
        return []

    # 清理输入文本，移除空字符串
    cleaned_texts = [
        text.strip()
        for text in texts
    ]
    # 检查是否有空字符，any() 函数表示至少有一个元素为 True
    if any(not text for text in cleaned_texts):
        raise EmbeddingError(
            "Embedding input contains empty text"
        )

    try:
        # 加载模型
        model = get_embedding_model()
        # 文本向量化,批量处理
        vectors = model.encode(
            cleaned_texts,
            # 归一化向量，确保向量长度为 1
            normalize_embeddings=True,
            # 表示让模型返回 NumPy 数组，而不是普通 Python 列表
            convert_to_numpy=True,
        )

    except EmbeddingError:
        raise

    except Exception as error:
        raise EmbeddingError(
            "Failed to generate text embeddings"
        ) from error
        
    # 转换为列表，返回结果的顺序与输入 texts 保持一致
    return vectors.tolist()