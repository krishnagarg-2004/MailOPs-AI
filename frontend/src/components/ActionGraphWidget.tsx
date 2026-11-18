import React, { useEffect, useState } from 'react';
import { Grid, RefreshCw, X } from 'lucide-react';
import { GraphEdgeResult, GraphNodeResult } from '../types/graph';

interface ActionGraphWidgetProps {
  nodes?: GraphNodeResult[];
  edges?: GraphEdgeResult[];
  onNodeClick?: (node: GraphNodeResult) => void;
  onRebuildGraph?: () => void;
  isLoading?: boolean;
}

export const ActionGraphWidget: React.FC<ActionGraphWidgetProps> = ({
  nodes = [],
  edges = [],
  onNodeClick,
  onRebuildGraph,
  isLoading = false,
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNodeResult | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');

  useEffect(() => {
    if (
      selectedNode &&
      !nodes.some((node) => node.id === selectedNode.id)
    ) {
      setSelectedNode(null);
    }
  }, [nodes, selectedNode]);

  const filteredNodes = filterType === 'ALL'
    ? nodes
    : nodes.filter((n) => n.node_type === filterType);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'ACTION_ITEM':
        return 'bg-red-950/40 text-red-200 border-red-500/30';
      case 'EMAIL_MESSAGE':
      case 'EMAIL_THREAD':
        return 'bg-white/[0.04] text-zinc-200 border-white/[0.08]';
      case 'INVOICE':
        return 'bg-zinc-900/90 text-red-300 border-red-900/50';
      case 'CONTRACT':
        return 'bg-zinc-800/80 text-zinc-300 border-zinc-700/80';
      case 'PERSON':
        return 'bg-white/[0.03] text-zinc-300 border-white/[0.06]';
      default:
        return 'bg-white/[0.03] text-zinc-300 border-white/[0.06]';
    }
  };

  const handleNodeSelect = (node: GraphNodeResult) => {
    setSelectedNode(node);
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  return (
    <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-4 sm:p-5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] space-y-3.5 text-[#ededed] font-sans">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] pb-3">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-white flex items-center gap-1.5">
            <Grid className="w-3.5 h-3.5 text-red-400" />
            <span>Action Graph Grid</span>
            <span className="text-[10px] text-zinc-500 font-mono">
              ({nodes.length} nodes, {edges.length} edges)
            </span>
          </h3>
          <p className="text-xs text-zinc-500 mt-0.5">
            Relational dependency inventory across emails, actions, documents, and risks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-[#121216] border border-white/[0.07] rounded-lg text-xs px-2.5 py-1.5 text-zinc-200 focus:outline-none focus:border-red-500/60 transition"
          >
            <option value="ALL">All Types</option>
            <option value="ACTION_ITEM">Action Tasks</option>
            <option value="EMAIL_MESSAGE">Emails</option>
            <option value="INVOICE">Invoices</option>
            <option value="CONTRACT">Contracts</option>
            <option value="PERSON">People</option>
          </select>

          <button
            onClick={onRebuildGraph}
            disabled={isLoading}
            className="text-xs bg-white/[0.04] hover:bg-white/[0.08] text-zinc-200 border border-white/[0.08] px-3 py-1.5 rounded-lg transition font-medium disabled:opacity-50 active:scale-95 flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3 h-3 text-red-400 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Rebuilding...' : 'Rebuild'}</span>
          </button>
        </div>
      </div>

      {/* Node Grid Layout */}
      {filteredNodes.length === 0 ? (
        <div className="text-center py-10 text-xs text-zinc-500">
          No nodes found for this filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-96 overflow-y-auto pr-1">
          {filteredNodes.map((node) => (
            <div
              key={node.id}
              onClick={() => handleNodeSelect(node)}
              className={`border rounded-lg p-3 cursor-pointer transition-all duration-150 ${getNodeColor(node.node_type)} ${
                selectedNode?.id === node.id ? 'ring-1 ring-red-500 shadow-sm' : 'hover:border-white/[0.14]'
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono tracking-wider uppercase mb-1 opacity-75">
                <span>{node.node_type}</span>
              </div>
              <div className="font-medium text-xs text-zinc-100 truncate">{node.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Selected Node Drawer */}
      {selectedNode && (
        <div className="bg-[#0a0a0d] p-3.5 rounded-lg border border-white/[0.08] space-y-2 text-xs animate-fadeIn">
          <div className="flex items-center justify-between">
            <span className="font-medium text-red-400 text-xs">Node Properties ({selectedNode.node_type})</span>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-zinc-500 hover:text-white p-1 rounded-md transition"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <p className="font-medium text-zinc-200">{selectedNode.label}</p>
          <pre className="bg-[#121216] p-2.5 rounded-md font-mono text-[11px] text-zinc-300 overflow-x-auto leading-relaxed border border-white/[0.05]">
            {JSON.stringify(selectedNode.properties, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
