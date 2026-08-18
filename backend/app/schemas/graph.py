from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, Field


class NodeTypeEnum(str, Enum):
    EMAIL_MESSAGE = "EMAIL_MESSAGE"
    EMAIL_THREAD = "EMAIL_THREAD"
    ACTION_ITEM = "ACTION_ITEM"
    INVOICE = "INVOICE"
    CONTRACT = "CONTRACT"
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    PROJECT = "PROJECT"


class RelationshipTypeEnum(str, Enum):
    DEPENDS_ON = "DEPENDS_ON"
    BLOCKED_BY = "BLOCKED_BY"
    EXTRACTED_FROM = "EXTRACTED_FROM"
    REFERENCES = "REFERENCES"
    ASSIGNED_TO = "ASSIGNED_TO"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    SUPERSEDES = "SUPERSEDES"


class GraphNodeRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    node_type: str
    label: str
    entity_reference_id: uuid.UUID | None = None
    properties: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphEdgeRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID
    relationship_type: str
    weight: float
    properties: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphNetworkResponse(BaseModel):
    nodes: list[GraphNodeRead]
    edges: list[GraphEdgeRead]


class DependencyChainResponse(BaseModel):
    action_id: uuid.UUID
    action_label: str
    blocking_nodes: list[GraphNodeRead]
    dependency_edges: list[GraphEdgeRead]
