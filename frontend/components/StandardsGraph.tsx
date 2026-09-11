'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { getGraphData } from '../lib/api';
import { Network, RefreshCw, Layers } from 'lucide-react';

interface StandardsGraphProps {
  standardId: string;
  onSelectStandard: (standard_id: string) => void;
}

export const StandardsGraph: React.FC<StandardsGraphProps> = ({
  standardId,
  onSelectStandard,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchGraph = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getGraphData(id);
      
      const formattedNodes: Node[] = data.nodes.map((n) => {
        const isMain = n.data.type === 'MAIN';
        return {
          id: n.id,
          position: n.position,
          data: {
            label: (
              <div className={`p-3 rounded-xl border text-center transition shadow-lg ${
                isMain
                  ? 'bg-gradient-to-br from-blue-900 to-indigo-950 border-blue-400 text-white ring-4 ring-blue-500/20'
                  : 'bg-slate-900 border-slate-700 text-slate-200 hover:border-amber-500'
              }`}>
                <span className="text-xs font-bold block">{n.data.label}</span>
                <span className="text-[10px] text-slate-400 line-clamp-1 block max-w-[140px]">
                  {n.data.title}
                </span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-semibold mt-1 inline-block ${
                  isMain ? 'bg-blue-500/20 text-blue-300' : 'bg-slate-800 text-amber-400'
                }`}>
                  {isMain ? 'Selected Anchor IS' : n.data.department}
                </span>
              </div>
            ),
          },
          type: n.type || 'default',
        };
      });

      const formattedEdges: Edge[] = data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: true,
        style: { stroke: '#3b82f6', strokeWidth: 2 },
        labelStyle: { fill: '#f59e0b', fontWeight: 600, fontSize: 10 },
        labelBgStyle: { fill: '#0f172a', rx: 4, ry: 4 },
      }));

      setNodes(formattedNodes);
      setEdges(formattedEdges);
    } catch (err: any) {
      setError('Failed to load Knowledge Graph data.');
    } finally {
      setIsLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    if (standardId) {
      fetchGraph(standardId);
    }
  }, [standardId, fetchGraph]);

  const handleNodeClick = (_: React.MouseEvent, node: Node) => {
    onSelectStandard(node.id);
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl mb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Network className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-bold text-white">Interactive Standards Knowledge Graph</h2>
          <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded font-mono border border-blue-500/20">
            {standardId}
          </span>
        </div>
        
        <button
          onClick={() => fetchGraph(standardId)}
          className="text-xs text-slate-400 hover:text-white flex items-center space-x-1 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Reset Layout</span>
        </button>
      </div>

      <div className="w-full h-[380px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden relative">
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-10">
            <div className="flex items-center space-x-2 text-slate-300 text-sm">
              <RefreshCw className="w-5 h-5 animate-spin text-blue-400" />
              <span>Rendering React Flow Graph...</span>
            </div>
          </div>
        ) : error ? (
          <div className="absolute inset-0 flex items-center justify-center text-rose-400 text-sm">
            {error}
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            fitView
          >
            <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
            <Controls className="bg-slate-900 border-slate-800 fill-slate-300 text-slate-300" />
          </ReactFlow>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
        <span className="flex items-center space-x-1">
          <Layers className="w-3.5 h-3.5 text-amber-400" />
          <span>Click any node to switch anchor standard inspection</span>
        </span>
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
            <span>TESTED_BY</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            <span>REQUIRES_MATERIAL</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <span>COMPLEMENTS</span>
          </span>
        </div>
      </div>
    </div>
  );
};
