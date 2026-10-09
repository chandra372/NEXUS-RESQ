import React from 'react';
import { IncidentSummary } from '../types';
import { IncidentCard } from './IncidentCard';
import { ShieldCheck, Inbox } from 'lucide-react';

interface IncidentListProps {
  incidents: IncidentSummary[];
  selectedIncident: IncidentSummary | null;
  onSelectIncident: (inc: IncidentSummary) => void;
}

export const IncidentList: React.FC<IncidentListProps> = ({
  incidents,
  selectedIncident,
  onSelectIncident
}) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between pb-1 border-b border-slate-800">
        <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          Discovered Incidents ({incidents.length})
        </h2>
        <span className="text-[11px] text-slate-400">
          Clustered from multiple raw channels
        </span>
      </div>

      {incidents.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center">
          <Inbox className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-slate-300">No Incidents Detected Yet</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Click "Process Stage" or "Replay" in the top bar to begin streaming and clustering emergency observations.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {incidents.map((inc) => (
            <IncidentCard
              key={inc.incident_id}
              incident={inc}
              isSelected={selectedIncident?.incident_id === inc.incident_id}
              onSelect={onSelectIncident}
            />
          ))}
        </div>
      )}
    </div>
  );
};
