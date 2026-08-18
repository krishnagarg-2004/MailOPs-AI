import uuid
import pytest
from sqlalchemy.orm import Session
from backend.app.integrations.google_oauth import has_compose_scope
from backend.app.models.oauth import OAuthAccount
from backend.app.models.user import User
from backend.app.services.reply_draft_service import ReplyDraftService
from backend.tests.integration.test_database import db_session, test_engine


def test_has_compose_scope_verification():
    readonly_scopes = "openid email profile https://www.googleapis.com/auth/gmail.readonly"
    compose_scopes = "openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose"

    assert has_compose_scope(readonly_scopes) is False
    assert has_compose_scope(compose_scopes) is True


def test_verify_compose_scope_raises_permission_error_when_missing(db_session: Session):
    user = User(email=f"scope_user_{uuid.uuid4().hex[:8]}@test.com", full_name="Scope User", is_active=True)
    db_session.add(user)
    db_session.commit()

    oauth_readonly = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_account_id=f"g_acc_{uuid.uuid4().hex[:8]}",
        scopes="openid email profile https://www.googleapis.com/auth/gmail.readonly",
    )
    db_session.add(oauth_readonly)
    db_session.commit()

    # Attempting compose verification when user only has read-only scope MUST raise PermissionError
    with pytest.raises(PermissionError) as exc_info:
        ReplyDraftService.verify_compose_scope(db_session, user.id)
    assert "compose permissions are required" in str(exc_info.value)
