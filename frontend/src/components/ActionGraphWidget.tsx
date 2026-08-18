import React, { useState } from 'react';
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

  const filteredNodes = filterType === 'ALL'
    ? nodes
    : nodes.filter((n) => n.node_type === filterType);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'ACTION_ITEM':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'EMAIL_MESSAGE':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      case 'INVOICE':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'CONTRACT':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'PERSON':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const handleNodeSelect = (node: GraphNodeResult) => {
    setSelectedNode(node);
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 text-slate-100 font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-amber-400">
            Action Graph & Relationship Layer
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Relational dependency map ({nodes.length} nodes, {edges.length} edges)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded text-xs px-2.5 py-1 text-slate-200 focus:outline-none"
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
            className="text-xs bg-amber-600/20 text-amber-300 border border-amber-500/40 px-3 py-1 rounded hover:bg-amber-600/30 transition font-medium disabled:opacity-50"
          >
            {isLoading ? 'Rebuilding...' : 'Rebuild Graph'}
          </button>
        </div>
      </div>

      {/* Node Grid Layout Representation */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-80 overflow-y-auto pr-1">
        {filteredNodes.map((node) => (
          <div
            key={node.id}
            onClick={() => handleNodeSelect(node)}
            className={`border rounded-lg p-3 cursor-pointer transition hover:scale-[1.01] ${getNodeColor(node.node_type)} ${
              selectedNode?.id === node.id ? 'ring-2 ring-amber-400' : ''
            }`}
          >
            <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider uppercase mb-1">
              <span>{node.node_type}</span>
            </div>
            <div className="font-semibold text-xs text-slate-100 truncate">{node.label}</div>
          </div>
        ))}
      </div>

      {/* Selected Node Drawer */}
      {selectedNode && (
        <div className="bg-slate-950 p-4 rounded-xl border border-amber-500/30 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-amber-400">Node Properties ({selectedNode.node_type})</span>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-slate-200 text-xs"
            >
              ✕ Close
            </button>
          </div>
          <p className="font-semibold text-slate-100">{selectedNode.label}</p>
          <pre className="bg-slate-900 p-2.5 rounded font-mono text-[11px] text-slate-300 overflow-x-auto">
            {JSON.stringify(selectedNode.properties, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
