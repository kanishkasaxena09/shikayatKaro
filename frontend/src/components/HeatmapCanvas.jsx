import React, { useState } from 'react';
import { MapPin, AlertCircle, Layers, Activity } from 'lucide-react';

export const HeatmapCanvas = ({ data = [], loading = false, selectedCategory, onSelectLocation }) => {
  const [activeNode, setActiveNode] = useState(null);

  // Group or map nodes to canvas
  const getNodeColor = (impact, complaints) => {
    if (impact >= 70 || complaints >= 5) return 'bg-rose-500 border-rose-600 text-white shadow-rose-300 ring-4 ring-rose-200';
    if (impact >= 40 || complaints >= 3) return 'bg-amber-500 border-amber-600 text-white shadow-amber-300 ring-4 ring-amber-100';
    if (impact > 0 || complaints > 0) return 'bg-blue-500 border-blue-600 text-white shadow-blue-300';
    return 'bg-slate-300 border-slate-400 text-slate-700';
  };

  const getNodeSize = (impact, complaints) => {
    const total = (impact || 0) + (complaints || 0) * 10;
    if (total >= 70) return 'w-12 h-12 text-sm';
    if (total >= 30) return 'w-10 h-10 text-xs';
    return 'w-8 h-8 text-[11px]';
  };

  return (
    <div className="relative bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-xl p-4 sm:p-6 text-white">
      {/* Canvas Header & Legend */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <h3 className="font-bold text-base text-white tracking-tight">Live Campus Spatial Grievance Heatmap</h3>
          </div>
          <p className="text-xs text-slate-400">
            Real-time multi-source clustering coordinates across campus blocks and infrastructure.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-xs text-slate-300">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500 ring-2 ring-rose-300"></span>
            <span>Critical Hotspot (Impact ≥ 70)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500 ring-2 ring-amber-200"></span>
            <span>Moderate (Impact 40-69)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
            <span>Active Grievance</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-slate-500"></span>
            <span>Clear</span>
          </div>
        </div>
      </div>

      {/* 2D Spatial Layout Plane */}
      <div className="relative w-full h-[420px] bg-slate-950 rounded-xl border border-slate-800/80 overflow-hidden shadow-inner">
        {/* Subtle Campus Grid Lines */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-35" />

        {/* Campus Landmark Labels */}
        <div className="absolute top-3 left-3 text-[11px] font-mono text-slate-600 uppercase tracking-widest pointer-events-none">
          Sector A — Academic Complex
        </div>
        <div className="absolute bottom-3 left-3 text-[11px] font-mono text-slate-600 uppercase tracking-widest pointer-events-none">
          Sector B — Administrative & Governance
        </div>
        <div className="absolute top-3 right-3 text-[11px] font-mono text-slate-600 uppercase tracking-widest pointer-events-none">
          Sector C — Residential & Student Hostels
        </div>

        {/* Heatmap Nodes */}
        {data.map((node) => {
          const isSelected = activeNode?.location_id === node.location_id;
          return (
            <button
              key={node.location_id}
              onClick={() => {
                setActiveNode(node);
                if (onSelectLocation) onSelectLocation(node);
              }}
              style={{
                left: `${Math.min(92, Math.max(8, node.grid_x))}%`,
                top: `${Math.min(90, Math.max(10, node.grid_y))}%`,
                transform: 'translate(-50%, -50%)',
              }}
              className={`absolute rounded-full border flex flex-col items-center justify-center font-bold shadow-md cursor-pointer transition-all duration-300 hover:scale-125 z-10 ${getNodeColor(
                node.total_impact,
                node.complaint_count
              )} ${getNodeSize(node.total_impact, node.complaint_count)} ${
                isSelected ? 'ring-4 ring-indigo-400 scale-125 z-20' : ''
              }`}
              title={`${node.location_name}: ${node.complaint_count} complaints, Impact: ${node.total_impact}`}
            >
              <span>{node.complaint_count || 0}</span>
            </button>
          );
        })}

        {/* Selected Node Details Floating Popup Card */}
        {activeNode && (
          <div className="absolute bottom-4 right-4 z-30 bg-slate-900/95 backdrop-blur-md border border-slate-700 p-4 rounded-xl shadow-2xl max-w-xs w-full text-xs text-slate-200 animate-in fade-in slide-in-from-bottom-2 duration-150">
            <div className="flex items-start justify-between gap-2 border-b border-slate-800 pb-2 mb-2">
              <div>
                <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                  {activeNode.location_name}
                </h4>
                {activeNode.parent_name && (
                  <span className="text-[11px] text-slate-400">{activeNode.parent_name}</span>
                )}
              </div>
              <button
                onClick={() => setActiveNode(null)}
                className="text-slate-400 hover:text-white font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-2">
              <div className="bg-slate-800/60 p-2 rounded-lg">
                <span className="text-slate-400 text-[10px] block">Complaints:</span>
                <span className="font-bold text-sm text-white">{activeNode.complaint_count}</span>
              </div>
              <div className="bg-slate-800/60 p-2 rounded-lg">
                <span className="text-slate-400 text-[10px] block">Impact Score:</span>
                <span className="font-bold text-sm text-rose-400">{activeNode.total_impact}/100</span>
              </div>
            </div>

            {activeNode.primary_category && (
              <div className="text-[11px] text-slate-300">
                Primary Issue: <strong className="text-indigo-300">{activeNode.primary_category}</strong>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default HeatmapCanvas;
