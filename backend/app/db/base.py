# Import Base and all domain models so Alembic autogenerate metadata detects them cleanly
from backend.app.db.base_class import Base
from backend.app.models.attachment import Attachment
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.gmail_sync_state import GmailSyncState
from backend.app.models.oauth import OAuthAccount
from backend.app.models.session import UserSession
from backend.app.models.user import User

__all__ = [
    "Base",
    "User",
    "OAuthAccount",
    "UserSession",
    "EmailThread",
    "EmailMessage",
    "Attachment",
    "GmailSyncState",
]
