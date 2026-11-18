import React, { useEffect, useState } from 'react';
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
        return 'bg-red-950/70 text-red-200 border-red-800/80';
      case 'EMAIL_MESSAGE':
      case 'EMAIL_THREAD':
        return 'bg-zinc-900/80 text-zinc-200 border-zinc-700/80';
      case 'INVOICE':
        return 'bg-red-950/50 text-red-300 border-red-800/60';
      case 'CONTRACT':
        return 'bg-zinc-800/80 text-zinc-300 border-zinc-600/80';
      case 'PERSON':
        return 'bg-zinc-900/80 text-zinc-300 border-zinc-700/80';
      default:
        return 'bg-zinc-900/80 text-zinc-300 border-zinc-800';
    }
  };

  const handleNodeSelect = (node: GraphNodeResult) => {
    setSelectedNode(node);
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  return (
    <div className="bg-zinc-950/90 border border-zinc-800/80 rounded-2xl p-5 shadow-xl space-y-4 text-zinc-100 font-sans">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-red-400">
            Action Graph Grid ({nodes.length} nodes, {edges.length} edges)
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Relational dependency inventory across emails, actions, documents, and risks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-xl text-xs px-3 py-1.5 text-zinc-200 focus:outline-none focus:border-red-500/80 transition"
          >
            <option value="ALL">All Node Types</option>
            <option value="ACTION_ITEM">Action Tasks</option>
            <option value="EMAIL_MESSAGE">Emails</option>
            <option value="INVOICE">Invoices</option>
            <option value="CONTRACT">Contracts</option>
            <option value="PERSON">People</option>
          </select>

          <button
            onClick={onRebuildGraph}
            disabled={isLoading}
            className="text-xs bg-red-950/60 text-red-300 border border-red-800/60 px-3.5 py-1.5 rounded-xl hover:bg-red-900/50 transition font-medium disabled:opacity-50 active:scale-95"
          >
            {isLoading ? 'Rebuilding...' : 'Rebuild Graph'}
          </button>
        </div>
      </div>

      {/* Node Grid Layout */}
      {filteredNodes.length === 0 ? (
        <div className="text-center py-10 text-xs text-zinc-500">
          No nodes found for this filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-96 overflow-y-auto pr-1">
          {filteredNodes.map((node) => (
            <div
              key={node.id}
              onClick={() => handleNodeSelect(node)}
              className={`border rounded-xl p-3.5 cursor-pointer transition-all duration-150 hover:border-zinc-500 ${getNodeColor(node.node_type)} ${
                selectedNode?.id === node.id ? 'ring-2 ring-red-500 shadow-md' : ''
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider uppercase mb-1.5 opacity-80">
                <span>{node.node_type}</span>
              </div>
              <div className="font-semibold text-xs text-zinc-100 truncate">{node.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Selected Node Drawer */}
      {selectedNode && (
        <div className="bg-black/80 p-4 rounded-xl border border-red-800/60 space-y-2 text-xs animate-fadeIn shadow-inner">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-red-400">Node Properties ({selectedNode.node_type})</span>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-zinc-400 hover:text-white text-xs px-2 py-0.5"
            >
              ✕ Close
            </button>
          </div>
          <p className="font-semibold text-zinc-100">{selectedNode.label}</p>
          <pre className="bg-zinc-900/80 p-3 rounded-lg font-mono text-[11px] text-zinc-300 overflow-x-auto leading-relaxed border border-zinc-800">
            {JSON.stringify(selectedNode.properties, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
