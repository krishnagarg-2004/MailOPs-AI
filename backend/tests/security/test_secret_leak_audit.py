import os
import re
from pathlib import Path
import pytest
from backend.app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_config_default_secret_keys_warning():
    """Assert default dev secret keys are present only in non-production development mode."""
    assert settings.APP_ENV == "development"
    # Ensure default dev key is structured appropriately for dev
    assert len(settings.SECRET_KEY) >= 32
    assert len(settings.ENCRYPTION_KEY) >= 32


def test_codebase_secret_leak_audit():
    """
    EXPLICIT SECURITY AUDIT:
    Scan all source files under backend/app and database/migrations for hardcoded production secrets,
    private RSA/EC keys, or unencrypted OAuth credentials.
    """
    secret_patterns = [
        re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"),
        re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),  # Google API Key format
        re.compile(r"client_secret\s*=\s*['\"](?!\s*your_google_client_secret_here|dev_|test_)[A-Za-z0-9_-]{24,}['\"]"),
        re.compile(r"postgres://[a-zA-Z0-9_]+:[a-zA-Z0-9_]+@\S+"),  # Hardcoded production DB URLs
    ]

    scanned_extensions = {".py", ".toml", ".json", ".yaml", ".yml"}
    flagged_issues: list[str] = []

    search_dirs = [
        PROJECT_ROOT / "backend" / "app",
        PROJECT_ROOT / "database" / "migrations",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for root, _, files in os.walk(search_dir):
            for file_name in files:
                file_path = Path(root) / file_name
                if file_path.suffix in scanned_extensions:
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        for pattern in secret_patterns:
                            if pattern.search(content):
                                flagged_issues.append(f"Potential secret leak matched pattern '{pattern.pattern}' in {file_path}")
                    except Exception as exc:
                        flagged_issues.append(f"Could not read {file_path}: {exc}")

    assert len(flagged_issues) == 0, f"Secret leak audit failures: {flagged_issues}"
