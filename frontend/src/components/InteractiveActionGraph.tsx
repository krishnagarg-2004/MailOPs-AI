import React, { useEffect, useRef, useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Move } from 'lucide-react';
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
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
        ctx.lineWidth = 1.2;
        ctx.stroke();

        // Edge label (relationship type)
        const midX = (src.x + tgt.x) / 2;
        const midY = (src.y + tgt.y) / 2;
        ctx.fillStyle = '#71717a';
        ctx.font = '9px monospace';
        ctx.fillText(edge.relationship_type, midX, midY - 4);
      });

      // 2. Draw Nodes
      visualNodes.forEach((n) => {
        const isSelected = selectedNodeId === n.id;
        const radius = isSelected ? 20 : 16;

        let fillColor = '#121216';
        let strokeColor = 'rgba(255, 255, 255, 0.15)';
        if (n.node_type === 'ACTION_ITEM') {
          fillColor = '#450a0a';
          strokeColor = '#ef4444';
        } else if (n.node_type === 'EMAIL_MESSAGE' || n.node_type === 'EMAIL_THREAD') {
          fillColor = '#18181f';
          strokeColor = 'rgba(255, 255, 255, 0.2)';
        } else if (n.node_type === 'INVOICE') {
          fillColor = '#1e1b4b';
          strokeColor = '#818cf8';
        } else if (n.node_type === 'CONTRACT') {
          fillColor = '#14532d';
          strokeColor = '#4ade80';
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.lineWidth = isSelected ? 2.5 : 1;
        ctx.strokeStyle = isSelected ? '#ef4444' : strokeColor;
        ctx.stroke();

        // Label
        ctx.fillStyle = '#ededed';
        ctx.font = '10px -apple-system, sans-serif';
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
    <div className="relative w-full rounded-xl bg-[#0a0a0d] border border-white/[0.07] overflow-hidden select-none shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
      <div className="absolute top-3 left-3 z-10 flex items-center gap-1.5 bg-[#0f0f12]/90 backdrop-blur-md border border-white/[0.08] px-2.5 py-1 rounded-md text-[11px] text-zinc-400 shadow-sm">
        <span className="font-medium text-white flex items-center gap-1">
          <Move className="w-3 h-3 text-red-400" />
          Interactive Canvas:
        </span>
        <span className="hidden sm:inline">Drag nodes • Pan canvas • Scroll to zoom</span>
      </div>

      <div className="absolute top-3 right-3 z-10 flex items-center gap-1 bg-[#0f0f12]/90 backdrop-blur-md border border-white/[0.08] p-1 rounded-md shadow-sm">
        <button
          onClick={() => setZoom((z) => Math.min(z * 1.2, 2.5))}
          className="p-1 hover:bg-white/[0.06] rounded text-zinc-300 transition"
          title="Zoom In"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(z / 1.2, 0.5))}
          className="p-1 hover:bg-white/[0.06] rounded text-zinc-300 transition"
          title="Zoom Out"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          className="p-1 hover:bg-white/[0.06] rounded text-zinc-300 transition"
          title="Reset View"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      <canvas
        ref={canvasRef}
        width={800}
        height={450}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        className="w-full h-[450px] cursor-grab active:cursor-grabbing block"
      />
    </div>
  );
};
