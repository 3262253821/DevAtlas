import sys
from pathlib import Path

import pytest
from pypdf import PdfWriter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))


from app.core.file_security import (  # noqa: E402
    InvalidFilenameError,
    UnsupportedFileTypeError,
    ensure_safe_path,
    normalize_filename,
    validate_extension,
)
from app.services.document_parser import EmptyDocumentError, parse_document  # noqa: E402


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InvalidFilenameError):
        ensure_safe_path(tmp_path, "../outside.txt")


def test_filename_is_normalized_to_a_safe_basename() -> None:
    assert normalize_filename(r"..\nested\guide.txt") == "guide.txt"


def test_unsupported_extension_is_rejected() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_extension("guide.exe")


def test_empty_pdf_text_is_rejected(tmp_path: Path) -> None:
    # 这是一个合法但没有可提取文字的 PDF 文件。
    empty_pdf = tmp_path / "empty.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with empty_pdf.open("wb") as output:
        writer.write(output)

    with pytest.raises(EmptyDocumentError):
        parse_document(empty_pdf, "pdf")
