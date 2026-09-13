import re


class InvalidChunkConfigError(ValueError):
    """文本切分参数不合法。"""


def split_text_by_sentence(
    text: str,
    chunk_size: int = 800,
) -> list[str]:
    """
    按句子和换行切分文本，并尽量让每个 chunk 不超过 chunk_size。
    """
    if chunk_size <= 0:
        raise InvalidChunkConfigError(
            "chunk_size must be greater than 0"
        )

    # 移除文本中的控制字符和首尾空格
    cleaned_text = text.replace("\x00", "").strip()

    if not cleaned_text:
        return []
    # 初步拆出来的句子
    sentences = [
        part.strip()
        for part in re.split(
            r"(?<=[。！？!?])|[\r\n]+",
            cleaned_text,
        )
        if part.strip()
    ]
    # 已经完成的文档块
    chunks: list[str] = []
    # 当前正在拼接的句子
    current_sentences: list[str] = []
    current_length = 0

    for sentence in sentences:
        # 单个句子超过上限时，按字符硬切。即兜底策略。
        if len(sentence) > chunk_size:
            if current_sentences:
                chunks.append(
                    "\n".join(current_sentences)
                )
                current_sentences = []
                current_length = 0

            for start in range(
                0,
                len(sentence),
                chunk_size,
            ):
                chunks.append(
                    sentence[start:start + chunk_size]
                )

            continue

        extra_length = (
            len(sentence)
            if not current_sentences
            else len(sentence) + 1
        )

        # 加入当前句会超出上限，先保存旧 chunk。
        if (
            current_sentences
            and current_length + extra_length > chunk_size
        ):
            chunks.append(
                "\n".join(current_sentences)
            )
            current_sentences = [sentence]
            current_length = len(sentence)
        else:
            current_sentences.append(sentence)
            current_length += extra_length

    if current_sentences:
        chunks.append(
            "\n".join(current_sentences)
        )

    return chunks