import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


from app.services.document_parser import (
    EmptyDocumentError,
    parse_document,
)
from app.services.text_splitter import (
    split_text_by_sentence,
)


def test_parse_txt_file(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text(
        "第一句话。第二句话。",
        encoding="utf-8",
    )

    result = parse_document(sample_file)

    assert result.file_type == "txt"
    assert result.page_count is None
    assert result.text == "第一句话。第二句话。"


def test_parse_empty_txt_file_fails(
    tmp_path: Path,
) -> None:
    sample_file = tmp_path / "empty.txt"
    sample_file.write_text(
        "",
        encoding="utf-8",
    )

    try:
        parse_document(sample_file)
    except EmptyDocumentError:
        assert True
    else:
        assert False


def test_split_text_by_sentence() -> None:
    text = "第一句话。第二句话。第三句话。"

    chunks = split_text_by_sentence(
        text,
        chunk_size=10,
    )

    assert len(chunks) >= 2
    assert "".join(chunks).replace(
        "\n",
        "",
    ) == text