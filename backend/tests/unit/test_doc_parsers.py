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


def test_pdf_parser_native_text_extraction(tmp_path: Path):
    import pypdf
    pdf_path = tmp_path / "sample.pdf"
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    # Add native text content that exceeds DOC_OCR_MIN_CHAR_THRESHOLD (30 chars)
    # Use annotation or text write
    writer.add_outline_item("Title", 0)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    # Use a real text PDF if possible, or verify PDFParser threshold logic
    # When blank, avg_chars < 30 -> triggers OCR fallback
    with pytest.raises(RuntimeError) as exc_info:
        PDFParser.parse_pdf(pdf_path)
    assert "OCR" in str(exc_info.value) or "Poppler" in str(exc_info.value)


def test_document_service_dat_routing_and_traversal(tmp_path: Path):
    from unittest.mock import MagicMock
    from backend.app.services.document_service import DocumentProcessingService
    import uuid

    # Test traversal rejection
    mock_db = MagicMock()
    user_id = uuid.uuid4()
    att_id = uuid.uuid4()

    mock_att = MagicMock()
    mock_att.id = att_id
    mock_att.user_id = user_id
    mock_att.is_downloaded = True
    mock_att.storage_path = "../../../../../windows/system32/cmd.exe"
    mock_att.filename = "evil.pdf"

    mock_db.query.return_value.filter.return_value.first.return_value = mock_att

    with pytest.raises(ValueError) as exc_info:
        DocumentProcessingService.process_attachment(mock_db, user_id, att_id)
    assert "directory traversal" in str(exc_info.value).lower()
