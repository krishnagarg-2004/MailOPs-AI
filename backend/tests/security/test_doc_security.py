from pathlib import Path
import pytest
from backend.app.documents.docx_parser import DOCXParser
from backend.app.documents.sanitizer import DocumentSanitizer


def test_document_sanitizer_removes_dangerous_control_characters():
    malicious_input = "Invoice\x00 #101\x07\x1b[31m RED TEXT \x1b[0m Payload"
    cleaned = DocumentSanitizer.sanitize_text(malicious_input)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "Invoice #101" in cleaned


def test_docx_parser_rejects_non_zip_files(tmp_path: Path):
    exe_file = tmp_path / "malicious.docx"
    exe_file.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00 Fake EXE Payload")

    with pytest.raises(ValueError) as exc_info:
        DOCXParser.parse_docx(exe_file)
    assert "not a valid DOCX/ZIP archive" in str(exc_info.value)
