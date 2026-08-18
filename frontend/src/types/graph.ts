export type NodeTypeEnum =
  | 'EMAIL_MESSAGE'
  | 'EMAIL_THREAD'
  | 'ACTION_ITEM'
  | 'INVOICE'
  | 'CONTRACT'
  | 'PERSON'
  | 'ORGANIZATION'
  | 'PROJECT';

export type RelationshipTypeEnum =
  | 'DEPENDS_ON'
  | 'BLOCKED_BY'
  | 'EXTRACTED_FROM'
  | 'REFERENCES'
  | 'ASSIGNED_TO'
  | 'ASSOCIATED_WITH'
  | 'SUPERSEDES';

export interface GraphNodeResult {
  id: string;
  user_id: string;
  node_type: NodeTypeEnum;
  label: string;
  entity_reference_id?: string;
  properties: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface GraphEdgeResult {
  id: string;
  user_id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: RelationshipTypeEnum;
  weight: number;
  properties: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface GraphNetworkResponse {
  nodes: GraphNodeResult[];
  edges: GraphEdgeResult[];
}

export interface DependencyChainResponse {
  action_id: string;
  action_label: string;
  blocking_nodes: GraphNodeResult[];
  dependency_edges: GraphEdgeResult[];
}
