import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.api.v1.auth import get_current_user
from backend.app.db.session import get_db
from backend.app.models.business_document_extraction import BusinessDocumentExtraction
from backend.app.models.email_message import EmailMessage
from backend.app.models.extracted_action import ExtractedAction
from backend.app.models.graph_edge import GraphEdge
from backend.app.models.graph_node import GraphNode
from backend.app.models.user import User
from backend.app.schemas.graph import (
    DependencyChainResponse,
    GraphEdgeRead,
    GraphNetworkResponse,
    GraphNodeRead,
)
from backend.app.services.action_graph_service import ActionGraphService

router = APIRouter(prefix="/graph", tags=["Action Graph & Relationships"])


@router.get("/nodes", response_model=list[GraphNodeRead])
async def get_graph_nodes(
    node_type: str | None = Query(default=None, description="Optional node type filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Action Graph nodes strictly scoped to current user."""
    query = db.query(GraphNode).filter(GraphNode.user_id == current_user.id)
    if node_type:
        query = query.filter(GraphNode.node_type == node_type)
    return query.all()


@router.get("/edges", response_model=list[GraphEdgeRead])
async def get_graph_edges(
    relationship_type: str | None = Query(default=None, description="Optional edge relationship filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Action Graph edges strictly scoped to current user."""
    query = db.query(GraphEdge).filter(GraphEdge.user_id == current_user.id)
    if relationship_type:
        query = query.filter(GraphEdge.relationship_type == relationship_type)
    return query.all()


@router.get("/visual", response_model=GraphNetworkResponse)
async def get_graph_network_visualization(
    node_type: str | None = Query(default=None, description="Filter nodes by type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve graph nodes and edges payload formatted for network visualization."""
    nodes, edges = ActionGraphService.get_user_network(db=db, user_id=current_user.id, node_type=node_type)
    return GraphNetworkResponse(nodes=nodes, edges=edges)


@router.get("/dependencies/{action_id}", response_model=DependencyChainResponse)
async def get_action_dependency_chain(
    action_id: uuid.UUID,
    depth: int | None = Query(default=None, ge=1, le=20, description="Max BFS traversal depth"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute BFS traversal to resolve blocking dependency chain for an action item."""
    try:
        root_node, blocking_nodes, dependency_edges = ActionGraphService.get_dependency_chain(
            db=db,
            user_id=current_user.id,
            action_id=action_id,
            max_depth=depth,
        )
        return DependencyChainResponse(
            action_id=action_id,
            action_label=root_node.label,
            blocking_nodes=blocking_nodes,
            dependency_edges=dependency_edges,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dependency chain resolution failed: {exc}",
        )


@router.post("/rebuild")
async def rebuild_user_graph(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync and rebuild Action Graph nodes and edges across all user messages and extracted actions."""
    messages = db.query(EmailMessage).filter(EmailMessage.user_id == current_user.id).all()
    actions = db.query(ExtractedAction).filter(ExtractedAction.user_id == current_user.id).all()

    synced_messages = 0
    synced_actions = 0

    for msg in messages:
        ActionGraphService.sync_message_nodes(db, current_user.id, msg.id)
        synced_messages += 1

    for act in actions:
        ActionGraphService.sync_action_nodes(db, current_user.id, act.id)
        synced_actions += 1

    return {
        "status": "ok",
        "synced_messages": synced_messages,
        "synced_actions": synced_actions,
    }
