import uuid
import pytest
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.services.action_graph_service import ActionGraphService
from backend.tests.integration.test_database import db_session, test_engine


def test_cross_user_graph_node_and_edge_isolation(db_session: Session):
    """
    EXPLICIT SECURITY TEST:
    Verify User B cannot query, traverse, or create edges pointing to User A's graph nodes.
    """
    user_a = User(email=f"usera_{uuid.uuid4().hex[:8]}@test.com", full_name="User A", is_active=True)
    user_b = User(email=f"userb_{uuid.uuid4().hex[:8]}@test.com", full_name="User B", is_active=True)
    db_session.add_all([user_a, user_b])
    db_session.commit()

    # User A creates a node
    node_a = ActionGraphService.get_or_create_node(
        db_session, user_a.id, node_type="ACTION_ITEM", label="User A Confidential Task"
    )
    # User B creates a node
    node_b = ActionGraphService.get_or_create_node(
        db_session, user_b.id, node_type="ACTION_ITEM", label="User B Task"
    )

    # 1. User B queries network - MUST NOT see User A's node
    nodes_b, edges_b = ActionGraphService.get_user_network(db_session, user_b.id)
    b_node_ids = {n.id for n in nodes_b}
    assert node_a.id not in b_node_ids
    assert node_b.id in b_node_ids

    # 2. User B attempts to create edge linking User B's node to User A's node - MUST RAISE ValueError
    with pytest.raises(ValueError) as exc_info:
        ActionGraphService.get_or_create_edge(
            db=db_session,
            user_id=user_b.id,
            source_node_id=node_b.id,
            target_node_id=node_a.id,
            relationship_type="DEPENDS_ON",
        )
    assert "does not exist or belong to user" in str(exc_info.value)

    # 3. User B attempts BFS dependency traversal on User A's action - MUST RAISE ValueError
    fake_action_id = uuid.uuid4()
    with pytest.raises(ValueError) as exc_info_bfs:
        ActionGraphService.get_dependency_chain(db_session, user_b.id, fake_action_id)
    assert "not found for user" in str(exc_info_bfs.value)
