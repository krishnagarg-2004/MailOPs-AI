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
      <div className="flex flex-wrap items-center justify-between border-b border-zinc-800 pb-4 gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🕸️ Action Graph & Relationship Workspace</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-red-950/60 text-red-400 border border-red-800/60">
              BFS Dependency Engine
            </span>
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Visualize relational dependencies across email threads, action items, documents, and risks with BFS traversal.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRebuildGraph}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-600 hover:bg-red-500 text-white shadow-md shadow-red-950/50 transition disabled:opacity-50"
            title="Scan all synced emails and actions to construct the dependency graph"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Syncing Graph...</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>Auto-Generate Graph</span>
              </>
            )}
          </button>

          <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 p-1 rounded-lg text-xs">
            <button
              onClick={() => setViewMode('canvas')}
              className={`px-3 py-1 rounded-md font-medium transition ${
                viewMode === 'canvas'
                  ? 'bg-red-950/70 text-red-400 border border-red-800/80 shadow-xs'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              🎨 Interactive Canvas
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 rounded-md font-medium transition ${
                viewMode === 'grid'
                  ? 'bg-red-950/70 text-red-400 border border-red-800/80 shadow-xs'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              📋 Grid Cards
            </button>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-zinc-950 border border-zinc-800 p-3 rounded-xl shadow-sm">
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-zinc-400 font-semibold mr-1">Filter Nodes:</span>
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
                  ? 'bg-red-600 text-white font-semibold shadow-sm'
                  : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'
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
            className="bg-zinc-900 border border-zinc-800 rounded-lg text-xs px-3 py-1 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30 w-44"
          />
          <span className="text-[11px] text-zinc-500 font-mono">
            {filteredNodes.length}/{nodes.length} nodes
          </span>
        </div>
      </div>

      {/* Visual Canvas or Empty State Explainer */}
      {nodes.length === 0 && !isLoading ? (
        <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-8 text-center space-y-6">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-red-950/40 border border-red-800/60 flex items-center justify-center text-3xl text-red-500">
            🕸️
          </div>
          <div className="max-w-xl mx-auto space-y-2">
            <h3 className="text-base font-bold text-white">Action Graph is Not Yet Generated</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Action Graph automatically maps relationships between your emails, extracted action items, stakeholders, decisions, and risks into a navigable knowledge and dependency graph.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-3xl mx-auto text-left">
            <div className="bg-zinc-900 p-4 rounded-lg border border-zinc-800">
              <span className="text-lg">⚡</span>
              <h4 className="text-xs font-semibold text-red-400 mt-2">Action Dependencies</h4>
              <p className="text-[11px] text-slate-400 mt-1">
                Identifies which tasks depend on other prerequisites (e.g. review PR before merge, countersign NDA before payment).
              </p>
            </div>
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
              <span className="text-lg">🔍</span>
              <h4 className="text-xs font-semibold text-sky-300 mt-2">BFS Path Traversal</h4>
              <p className="text-[11px] text-slate-400 mt-1">
                Walks multi-hop dependency chains to find root-cause blockers holding up critical business workflows.
              </p>
            </div>
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
              <span className="text-lg">👥</span>
              <h4 className="text-xs font-semibold text-indigo-300 mt-2">Stakeholder Mapping</h4>
              <p className="text-[11px] text-slate-400 mt-1">
                Links senders, recipients, and assignees directly to their corresponding action items and decisions.
              </p>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={handleRebuildGraph}
              disabled={isLoading}
              className="px-6 py-2.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg transition inline-flex items-center gap-2"
            >
              <span>⚡</span>
              <span>Auto-Generate Action Graph from Mailbox</span>
            </button>
          </div>
        </div>
      ) : viewMode === 'canvas' ? (
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
