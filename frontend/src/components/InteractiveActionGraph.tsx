import React, { useEffect, useRef, useState } from 'react';
import { GraphEdgeResult, GraphNodeResult } from '../types/graph';

interface VisualNode extends GraphNodeResult {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface InteractiveActionGraphProps {
  nodes?: GraphNodeResult[];
  edges?: GraphEdgeResult[];
  onNodeClick?: (node: GraphNodeResult) => void;
  selectedNodeId?: string | null;
}

export const InteractiveActionGraph: React.FC<InteractiveActionGraphProps> = ({
  nodes = [],
  edges = [],
  onNodeClick,
  selectedNodeId,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [visualNodes, setVisualNodes] = useState<VisualNode[]>([]);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [draggedNode, setDraggedNode] = useState<VisualNode | null>(null);

  // Initialize nodes in circular/distributed layout
  useEffect(() => {
    const width = 800;
    const height = 450;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) * 0.65;

    const vNodes: VisualNode[] = nodes.map((n, i) => {
      const angle = (i / Math.max(1, nodes.length)) * 2 * Math.PI;
      return {
        ...n,
        x: centerX + radius * Math.cos(angle) + (Math.random() - 0.5) * 40,
        y: centerY + radius * Math.sin(angle) + (Math.random() - 0.5) * 40,
        vx: 0,
        vy: 0,
      };
    });

    setVisualNodes(vNodes);
  }, [nodes]);

  // Canvas render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();

      // Pan & Zoom transform
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);

      // Map nodes by id for quick edge lookup
      const nodeMap = new Map<string, VisualNode>();
      visualNodes.forEach((n) => nodeMap.set(n.id, n));

      // 1. Draw Edges
      edges.forEach((edge) => {
        const src = nodeMap.get(edge.source_node_id);
        const tgt = nodeMap.get(edge.target_node_id);
        if (!src || !tgt) return;

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = '#27272a'; // zinc-800
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Edge label (relationship type)
        const midX = (src.x + tgt.x) / 2;
        const midY = (src.y + tgt.y) / 2;
        ctx.fillStyle = '#a1a1aa'; // zinc-400
        ctx.font = '9px sans-serif';
        ctx.fillText(edge.relationship_type, midX, midY - 4);
      });

      // 2. Draw Nodes
      visualNodes.forEach((n) => {
        const isSelected = selectedNodeId === n.id;
        const radius = isSelected ? 22 : 18;

        // Node fill color by type
        let fillColor = '#18181b'; // zinc-900
        let strokeColor = '#71717a'; // zinc-500
        if (n.node_type === 'ACTION_ITEM') {
          fillColor = '#991b1b'; // red-800
          strokeColor = '#dc2626'; // red-600
        } else if (n.node_type === 'EMAIL_MESSAGE' || n.node_type === 'EMAIL_THREAD') {
          fillColor = '#27272a'; // zinc-800
          strokeColor = '#a1a1aa'; // zinc-400
        } else if (n.node_type === 'INVOICE') {
          fillColor = '#18181b'; // zinc-900
          strokeColor = '#dc2626'; // red-600
        } else if (n.node_type === 'CONTRACT') {
          fillColor = '#27272a'; // zinc-800
          strokeColor = '#991b1b'; // red-800
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.lineWidth = isSelected ? 3 : 1.5;
        ctx.strokeStyle = isSelected ? '#dc2626' : strokeColor; // red-600 if selected
        ctx.stroke();

        // Label
        ctx.fillStyle = '#f8fafc';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        const labelText = n.label.length > 16 ? n.label.substring(0, 14) + '...' : n.label;
        ctx.fillText(labelText, n.x, n.y + radius + 12);
      });

      ctx.restore();
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animationFrameId);
  }, [visualNodes, edges, pan, zoom, selectedNodeId]);

  // Mouse Interaction handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - pan.x) / zoom;
    const mouseY = (e.clientY - rect.top - pan.y) / zoom;

    // Check if clicked on a node
    const clickedNode = visualNodes.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= 22;
    });

    if (clickedNode) {
      setDraggedNode(clickedNode);
      if (onNodeClick) {
        onNodeClick(clickedNode);
      }
    } else {
      setIsDraggingCanvas(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (draggedNode) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - pan.x) / zoom;
      const mouseY = (e.clientY - rect.top - pan.y) / zoom;

      setVisualNodes((prev) =>
        prev.map((n) => (n.id === draggedNode.id ? { ...n, x: mouseX, y: mouseY } : n))
      );
    } else if (isDraggingCanvas) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setDraggedNode(null);
    setIsDraggingCanvas(false);
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = 1.1;
    if (e.deltaY < 0) {
      setZoom((z) => Math.min(z * zoomFactor, 2.5));
    } else {
      setZoom((z) => Math.max(z / zoomFactor, 0.5));
    }
  };

  return (
    <div className="relative w-full rounded-xl bg-black border border-zinc-800 overflow-hidden select-none">
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2 bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 px-3 py-1.5 rounded-lg text-xs text-zinc-300">
        <span className="font-semibold text-red-400">Interactive Canvas:</span>
        <span>Drag nodes • Pan canvas • Scroll to zoom</span>
      </div>

      <div className="absolute top-3 right-3 z-10 flex items-center gap-1 bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 p-1 rounded-lg">
        <button
          onClick={() => setZoom((z) => Math.min(z * 1.2, 2.5))}
          className="px-2 py-1 text-xs hover:bg-zinc-800 rounded text-zinc-300"
          title="Zoom In"
        >
          ➕
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(z / 1.2, 0.5))}
          className="px-2 py-1 text-xs hover:bg-zinc-800 rounded text-zinc-300"
          title="Zoom Out"
        >
          ➖
        </button>
        <button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          className="px-2 py-1 text-xs hover:bg-zinc-800 rounded text-zinc-300 font-mono"
          title="Reset View"
        >
          Reset
        </button>
      </div>

      <canvas
        ref={canvasRef}
        width={800}
        height={420}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        className="w-full h-[420px] cursor-grab active:cursor-grabbing block"
      />
    </div>
  );
};
