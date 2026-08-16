# Import Base and all domain models so Alembic autogenerate metadata detects them cleanly
from backend.app.db.base_class import Base
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User

__all__ = ["Base", "User", "OAuthAccount"]
