import React, { useEffect, useState } from 'react';
import {
  Network,
  RefreshCw,
  Search,
  Zap,
  Grid,
  GitCommit,
} from 'lucide-react';
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
    <div className="space-y-5 font-sans">
      <div className="flex flex-wrap items-center justify-between border-b border-white/[0.06] pb-3.5 gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2 tracking-tight">
            <span>Action Graph & Relationship Workspace</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.04] text-zinc-400 border border-white/[0.08] tracking-wider">
              BFS Dependency Engine
            </span>
          </h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            Visualize relational dependencies across email threads, action items, documents, and risks with BFS traversal.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRebuildGraph}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white shadow-sm transition disabled:opacity-50 active:scale-95"
            title="Scan all synced emails and actions to construct the dependency graph"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Syncing...' : 'Auto-Generate Graph'}</span>
          </button>

          <div className="flex items-center gap-1 bg-[#121216] border border-white/[0.06] p-1 rounded-lg text-xs">
            <button
              onClick={() => setViewMode('canvas')}
              className={`px-2.5 py-1 rounded-md font-medium transition flex items-center gap-1 ${
                viewMode === 'canvas'
                  ? 'bg-white/[0.08] text-white border border-white/[0.12] shadow-sm font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Network className="w-3 h-3 text-red-400" />
              <span>Canvas</span>
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`px-2.5 py-1 rounded-md font-medium transition flex items-center gap-1 ${
                viewMode === 'grid'
                  ? 'bg-white/[0.08] text-white border border-white/[0.12] shadow-sm font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Grid className="w-3 h-3 text-zinc-400" />
              <span>Grid</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 bg-[#0e0e12] border border-white/[0.07] p-3 rounded-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
        <div className="flex flex-wrap items-center gap-1 text-xs">
          <span className="text-zinc-500 text-[10px] uppercase font-semibold tracking-wider mr-1">Filter:</span>
          {[
            { id: 'ALL', label: 'All' },
            { id: 'ACTION_ITEM', label: 'Actions' },
            { id: 'EMAIL_THREAD', label: 'Threads' },
            { id: 'DOCUMENT', label: 'Documents' },
            { id: 'DECISION', label: 'Decisions' },
            { id: 'RISK', label: 'Risks' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setNodeTypeFilter(cat.id)}
              className={`px-2.5 py-1 rounded-md font-medium transition ${
                nodeTypeFilter === cat.id
                  ? 'bg-white/[0.08] text-white border border-white/[0.12] font-semibold shadow-sm'
                  : 'bg-white/[0.02] text-zinc-400 hover:text-white border border-white/[0.05]'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3 h-3 text-zinc-500 absolute left-2.5 top-2" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#121216] border border-white/[0.07] rounded-lg text-xs pl-7 pr-3 py-1.5 text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-red-500/60 w-44 transition"
            />
          </div>
          <span className="text-[10px] text-zinc-500 font-mono px-2 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] tabular-nums">
            {filteredNodes.length}/{nodes.length}
          </span>
        </div>
      </div>

      {/* Visual Canvas or Empty State */}
      {nodes.length === 0 && !isLoading ? (
        <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-10 text-center space-y-4 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
          <div className="mx-auto w-12 h-12 rounded-xl bg-white/[0.03] border border-white/[0.07] flex items-center justify-center text-red-500">
            <Network className="w-6 h-6" />
          </div>
          <div className="max-w-xl mx-auto space-y-1">
            <h3 className="text-sm font-semibold text-white">Action Graph Not Yet Generated</h3>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Action Graph automatically maps relationships between your emails, extracted action items, stakeholders, decisions, and risks into a navigable knowledge and dependency graph.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-3xl mx-auto text-left pt-2">
            <div className="bg-[#0a0a0d] p-3.5 rounded-lg border border-white/[0.06]">
              <Zap className="w-4 h-4 text-red-400" />
              <h4 className="text-xs font-medium text-zinc-200 mt-2">Action Dependencies</h4>
              <p className="text-[11px] text-zinc-500 mt-0.5">
                Identifies which tasks depend on prerequisites before processing.
              </p>
            </div>
            <div className="bg-[#0a0a0d] p-3.5 rounded-lg border border-white/[0.06]">
              <Search className="w-4 h-4 text-zinc-400" />
              <h4 className="text-xs font-medium text-zinc-200 mt-2">BFS Path Traversal</h4>
              <p className="text-[11px] text-zinc-500 mt-0.5">
                Walks multi-hop dependency chains to find root-cause blockers.
              </p>
            </div>
            <div className="bg-[#0a0a0d] p-3.5 rounded-lg border border-white/[0.06]">
              <GitCommit className="w-4 h-4 text-red-400" />
              <h4 className="text-xs font-medium text-zinc-200 mt-2">Stakeholder Mapping</h4>
              <p className="text-[11px] text-zinc-500 mt-0.5">
                Links senders, recipients, and assignees directly to their tasks.
              </p>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={handleRebuildGraph}
              disabled={isLoading}
              className="px-5 py-2 rounded-lg text-xs font-medium bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white shadow-sm transition inline-flex items-center gap-1.5 active:scale-95"
            >
              <Zap className="w-3.5 h-3.5" />
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
        <div className="bg-[#0e0e12] border border-red-500/20 rounded-xl p-4 shadow-sm space-y-3 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
            <h3 className="text-xs font-semibold text-white tracking-tight flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-red-400" />
              <span>BFS Dependency Chain Resolution</span>
            </h3>
            <span className="text-[10px] bg-red-950/40 text-red-400 font-mono px-2 py-0.5 rounded-full border border-red-500/20">
              Action: {dependencyChain.action_label}
            </span>
          </div>

          <div className="space-y-1.5 text-xs">
            <span className="text-zinc-500 font-medium block text-[11px]">
              Blocking Prerequisite Nodes ({dependencyChain.blocking_nodes.length}):
            </span>

            {dependencyChain.blocking_nodes.length === 0 ? (
              <p className="text-zinc-500 italic">No prerequisite blocking nodes identified for this action item.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {dependencyChain.blocking_nodes.map((node) => (
                  <div key={node.id} className="bg-[#0a0a0d] p-3 rounded-lg border border-white/[0.05] space-y-0.5">
                    <span className="text-[10px] font-mono text-red-400 uppercase tracking-wider block">
                      {node.node_type}
                    </span>
                    <p className="font-medium text-zinc-100">{node.label}</p>
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
