import React, { useEffect, useState } from 'react';
import { ActionGraphWidget } from '../components/ActionGraphWidget';
import { InteractiveActionGraph } from '../components/InteractiveActionGraph';
import { api } from '../services/api';
import { DependencyChainResponse, GraphEdgeResult, GraphNodeResult } from '../types/graph';

export const ActionGraphView: React.FC = () => {
  const [nodes, setNodes] = useState<GraphNodeResult[]>([]);
  const [edges, setEdges] = useState<GraphEdgeResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'canvas' | 'grid'>('canvas');
  const [dependencyChain, setDependencyChain] = useState<DependencyChainResponse | null>(null);

  // Node Filters
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchGraphData = async () => {
    try {
      setIsLoading(true);
      const res = await api.getGraphVisual();
      setNodes(res.nodes);
      setEdges(res.edges);
    } catch {
      // Ignore background errors
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, []);

  const handleRebuildGraph = async () => {
    try {
      setIsLoading(true);
      await api.rebuildGraph();
      await fetchGraphData();
    } catch (err: any) {
      alert(`Graph Rebuild Error: ${err.message}`);
      setIsLoading(false);
    }
  };

  const handleNodeClick = async (node: GraphNodeResult) => {
    setSelectedNodeId(node.id);
    if (node.node_type === 'ACTION_ITEM' && node.entity_reference_id) {
      try {
        const chain = await api.getGraphDependencies(node.entity_reference_id);
        setDependencyChain(chain);
      } catch {
        setDependencyChain(null);
      }
    } else {
      setDependencyChain(null);
    }
  };

  // Filter nodes by selected type and search query
  const filteredNodes = nodes.filter((n) => {
    const matchesSearch =
      !searchQuery ||
      n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.node_type.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (nodeTypeFilter === 'ALL') return true;
    return n.node_type === nodeTypeFilter;
  });

  const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));

  // Edges are visible only if both source and target are visible
  const filteredEdges = edges.filter(
    (e) => visibleNodeIds.has(e.source_node_id) && visibleNodeIds.has(e.target_node_id)
  );

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Action Graph & Relationship Workspace</h2>
          <p className="text-xs text-slate-400">
            Inspect relational dependencies across emails, actions, invoices, contracts, and people with BFS traversal.
          </p>
        </div>

        <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-lg text-xs">
          <button
            onClick={() => setViewMode('canvas')}
            className={`px-3 py-1 rounded-md font-medium transition ${
              viewMode === 'canvas'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🎨 Interactive Canvas
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1 rounded-md font-medium transition ${
              viewMode === 'grid'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            📋 Grid Cards
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 border border-slate-800 p-3 rounded-xl">
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-slate-400 font-semibold mr-1">Filter Nodes:</span>
          {[
            { id: 'ALL', label: 'All Nodes' },
            { id: 'ACTION_ITEM', label: '⚡ Actions' },
            { id: 'EMAIL_THREAD', label: '📬 Threads' },
            { id: 'DOCUMENT', label: '📄 Documents' },
            { id: 'DECISION', label: '⚖️ Decisions' },
            { id: 'RISK', label: '⚠️ Risks' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setNodeTypeFilter(cat.id)}
              className={`px-2.5 py-1 rounded-md font-medium transition ${
                nodeTypeFilter === cat.id
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search nodes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg text-xs px-3 py-1 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-44"
          />
          <span className="text-[11px] text-slate-500 font-mono">
            {filteredNodes.length}/{nodes.length} nodes
          </span>
        </div>
      </div>

      {/* Visual Canvas Mode */}
      {viewMode === 'canvas' ? (
        <InteractiveActionGraph
          nodes={filteredNodes}
          edges={filteredEdges}
          onNodeClick={handleNodeClick}
          selectedNodeId={selectedNodeId}
        />
      ) : (
        <ActionGraphWidget
          nodes={filteredNodes}
          edges={filteredEdges}
          onNodeClick={handleNodeClick}
          onRebuildGraph={handleRebuildGraph}
          isLoading={isLoading}
        />
      )}

      {/* BFS Dependency Chain Resolution Drawer */}
      {dependencyChain && (
        <div className="bg-slate-900 border border-amber-500/30 rounded-xl p-5 shadow-lg space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-sm font-semibold text-amber-400">
              BFS Dependency Chain Resolution
            </h3>
            <span className="text-xs bg-amber-500/20 text-amber-300 font-mono px-2 py-0.5 rounded">
              Action: {dependencyChain.action_label}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <span className="text-slate-400 font-medium block">
              Blocking Prerequisite Nodes ({dependencyChain.blocking_nodes.length}):
            </span>

            {dependencyChain.blocking_nodes.length === 0 ? (
              <p className="text-slate-500 italic">No prerequisite blocking nodes identified for this action item.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {dependencyChain.blocking_nodes.map((node) => (
                  <div key={node.id} className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                    <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider block">
                      {node.node_type}
                    </span>
                    <p className="font-semibold text-slate-200">{node.label}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
