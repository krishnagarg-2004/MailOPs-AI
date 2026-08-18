import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.models.user import User
from backend.app.models.email_thread import EmailThread
from backend.app.models.email_message import EmailMessage
from backend.tests.integration.test_database import db_session, test_engine



@pytest.fixture
def auth_user_message(db_session: Session):
    user = User(
        email=f"api_ai_user_{uuid.uuid4().hex[:8]}@example.com",
        full_name="AI API Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"thread_api_{uuid.uuid4().hex[:8]}",
        snippet="API Thread",
    )
    db_session.add(thread)
    db_session.commit()
    db_session.refresh(thread)

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_api_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="vendor@company.com",
        subject="Invoice #404 Payment Due",
        body_plain="Please pay invoice #404 of $1,200 due by 2026-08-30.",
        snippet="Please pay invoice #404 of $1,200 due by 2026-08-30.",
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)

    return user, thread, message


@pytest.mark.asyncio
async def test_ai_analyze_message_and_actions_flow(auth_user_message):
    user, thread, message = auth_user_message

    # Create user session in database
    from backend.app.services.auth_service import create_user_session
    from backend.app.core.config import settings
    # We pass session DB directly
    from backend.tests.integration.test_database import test_engine
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=test_engine)
    session_db = SessionLocal()

    raw_token, _ = create_user_session(session_db, user)
    session_db.close()

    cookie_name = settings.SESSION_COOKIE_NAME
    cookies = {cookie_name: raw_token}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", cookies=cookies) as ac:

        # 1. Trigger AI analysis for message
        response = await ac.post(f"/api/v1/ai/analyze/message/{message.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["email_message_id"] == str(message.id)
        assert data["intent"] in ["FINANCIAL_INVOICE", "URGENT_ACTION", "INFORMATIONAL"]
        assert len(data["extracted_items"]) > 0

        # 2. Get AI analysis
        get_res = await ac.get(f"/api/v1/ai/analysis/message/{message.id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == data["id"]

        # 3. Get user actions
        actions_res = await ac.get("/api/v1/ai/actions")
        assert actions_res.status_code == 200
        actions_list = actions_res.json()
        assert len(actions_list) > 0

        # 4. Patch action status (Human-in-the-Loop)
        action_id = actions_list[0]["id"]
        patch_res = await ac.patch(f"/api/v1/ai/actions/{action_id}", json={"status": "CONFIRMED"})
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "CONFIRMED"
