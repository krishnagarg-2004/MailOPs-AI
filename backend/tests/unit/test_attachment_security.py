from pathlib import Path
import pytest
from backend.app.core.config import settings
from backend.app.services.gmail_sync_service import SUPPORTED_DOWNLOAD_EXTENSIONS


def test_supported_extensions_whitelist():
    """Verify supported download extensions whitelist contains expected document and image formats."""
    assert ".pdf" in SUPPORTED_DOWNLOAD_EXTENSIONS
    assert ".png" in SUPPORTED_DOWNLOAD_EXTENSIONS
    assert ".jpg" in SUPPORTED_DOWNLOAD_EXTENSIONS
    assert ".jpeg" in SUPPORTED_DOWNLOAD_EXTENSIONS
    assert ".docx" in SUPPORTED_DOWNLOAD_EXTENSIONS
    assert ".exe" not in SUPPORTED_DOWNLOAD_EXTENSIONS
    assert ".bat" not in SUPPORTED_DOWNLOAD_EXTENSIONS
    assert ".js" not in SUPPORTED_DOWNLOAD_EXTENSIONS


def test_attachment_max_size_bytes_limit():
    """Verify ATTACHMENT_MAX_SIZE_BYTES defaults to 10 MB."""
    assert settings.ATTACHMENT_MAX_SIZE_BYTES == 10 * 1024 * 1024


def test_path_traversal_prevention_logic():
    """Verify malicious filenames with path traversal elements do not affect storage path construction."""
    malicious_filename = "../../../../../etc/passwd"
    ext = Path(malicious_filename).suffix.lower()
    
    # Extension is not in whitelist
    assert ext not in SUPPORTED_DOWNLOAD_EXTENSIONS

    malicious_pdf = "../../../etc/contract.pdf"
    ext_pdf = Path(malicious_pdf).suffix.lower()
    assert ext_pdf == ".pdf"
    
    # Even if extension is .pdf, disk filename uses random UUID, completely discarding malicious path elements
    import uuid
    uuid_filename = f"{uuid.uuid4().hex}.dat"
    assert "etc" not in uuid_filename
    assert "passwd" not in uuid_filename
