import React, { useEffect, useState } from 'react';
import { ActionGraphWidget } from '../components/ActionGraphWidget';
import { InteractiveActionGraph } from '../components/InteractiveActionGraph';
import { useToast } from '../context/ToastContext';
import { api } from '../services/api';
import { DependencyChainResponse, GraphEdgeResult, GraphNodeResult } from '../types/graph';

export const ActionGraphView: React.FC = () => {
  const { toast } = useToast();
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
      toast.success('Action graph successfully rebuilt!');
    } catch (err: any) {
      const msg = err?.message === 'Failed to fetch'
        ? 'Connection to backend failed (service may be waking up or restarting). Please retry in a few moments.'
        : (err?.message || 'Rebuild failed');
      toast.error(`Graph Rebuild Error: ${msg}`);
    } finally {
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
      <div className="flex flex-wrap items-center justify-between border-b border-zinc-800/80 pb-4 gap-3">
        <div>
          <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2 tracking-tight">
            <span>Action Graph & Relationship Workspace</span>
            <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-red-950/70 text-red-400 border border-red-800/70 uppercase tracking-wider font-mono">
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
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-medium bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white shadow-md shadow-red-950/50 transition disabled:opacity-50 active:scale-95"
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

          <div className="flex items-center gap-1 bg-zinc-900/90 border border-zinc-800/80 p-1 rounded-xl text-xs">
            <button
              onClick={() => setViewMode('canvas')}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                viewMode === 'canvas'
                  ? 'bg-red-950/80 text-red-400 border border-red-800/80 shadow-xs font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              🎨 Canvas
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                viewMode === 'grid'
                  ? 'bg-red-950/80 text-red-400 border border-red-800/80 shadow-xs font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              📋 Grid
            </button>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-zinc-950/90 border border-zinc-800/80 p-3.5 rounded-2xl shadow-sm">
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
              className={`px-3 py-1 rounded-lg font-medium transition ${
                nodeTypeFilter === cat.id
                  ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white font-semibold shadow-sm'
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
            className="bg-zinc-900/90 border border-zinc-800 rounded-xl text-xs px-3 py-1.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500/80 focus:ring-1 focus:ring-red-500/30 w-48 transition"
          />
          <span className="text-[11px] text-zinc-400 font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800">
            {filteredNodes.length}/{nodes.length}
          </span>
        </div>
      </div>

      {/* Visual Canvas or Empty State */}
      {nodes.length === 0 && !isLoading ? (
        <div className="bg-zinc-950/90 border border-zinc-800/80 rounded-2xl p-10 text-center space-y-6 shadow-xl">
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
            <div className="bg-zinc-900/60 p-4 rounded-xl border border-zinc-800/80">
              <span className="text-lg">⚡</span>
              <h4 className="text-xs font-semibold text-red-400 mt-2">Action Dependencies</h4>
              <p className="text-[11px] text-zinc-400 mt-1">
                Identifies which tasks depend on other prerequisites before merge or processing.
              </p>
            </div>
            <div className="bg-zinc-900/60 p-4 rounded-xl border border-zinc-800/80">
              <span className="text-lg">🔍</span>
              <h4 className="text-xs font-semibold text-zinc-200 mt-2">BFS Path Traversal</h4>
              <p className="text-[11px] text-zinc-400 mt-1">
                Walks multi-hop dependency chains to find root-cause blockers holding up critical workflows.
              </p>
            </div>
            <div className="bg-zinc-900/60 p-4 rounded-xl border border-zinc-800/80">
              <span className="text-lg">👥</span>
              <h4 className="text-xs font-semibold text-red-400 mt-2">Stakeholder Mapping</h4>
              <p className="text-[11px] text-zinc-400 mt-1">
                Links senders, recipients, and assignees directly to their corresponding action items.
              </p>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={handleRebuildGraph}
              disabled={isLoading}
              className="px-6 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white shadow-lg shadow-red-950/60 transition inline-flex items-center gap-2 active:scale-95"
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
        <div className="bg-zinc-950/90 border border-red-800/60 rounded-2xl p-5 shadow-xl space-y-3.5 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2.5">
            <h3 className="text-sm font-semibold text-red-400 tracking-tight">
              BFS Dependency Chain Resolution
            </h3>
            <span className="text-xs bg-red-950/70 text-red-300 font-mono px-2.5 py-0.5 rounded-full border border-red-800/70">
              Action: {dependencyChain.action_label}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <span className="text-zinc-400 font-medium block">
              Blocking Prerequisite Nodes ({dependencyChain.blocking_nodes.length}):
            </span>

            {dependencyChain.blocking_nodes.length === 0 ? (
              <p className="text-zinc-500 italic">No prerequisite blocking nodes identified for this action item.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {dependencyChain.blocking_nodes.map((node) => (
                  <div key={node.id} className="bg-zinc-900/80 p-3.5 rounded-xl border border-zinc-800/80 space-y-1">
                    <span className="text-[10px] font-semibold text-red-400 uppercase tracking-wider block">
                      {node.node_type}
                    </span>
                    <p className="font-semibold text-zinc-100">{node.label}</p>
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
