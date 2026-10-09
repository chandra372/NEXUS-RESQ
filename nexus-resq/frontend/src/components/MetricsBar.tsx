import React from 'react';
import { Activity, AlertTriangle, CheckCircle2, Filter, AlertOctagon, Flame } from 'lucide-react';
import { OverallStats, ReplayStatus } from '../types';

interface MetricsBarProps {
  stats: OverallStats | null;
  replayStatus: ReplayStatus | null;
}

export const MetricsBar: React.FC<MetricsBarProps> = ({ stats, replayStatus }) => {
  const processed = stats?.reports_processed ?? 0;
  const received = stats?.reports_received ?? 471;
  const active = stats?.active_incidents ?? 0;
  const critical = stats?.critical_incidents ?? 0;
  const resolved = stats?.resolved_incidents ?? 0;
  const noise = stats?.noise_count ?? 0;
  const rumors = stats?.rumor_count ?? 0;

  const pct = received > 0 ? Math.min(100, Math.round((processed / received) * 100)) : 0;

  return (
    <div className="bg-slate-900/90 border-b border-slate-800 px-6 py-3">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Stream Progress */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Stream Ingestion</span>
            <span className="font-semibold text-slate-200">{processed} / {received}</span>
          </div>
          <div className="mt-2 w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div 
              className="bg-indigo-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${pct}%` }}
            ></div>
          </div>
          <span className="text-[10px] text-indigo-400 mt-1 font-mono font-medium">{pct}% processed</span>
        </div>

        {/* Active Incidents */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 block">Active Incidents</span>
            <span className="text-xl font-bold text-white mt-0.5 block">{active}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        {/* Critical Incidents */}
        <div className="bg-slate-950 p-3 rounded-xl border border-red-900/30 flex items-center justify-between">
          <div>
            <span className="text-xs text-red-400/90 block font-medium">Critical Incidents</span>
            <span className="text-xl font-black text-red-500 mt-0.5 block">{critical}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
            <Flame className="w-5 h-5 animate-pulse" />
          </div>
        </div>

        {/* Resolved Incidents */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 block">Resolved</span>
            <span className="text-xl font-bold text-emerald-400 mt-0.5 block">{resolved}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        {/* Noise Filtered */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 block">Noise Filtered</span>
            <span className="text-xl font-bold text-slate-300 mt-0.5 block">{noise}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-400">
            <Filter className="w-5 h-5" />
          </div>
        </div>

        {/* Rumors Isolated */}
        <div className="bg-slate-950 p-3 rounded-xl border border-amber-900/20 flex items-center justify-between">
          <div>
            <span className="text-xs text-amber-400/90 block font-medium">Rumors Isolated</span>
            <span className="text-xl font-bold text-amber-400 mt-0.5 block">{rumors}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <AlertOctagon className="w-5 h-5" />
          </div>
        </div>
      </div>
    </div>
  );
};
