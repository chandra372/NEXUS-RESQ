import React from 'react';
import { AlertOctagon, Info, EyeOff } from 'lucide-react';
import { RumorItem } from '../types';

interface RumorFeedProps {
  rumors: RumorItem[];
}

export const RumorFeed: React.FC<RumorFeedProps> = ({ rumors }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md flex flex-col max-h-90">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <EyeOff className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Unverified / Rumor Feed ({rumors.length})
          </h2>
        </div>
        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Suppressed from Map
        </span>
      </div>

      <div className="overflow-y-auto space-y-2 pr-1 flex-1">
        {rumors.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-500">
            No active rumors detected. Unverified broadcasts are isolated here automatically.
          </div>
        ) : (
          rumors.map((r) => (
            <div
              key={r.rumor_id}
              className="p-2.5 bg-slate-950/70 rounded-lg border border-slate-800/80 hover:border-amber-500/30 transition text-xs"
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                <span className="font-mono text-amber-400 font-semibold">{r.rumor_id}</span>
                <span className="uppercase font-bold px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                  {r.source} • {r.sender}
                </span>
                <span>{new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <p className="text-slate-200 text-xs italic mb-1.5 bg-slate-900/60 p-1.5 rounded border border-slate-800">
                "{r.message}"
              </p>
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span className="text-amber-400/90 font-medium">Filter reason: {r.reason}</span>
                <span>Conf: {Math.round(r.confidence * 100)}%</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
