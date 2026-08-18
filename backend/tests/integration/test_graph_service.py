import uuid
import pytest
from sqlalchemy.orm import Session
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.email_message import EmailMessage
from backend.app.models.email_thread import EmailThread
from backend.app.models.extracted_action import ExtractedAction

from backend.app.models.user import User
from backend.app.services.action_graph_service import ActionGraphService
from backend.tests.integration.test_database import db_session, test_engine


@pytest.fixture
def sample_graph_data(db_session: Session):
    user = User(
        email=f"graph_user_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Graph User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    thread = EmailThread(
        user_id=user.id,
        gmail_thread_id=f"thread_g_{uuid.uuid4().hex[:8]}",
        snippet="Graph Thread",
    )
    db_session.add(thread)
    db_session.commit()

    message = EmailMessage(
        user_id=user.id,
        thread_id=thread.id,
        gmail_message_id=f"msg_g_{uuid.uuid4().hex[:8]}",
        gmail_thread_id=thread.gmail_thread_id,
        sender="boss@corp.com",
        subject="Project Launch Approval",
        body_plain="Please review and approve the project launch budget.",
        has_attachments=False,
    )
    db_session.add(message)
    db_session.commit()

    ai_analysis = AIAnalysis(
        user_id=user.id,
        email_message_id=message.id,
        email_thread_id=thread.id,
        summary="Summary of budget request",
        intent="WORK_REQUEST",
        priority="HIGH",
        sentiment="NEUTRAL",
        confidence_score=0.9,
        rationale="Budget review required for project launch.",
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
        description="Approve project launch budget",
        assignee="Alice",
        severity_or_priority="HIGH",
        confidence_score=0.9,
    )
    db_session.add(action)
    db_session.commit()


    return user, message, action


def test_action_graph_service_node_and_edge_sync(db_session: Session, sample_graph_data):
    user, message, action = sample_graph_data

    # Test syncing message & action into relational graph
    action_node = ActionGraphService.sync_action_nodes(db_session, user.id, action.id)

    assert action_node is not None
    assert action_node.node_type == "ACTION_ITEM"
    assert action_node.user_id == user.id

    # Verify user network query
    nodes, edges = ActionGraphService.get_user_network(db_session, user.id)
    assert len(nodes) >= 2  # Action node + Email node + Person node
    assert len(edges) >= 1  # EXTRACTED_FROM edge

    # Test dependency chain resolution (BFS)
    root, blocking_nodes, dep_edges = ActionGraphService.get_dependency_chain(db_session, user.id, action.id)
    assert root.id == action_node.id
    assert len(blocking_nodes) >= 1
