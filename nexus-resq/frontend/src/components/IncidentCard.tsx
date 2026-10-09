import React from 'react';
import { Users, AlertTriangle, Clock, ShieldCheck, ChevronRight, AlertCircle } from 'lucide-react';
import { IncidentSummary } from '../types';

interface IncidentCardProps {
  incident: IncidentSummary;
  isSelected: boolean;
  onSelect: (inc: IncidentSummary) => void;
}

export const IncidentCard: React.FC<IncidentCardProps> = ({ incident, isSelected, onSelect }) => {
  const isCritical = incident.priority_level === 'CRITICAL';
  const isHigh = incident.priority_level === 'HIGH';
  const isResolved = incident.is_resolved;

  const statusBg = isResolved
    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
    : incident.status === 'ESCALATING'
    ? 'bg-red-500/10 text-red-400 border-red-500/30'
    : incident.status === 'RESCUE_IN_PROGRESS'
    ? 'bg-sky-500/10 text-sky-400 border-sky-500/30'
    : 'bg-amber-500/10 text-amber-300 border-amber-500/30';

  const priorityColor = isCritical
    ? 'text-red-500'
    : isHigh
    ? 'text-orange-500'
    : incident.priority_level === 'MEDIUM'
    ? 'text-yellow-500'
    : 'text-slate-400';

  return (
    <div
      onClick={() => onSelect(incident)}
      className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer shadow-sm relative overflow-hidden ${
        isSelected
          ? 'bg-slate-800/90 border-indigo-500 ring-2 ring-indigo-500/20'
          : 'bg-slate-900/80 hover:bg-slate-850 border-slate-800 hover:border-slate-700'
      }`}
    >
      {/* Top Bar */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
            {incident.incident_id}
          </span>
          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${statusBg}`}>
            {incident.status.replace(/_/g, ' ')}
          </span>
          {incident.has_people_conflict && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> Conflict
            </span>
          )}
        </div>

        <div className="text-right">
          <span className={`text-sm font-black ${priorityColor}`}>
            {incident.priority_score}
          </span>
          <span className="text-[10px] text-slate-500 uppercase font-semibold block -mt-0.5">
            {incident.priority_level}
          </span>
        </div>
      </div>

      {/* Incident Title & Canonical Location */}
      <h3 className="text-sm font-bold text-white mb-1 line-clamp-1">
        {incident.name}
      </h3>
      <p className="text-xs text-slate-400 line-clamp-1 mb-3">
        📍 {incident.canonical_location}
      </p>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-2 py-2 px-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80 mb-3 text-xs">
        <div className="flex items-center gap-1.5 text-slate-300">
          <Users className="w-3.5 h-3.5 text-indigo-400" />
          <span>
            {incident.current_people !== null && incident.current_people !== undefined
              ? `${incident.current_people} affected`
              : 'Count unconfirmed'}
          </span>
        </div>
        <div className="flex items-center justify-end gap-1.5 text-slate-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>{Math.round(incident.confidence * 100)}% confidence</span>
        </div>
      </div>

      {/* Tags row */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3 text-[10px]">
        {incident.vulnerable_people.map((v) => (
          <span key={v} className="px-2 py-0.5 bg-amber-500/10 text-amber-300 rounded-md border border-amber-500/20 font-medium">
            ⚠️ {v}
          </span>
        ))}
        {incident.resources_needed.map((r) => (
          <span key={r} className="px-2 py-0.5 bg-indigo-500/10 text-indigo-300 rounded-md border border-indigo-500/20 font-medium">
            🚑 {r.replace(/_/g, ' ')}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3 text-slate-500" />
          <span>Evidence: <strong>{incident.evidence_count}</strong> reports</span>
        </div>
        <div className="flex items-center gap-1 text-indigo-400 font-semibold group-hover:translate-x-0.5 transition">
          <span>Inspect Evidence</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </div>
  );
};
