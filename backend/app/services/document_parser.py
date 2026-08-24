from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


class DocumentParseError(Exception):
    """文档解析失败的基础异常。"""


class UnsupportedDocumentTypeError(DocumentParseError):
    """文档类型不在解析器支持范围内。"""


class EmptyDocumentError(DocumentParseError):
    """文档解析后没有有效文本。"""

# frozen=True：返回后不能随意修改，避免后续业务流程意外改掉解析结果
@dataclass(frozen=True)
class ParsedDocument:
    """解析器返回的统一结果。"""

    text: str # 解析出来的完整文本
    file_type: str # txt、md 或 pdf
    page_count: int | None = None # PDF 页数，TXT 和 Markdown 没有页数，所以是 None


def parse_document(
    file_path: Path,
    file_type: str | None = None,
) -> ParsedDocument:
    """
    根据文件类型读取文档，并统一返回纯文本。
    file_type 可以传 md、txt、pdf,也可以让函数从路径后缀推断。
    """
    if not file_path.is_file():
        raise DocumentParseError(
            f"Document file does not exist: {file_path}"
        )

    normalized_type = (
        file_type or file_path.suffix
    ).lower().removeprefix(".")

    if normalized_type in {"txt", "md"}:
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise DocumentParseError(
                "The document is not valid UTF-8 text"
            ) from error

        page_count = None

    elif normalized_type == "pdf":
        try:
            reader = PdfReader(str(file_path))
            page_texts = [
                page.extract_text() or ""
                for page in reader.pages
            ]
            text = "\n\n".join(page_texts)
            page_count = len(reader.pages)
        except Exception as error:
            raise DocumentParseError(
                "Failed to parse PDF document"
            ) from error

    else:
        raise UnsupportedDocumentTypeError(
            f"Unsupported document type: {normalized_type or '<none>'}"
        )

    # 去掉首尾空白和可能影响后续处理的空字符。
    cleaned_text = text.replace("\x00", "").strip()

    if not cleaned_text:
        raise EmptyDocumentError(
            "Document contains no usable text"
        )

    return ParsedDocument(
        text=cleaned_text,
        file_type=normalized_type,
        page_count=page_count,
    )