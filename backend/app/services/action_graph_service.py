from collections import deque
import logging
import uuid
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.email_message import EmailMessage
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.graph_edge import GraphEdge
from backend.app.models.graph_node import GraphNode

logger = logging.getLogger(__name__)


class ActionGraphService:
    """Service for building and traversing the relational Action Graph in PostgreSQL with strict user isolation."""

    @classmethod
    def get_or_create_node(
        cls,
        db: Session,
        user_id: uuid.UUID,
        node_type: str,
        label: str,
        entity_reference_id: uuid.UUID | None = None,
        properties: dict | None = None,
    ) -> GraphNode:
        """Fetch existing or create graph node enforcing strict user_id scoping."""
        query = db.query(GraphNode).filter(
            GraphNode.user_id == user_id,
            GraphNode.node_type == node_type,
        )
        if entity_reference_id:
            query = query.filter(GraphNode.entity_reference_id == entity_reference_id)
        else:
            query = query.filter(GraphNode.label == label)

        existing = query.first()
        if existing:
            return existing

        node = GraphNode(
            user_id=user_id,
            node_type=node_type,
            label=label,
            entity_reference_id=entity_reference_id,
            properties=properties or {},
        )
        db.add(node)
        db.flush()
        return node

    @classmethod
    def get_or_create_edge(
        cls,
        db: Session,
        user_id: uuid.UUID,
        source_node_id: uuid.UUID,
        target_node_id: uuid.UUID,
        relationship_type: str,
        weight: float = 1.0,
        properties: dict | None = None,
    ) -> GraphEdge:
        """Fetch existing or create graph edge enforcing strict user_id scoping and composite unique constraint."""
        # Verify both source and target nodes belong to this user
        src = db.query(GraphNode).filter(GraphNode.id == source_node_id, GraphNode.user_id == user_id).first()
        tgt = db.query(GraphNode).filter(GraphNode.id == target_node_id, GraphNode.user_id == user_id).first()
        if not src or not tgt:
            raise ValueError("Source or target node does not exist or belong to user.")

        existing = (
            db.query(GraphEdge)
            .filter(
                GraphEdge.user_id == user_id,
                GraphEdge.source_node_id == source_node_id,
                GraphEdge.target_node_id == target_node_id,
                GraphEdge.relationship_type == relationship_type,
            )
            .first()
        )
        if existing:
            return existing

        edge = GraphEdge(
            user_id=user_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            weight=weight,
            properties=properties or {},
        )
        db.add(edge)
        db.flush()
        return edge

    @classmethod
    def sync_message_nodes(cls, db: Session, user_id: uuid.UUID, message_id: uuid.UUID) -> GraphNode:
        """Build graph nodes and relationships for an EmailMessage."""
        msg = db.query(EmailMessage).filter(EmailMessage.id == message_id, EmailMessage.user_id == user_id).first()
        if not msg:
            raise ValueError(f"Email message {message_id} not found for user {user_id}")

        # 1. Create EMAIL_MESSAGE node referencing existing domain entity
        email_node = cls.get_or_create_node(
            db=db,
            user_id=user_id,
            node_type="EMAIL_MESSAGE",
            label=f"Email: {msg.subject or 'No Subject'}",
            entity_reference_id=msg.id,
            properties={"sender": msg.sender, "received_at": msg.received_at.isoformat() if msg.received_at else None},
        )

        # 2. Create PERSON node for sender and connect ASSOCIATED_WITH edge
        if msg.sender:
            sender_node = cls.get_or_create_node(
                db=db,
                user_id=user_id,
                node_type="PERSON",
                label=msg.sender,
                properties={"email": msg.sender},
            )
            cls.get_or_create_edge(
                db=db,
                user_id=user_id,
                source_node_id=email_node.id,
                target_node_id=sender_node.id,
                relationship_type="ASSOCIATED_WITH",
            )

        db.commit()
        return email_node

    @classmethod
    def sync_action_nodes(cls, db: Session, user_id: uuid.UUID, action_id: uuid.UUID) -> GraphNode:
        """Build graph nodes and relationships for an ExtractedAction."""
        action = db.query(ExtractedAction).filter(ExtractedAction.id == action_id, ExtractedAction.user_id == user_id).first()
        if not action:
            raise ValueError(f"Extracted action {action_id} not found for user {user_id}")

        # 1. Create ACTION_ITEM node referencing existing domain entity
        action_node = cls.get_or_create_node(
            db=db,
            user_id=user_id,
            node_type="ACTION_ITEM",
            label=action.description[:60],
            entity_reference_id=action.id,
            properties={
                "item_type": action.item_type,
                "status": action.status,
                "severity_or_priority": action.severity_or_priority,
            },
        )

        # 2. Connect EXTRACTED_FROM edge to parent EmailMessage node
        if action.email_message_id:
            email_node = cls.get_or_create_node(
                db=db,
                user_id=user_id,
                node_type="EMAIL_MESSAGE",
                label=f"Email: {action.email_message_id}",
                entity_reference_id=action.email_message_id,
            )
            cls.get_or_create_edge(
                db=db,
                user_id=user_id,
                source_node_id=action_node.id,
                target_node_id=email_node.id,
                relationship_type="EXTRACTED_FROM",
            )

        # 3. Connect ASSIGNED_TO edge if assignee person exists
        if action.assignee:
            assignee_node = cls.get_or_create_node(
                db=db,
                user_id=user_id,
                node_type="PERSON",
                label=action.assignee,
                properties={"name": action.assignee},
            )
            cls.get_or_create_edge(
                db=db,
                user_id=user_id,
                source_node_id=action_node.id,
                target_node_id=assignee_node.id,
                relationship_type="ASSIGNED_TO",
            )

        db.commit()
        return action_node

    @classmethod
    def rebuild_user_graph(cls, db: Session, user_id: uuid.UUID) -> dict:
        """High-performance batch rebuild of the user's action graph using in-memory prefetching and a single commit."""
        messages = db.query(EmailMessage).filter(EmailMessage.user_id == user_id).all()
        actions = db.query(ExtractedAction).filter(ExtractedAction.user_id == user_id).all()

        # Prefetch existing nodes and edges to avoid N+1 queries over remote DB
        existing_nodes = db.query(GraphNode).filter(GraphNode.user_id == user_id).all()
        existing_edges = db.query(GraphEdge).filter(GraphEdge.user_id == user_id).all()

        nodes_by_ref: dict[uuid.UUID, GraphNode] = {n.entity_reference_id: n for n in existing_nodes if n.entity_reference_id}
        nodes_by_type_label: dict[tuple[str, str], GraphNode] = {(n.node_type, n.label): n for n in existing_nodes}
        edges_set: set[tuple[uuid.UUID, uuid.UUID, str]] = {
            (e.source_node_id, e.target_node_id, e.relationship_type) for e in existing_edges
        }

        def get_or_add_node(node_type: str, label: str, entity_ref: uuid.UUID | None = None, props: dict | None = None) -> GraphNode:
            if entity_ref and entity_ref in nodes_by_ref:
                return nodes_by_ref[entity_ref]
            key = (node_type, label)
            if key in nodes_by_type_label:
                return nodes_by_type_label[key]

            new_node = GraphNode(
                user_id=user_id,
                node_type=node_type,
                label=label,
                entity_reference_id=entity_ref,
                properties=props or {},
            )
            db.add(new_node)
            db.flush()
            if entity_ref:
                nodes_by_ref[entity_ref] = new_node
            nodes_by_type_label[key] = new_node
            return new_node

        def get_or_add_edge(src_id: uuid.UUID, tgt_id: uuid.UUID, rel: str) -> None:
            edge_key = (src_id, tgt_id, rel)
            if edge_key in edges_set:
                return
            new_edge = GraphEdge(
                user_id=user_id,
                source_node_id=src_id,
                target_node_id=tgt_id,
                relationship_type=rel,
                weight=1.0,
                properties={},
            )
            db.add(new_edge)
            db.flush()
            edges_set.add(edge_key)

        # 1. Process Messages
        for msg in messages:
            email_node = get_or_add_node(
                node_type="EMAIL_MESSAGE",
                label=f"Email: {msg.subject or 'No Subject'}",
                entity_ref=msg.id,
                props={"sender": msg.sender, "received_at": msg.received_at.isoformat() if msg.received_at else None},
            )
            if msg.sender:
                sender_node = get_or_add_node(
                    node_type="PERSON",
                    label=msg.sender,
                    props={"email": msg.sender},
                )
                get_or_add_edge(email_node.id, sender_node.id, "ASSOCIATED_WITH")

        # 2. Process Actions
        for act in actions:
            action_node = get_or_add_node(
                node_type="ACTION_ITEM",
                label=act.description[:60],
                entity_ref=act.id,
                props={
                    "item_type": act.item_type,
                    "status": act.status,
                    "severity_or_priority": act.severity_or_priority,
                },
            )
            if act.email_message_id and act.email_message_id in nodes_by_ref:
                email_node = nodes_by_ref[act.email_message_id]
                get_or_add_edge(action_node.id, email_node.id, "EXTRACTED_FROM")

            if act.assignee:
                assignee_node = get_or_add_node(
                    node_type="PERSON",
                    label=act.assignee,
                    props={"name": act.assignee},
                )
                get_or_add_edge(action_node.id, assignee_node.id, "ASSIGNED_TO")

        db.commit()

        return {
            "status": "ok",
            "synced_messages": len(messages),
            "synced_actions": len(actions),
        }

    @classmethod
    def get_dependency_chain(
        cls,
        db: Session,
        user_id: uuid.UUID,
        action_id: uuid.UUID,
        max_depth: int | None = None,
    ) -> tuple[GraphNode, list[GraphNode], list[GraphEdge]]:
        """
        Execute Breadth-First Search (BFS) graph traversal to resolve dependency blocking chain up to max_depth.
        Enforces strict user_id multi-tenant isolation.
        """
        limit_depth = max_depth or settings.GRAPH_MAX_TRAVERSAL_DEPTH

        # Find target action node referencing action_id for this user
        root_node = (
            db.query(GraphNode)
            .filter(
                GraphNode.user_id == user_id,
                GraphNode.entity_reference_id == action_id,
                GraphNode.node_type == "ACTION_ITEM",
            )
            .first()
        )
        if not root_node:
            raise ValueError(f"Graph node for action {action_id} not found for user {user_id}")

        visited_nodes: set[uuid.UUID] = {root_node.id}
        blocking_nodes: list[GraphNode] = []
        dependency_edges: list[GraphEdge] = []

        # BFS Queue storing (node_id, current_depth)
        queue: deque[tuple[uuid.UUID, int]] = deque([(root_node.id, 0)])

        while queue:
            curr_id, depth = queue.popleft()
            if depth >= limit_depth:
                continue

            # Query outgoing DEPENDS_ON or BLOCKED_BY edges for current node for user_id
            edges = (
                db.query(GraphEdge)
                .filter(
                    GraphEdge.user_id == user_id,
                    GraphEdge.source_node_id == curr_id,
                    GraphEdge.relationship_type.in_(["DEPENDS_ON", "BLOCKED_BY", "EXTRACTED_FROM"]),
                )
                .all()
            )

            for edge in edges:
                dependency_edges.append(edge)
                target_id = edge.target_node_id
                if target_id not in visited_nodes:
                    visited_nodes.add(target_id)
                    tgt_node = db.query(GraphNode).filter(GraphNode.id == target_id, GraphNode.user_id == user_id).first()
                    if tgt_node:
                        blocking_nodes.append(tgt_node)
                        queue.append((target_id, depth + 1))

        return root_node, blocking_nodes, dependency_edges

    @classmethod
    def get_user_network(
        cls,
        db: Session,
        user_id: uuid.UUID,
        node_type: str | None = None,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Retrieve all graph nodes and edges strictly scoped by user_id."""
        node_query = db.query(GraphNode).filter(GraphNode.user_id == user_id)
        if node_type:
            node_query = node_query.filter(GraphNode.node_type == node_type)

        nodes = node_query.all()
        node_ids = {n.id for n in nodes}

        if not node_ids:
            return [], []

        edges = (
            db.query(GraphEdge)
            .filter(
                GraphEdge.user_id == user_id,
                GraphEdge.source_node_id.in_(node_ids),
                GraphEdge.target_node_id.in_(node_ids),
            )
            .all()
        )

        return nodes, edges
