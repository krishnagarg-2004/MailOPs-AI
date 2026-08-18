from pathlib import Path
import pytest
from backend.app.documents.docx_parser import DOCXParser
from backend.app.documents.image_parser import ImageParser
from backend.app.documents.pdf_parser import PDFParser
from backend.app.documents.sanitizer import DocumentSanitizer


def test_document_sanitizer_cleans_nulls_and_formats_pages():
    raw_text = "Page 1 content\x00 with null bytes."
    clean = DocumentSanitizer.sanitize_text(raw_text)
    assert "\x00" not in clean
    assert "Page 1 content with null bytes." in clean

    pages = ["Page 1 text", "Page 2 text"]
    formatted, count = DocumentSanitizer.format_page_text(pages)
    assert count == 2
    assert "--- [Page 1] ---" in formatted
    assert "--- [Page 2] ---" in formatted


def test_image_parser_dimension_validation(tmp_path: Path):
    # Test file missing handling
    missing_file = tmp_path / "non_existent.png"
    with pytest.raises(FileNotFoundError):
        ImageParser.parse_image(missing_file)


def test_docx_parser_zip_bomb_protection(tmp_path: Path):
    # Test non-zip file handling
    invalid_docx = tmp_path / "fake.docx"
    invalid_docx.write_bytes(b"This is not a zip file.")

    with pytest.raises(ValueError) as exc_info:
        DOCXParser.parse_docx(invalid_docx)
    assert "not a valid DOCX/ZIP archive" in str(exc_info.value)
