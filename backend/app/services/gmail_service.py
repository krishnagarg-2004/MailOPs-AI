"""
Alias module redirecting to backend.app.services.gmail_sync_service.
"""

from backend.app.services.gmail_sync_service import (
    GmailSyncService,
    SUPPORTED_DOWNLOAD_EXTENSIONS,
)

__all__ = ["GmailSyncService", "SUPPORTED_DOWNLOAD_EXTENSIONS"]
