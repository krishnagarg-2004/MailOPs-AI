import React, { useEffect, useState } from 'react';
import { ActionGraphWidget } from '../components/ActionGraphWidget';
import { api } from '../services/api';
import { DependencyChainResponse, GraphEdgeResult, GraphNodeResult } from '../types/graph';

export const ActionGraphView: React.FC = () => {
  const [nodes, setNodes] = useState<GraphNodeResult[]>([]);
  const [edges, setEdges] = useState<GraphEdgeResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [dependencyChain, setDependencyChain] = useState<DependencyChainResponse | null>(null);

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

  return (
    <div className="space-y-6 font-sans">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-lg font-bold text-slate-100">Action Graph & Relationship Workspace</h2>
        <p className="text-xs text-slate-400">
          Inspect relational dependencies across emails, actions, invoices, contracts, and people with BFS traversal.
        </p>
      </div>

      {/* Main Action Graph Widget */}
      <ActionGraphWidget
        nodes={nodes}
        edges={edges}
        onNodeClick={handleNodeClick}
        onRebuildGraph={handleRebuildGraph}
        isLoading={isLoading}
      />

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
