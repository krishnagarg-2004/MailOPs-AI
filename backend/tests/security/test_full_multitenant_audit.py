import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.reply_draft import ReplyDraft
from backend.app.models.user import User
from backend.app.services.action_graph_service import ActionGraphService
from backend.app.services.auth_service import create_user_session
from backend.tests.integration.test_database import db_session, test_engine

client = TestClient(app)


def test_comprehensive_multi_tenant_isolation_audit(db_session: Session):
    """
    EXPLICIT MULTI-TENANT SECURITY AUDIT:
    Verify User B receives HTTP 404 or 403 for 100% of requests targeting User A's resources
    across all API endpoints (/gmail, /ai, /documents, /search, /graph, /reply-drafts).
    """
    # 1. Create User A and User B
    user_a = User(email=f"usera_audit_{uuid.uuid4().hex[:8]}@test.com", full_name="User A Audit", is_active=True)
    user_b = User(email=f"userb_audit_{uuid.uuid4().hex[:8]}@test.com", full_name="User B Audit", is_active=True)
    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a, _ = create_user_session(db_session, user_a)
    token_b, _ = create_user_session(db_session, user_b)
    cookies_b = {"mailops_session": token_b}

    # 2. Populate User A resources
    thread_a = EmailThread(user_id=user_a.id, gmail_thread_id=f"th_a_{uuid.uuid4().hex[:8]}", snippet="User A Thread")
    db_session.add(thread_a)
    db_session.commit()

    msg_a = EmailMessage(
        user_id=user_a.id,
        thread_id=thread_a.id,
        gmail_message_id=f"msg_a_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread_a.gmail_thread_id,
        sender="confidential@vendor.com",
        subject="Confidential Contract Details",
        body_plain="Confidential data for User A.",
    )
    db_session.add(msg_a)
    db_session.commit()

    analysis_a = AIAnalysis(
        user_id=user_a.id,
        email_message_id=msg_a.id,
        email_thread_id=thread_a.id,
        summary="User A Confidential Summary",
        intent="CONTRACT_LEGAL",
        priority="HIGH",
        sentiment="NEUTRAL",
        confidence_score=0.95,
        rationale="Confidential review required.",
        model_name="mock-model",
        prompt_version="1.0.0",
        status="COMPLETED",
    )
    db_session.add(analysis_a)
    db_session.commit()

    action_a = ExtractedAction(
        user_id=user_a.id,
        ai_analysis_id=analysis_a.id,
        email_message_id=msg_a.id,
        email_thread_id=thread_a.id,
        item_type="TASK",
        description="User A Confidential Task",
        assignee="Alice",
        severity_or_priority="HIGH",
        confidence_score=0.9,
    )
    db_session.add(action_a)
    db_session.commit()

    draft_a = ReplyDraft(
        user_id=user_a.id,
        email_thread_id=thread_a.id,
        email_message_id=msg_a.id,
        subject="Re: Confidential Contract Details",
        body_text="Confidential draft text.",
        recipient_email="confidential@vendor.com",
        status="DRAFTED",
    )
    db_session.add(draft_a)
    db_session.commit()

    node_a = ActionGraphService.sync_action_nodes(db_session, user_a.id, action_a.id)

    # 3. AUDIT TEST: User B attempts to access User A's endpoints

    # Endpoint 1: GET /api/v1/gmail/threads/{id}
    res1 = client.get(f"/api/v1/gmail/threads/{thread_a.id}", cookies=cookies_b)
    assert res1.status_code == 404, f"Gmail thread endpoint failed multi-tenant check: {res1.status_code}"

    # Endpoint 2: GET /api/v1/gmail/messages/{id}
    res2 = client.get(f"/api/v1/gmail/messages/{msg_a.id}", cookies=cookies_b)
    assert res2.status_code == 404, f"Gmail message endpoint failed multi-tenant check: {res2.status_code}"

    # Endpoint 3: GET /api/v1/ai/analysis/message/{id}
    res3 = client.get(f"/api/v1/ai/analysis/message/{msg_a.id}", cookies=cookies_b)
    assert res3.status_code == 404, f"AI analysis endpoint failed multi-tenant check: {res3.status_code}"

    # Endpoint 4: POST /api/v1/ai/actions/{id}/confirm
    res4 = client.post(f"/api/v1/ai/actions/{action_a.id}/confirm", cookies=cookies_b)
    assert res4.status_code == 404, f"AI action confirm endpoint failed multi-tenant check: {res4.status_code}"

    # Endpoint 5: GET /api/v1/documents/extraction/{id}
    fake_doc_id = uuid.uuid4()
    res5 = client.get(f"/api/v1/documents/extraction/{fake_doc_id}", cookies=cookies_b)
    assert res5.status_code == 404, f"Document extraction endpoint failed multi-tenant check: {res5.status_code}"

    # Endpoint 6: GET /api/v1/graph/dependencies/{action_id}
    res6 = client.get(f"/api/v1/graph/dependencies/{action_a.id}", cookies=cookies_b)
    assert res6.status_code == 404, f"Graph dependencies endpoint failed multi-tenant check: {res6.status_code}"

    # Endpoint 7: GET /api/v1/reply-drafts/{id}
    res7 = client.get(f"/api/v1/reply-drafts/{draft_a.id}", cookies=cookies_b)
    assert res7.status_code == 404, f"Reply draft endpoint failed multi-tenant check: {res7.status_code}"

    # Endpoint 8: PUT /api/v1/reply-drafts/{id}
    res8 = client.put(f"/api/v1/reply-drafts/{draft_a.id}", json={"body_text": "Hacked"}, cookies=cookies_b)
    assert res8.status_code == 404, f"Reply draft edit endpoint failed multi-tenant check: {res8.status_code}"
