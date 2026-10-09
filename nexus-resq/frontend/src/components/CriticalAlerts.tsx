import React from 'react';
import { AlertCircle, Flame, ArrowUpRight, ShieldAlert } from 'lucide-react';
import { IncidentSummary } from '../types';

interface CriticalAlertsProps {
  incidents: IncidentSummary[];
  onSelectIncident: (inc: IncidentSummary) => void;
}

export const CriticalAlerts: React.FC<CriticalAlertsProps> = ({ incidents, onSelectIncident }) => {
  const criticals = incidents.filter(
    (i) => (i.priority_level === 'CRITICAL' || i.status === 'ESCALATING' || i.urgency === 'HIGH') && !i.is_resolved
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md flex flex-col max-h-95">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-red-500 animate-pulse" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Critical Alerts ({criticals.length})
          </h2>
        </div>
        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
          Responder Priority
        </span>
      </div>

      <div className="overflow-y-auto space-y-2.5 pr-1 flex-1">
        {criticals.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No active critical emergencies. All situations currently within standard operational thresholds.
          </div>
        ) : (
          criticals.map((inc) => (
            <div
              key={inc.incident_id}
              onClick={() => onSelectIncident(inc)}
              className="p-3 bg-slate-950/90 hover:bg-slate-800/80 rounded-lg border border-red-900/30 hover:border-red-500/50 transition cursor-pointer group"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-[10px] font-mono font-bold text-red-400 bg-red-950/60 px-1.5 py-0.5 rounded border border-red-800/40">
                      {inc.incident_id}
                    </span>
                    <span className="text-[10px] font-bold text-amber-300">
                      {inc.status}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-200 group-hover:text-white line-clamp-1">
                    {inc.name}
                  </h4>
                  <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                    {inc.canonical_location}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-xs font-black text-red-500 block">
                    {inc.priority_score}
                  </span>
                  <span className="text-[10px] text-slate-500 block">priority</span>
                </div>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap items-center gap-1 mt-2 text-[10px]">
                {inc.current_people !== null && inc.current_people !== undefined && (
                  <span className="px-1.5 py-0.5 bg-slate-800 text-slate-300 rounded font-medium">
                    👥 {inc.current_people} people
                  </span>
                )}
                {inc.vulnerable_people.map((v) => (
                  <span key={v} className="px-1.5 py-0.5 bg-amber-500/10 text-amber-300 rounded border border-amber-500/20 font-medium">
                    ⚠️ {v}
                  </span>
                ))}
                {inc.resources_needed.map((r) => (
                  <span key={r} className="px-1.5 py-0.5 bg-indigo-500/10 text-indigo-300 rounded border border-indigo-500/20 font-medium">
                    🚑 {r.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
