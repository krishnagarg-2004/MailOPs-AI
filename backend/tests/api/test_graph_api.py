import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread

from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.user import User
from backend.app.services.action_graph_service import ActionGraphService
from backend.app.services.auth_service import create_user_session
from backend.tests.integration.test_database import db_session, test_engine

client = TestClient(app)


def test_graph_api_unauthenticated_returns_401():
    response = client.get("/api/v1/graph/nodes")
    assert response.status_code == 401


def test_graph_api_nodes_visual_rebuild_flow(db_session: Session):
    user = User(
        email=f"graph_api_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Graph API User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    session_token, _ = create_user_session(db_session, user)

    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"thread_gapi_{uuid.uuid4().hex[:8]}",
        snippet="GAPI Thread",
    )
    db_session.add(thread)
    db_session.commit()

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_gapi_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="pm@company.com",
        subject="Release Roadmap Q4",
        body_plain="Please finalize Q4 roadmap tasks.",
        has_attachments=False,
    )
    db_session.add(message)
    db_session.commit()

    ai_analysis = AIAnalysis(
        user_id=user.id,
        email_message_id=message.id,
        email_thread_id=thread.id,
        summary="Summary of Q4 roadmap",
        intent="WORK_REQUEST",
        priority="HIGH",
        sentiment="NEUTRAL",
        confidence_score=0.95,
        rationale="Roadmap task finalization needed.",
        model_name="mock-model",
        prompt_version="1.0.0",
        status="COMPLETED",
    )
    db_session.add(ai_analysis)
    db_session.commit()


    action = ExtractedAction(
        user_id=user.id,
        ai_analysis_id=ai_analysis.id,
        email_message_id=message.id,
        email_thread_id=thread.id,
        item_type="TASK",
        description="Finalize Q4 roadmap tasks",
        assignee="Bob",
        severity_or_priority="HIGH",
        confidence_score=0.95,
    )
    db_session.add(action)
    db_session.commit()

    # Pre-sync nodes
    action_node = ActionGraphService.sync_action_nodes(db_session, user.id, action.id)

    cookies = {"mailops_session": session_token}

    # Test GET /api/v1/graph/nodes
    get_nodes = client.get("/api/v1/graph/nodes", cookies=cookies)
    assert get_nodes.status_code == 200
    nodes_data = get_nodes.json()
    assert len(nodes_data) >= 1

    # Test GET /api/v1/graph/visual
    get_vis = client.get("/api/v1/graph/visual", cookies=cookies)
    assert get_vis.status_code == 200
    vis_data = get_vis.json()
    assert "nodes" in vis_data
    assert "edges" in vis_data

    # Test GET /api/v1/graph/dependencies/{action_id}
    get_dep = client.get(f"/api/v1/graph/dependencies/{action.id}", cookies=cookies)
    assert get_dep.status_code == 200
    dep_data = get_dep.json()
    assert dep_data["action_id"] == str(action.id)

    # Test POST /api/v1/graph/rebuild
    post_rebuild = client.post("/api/v1/graph/rebuild", cookies=cookies)
    assert post_rebuild.status_code == 200
    assert post_rebuild.json()["status"] == "ok"
