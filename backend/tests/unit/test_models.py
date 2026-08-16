import uuid
from backend.app.models.user import User
from backend.app.models.oauth import OAuthAccount


def test_user_model_attributes():
    """Verify User model instance attributes and table name."""
    user = User(
        email="test@enterprise.com",
        full_name="Test User",
        avatar_url="https://example.com/avatar.png",
        is_active=True,
        is_superuser=False,
    )
    assert user.__tablename__ == "users"
    assert user.email == "test@enterprise.com"
    assert user.full_name == "Test User"
    assert user.avatar_url == "https://example.com/avatar.png"
    assert user.is_active is True
    assert user.is_superuser is False


def test_oauth_account_model_attributes():
    """Verify OAuthAccount model instance attributes and table name."""
    user_id = uuid.uuid4()
    account = OAuthAccount(
        user_id=user_id,
        provider="google",
        provider_account_id="1234567890",
        email="test@gmail.com",
        scopes="https://www.googleapis.com/auth/gmail.readonly",
    )
    assert account.__tablename__ == "oauth_accounts"
    assert account.user_id == user_id
    assert account.provider == "google"
    assert account.provider_account_id == "1234567890"
    assert account.email == "test@gmail.com"
    assert account.scopes == "https://www.googleapis.com/auth/gmail.readonly"


def test_token_security_boundary_docstring():
    """Verify OAuthAccount includes security boundary documentation for token fields."""
    docstring = OAuthAccount.__doc__
    assert docstring is not None
    assert "SECURITY BOUNDARY NOTE" in docstring
    assert "MUST NEVER be stored" in docstring

