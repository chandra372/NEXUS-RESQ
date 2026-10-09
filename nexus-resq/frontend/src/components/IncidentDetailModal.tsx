import React, { useState, useEffect } from 'react';
import { 
  X, AlertTriangle, ShieldCheck, Clock, MapPin, Users, 
  HelpCircle, CheckCircle, FileText, Activity, AlertOctagon,
  ArrowRight, Navigation
} from 'lucide-react';
import { IncidentDetail, IncidentSummary } from '../types';
import { api } from '../services/api';

interface IncidentDetailModalProps {
  incidentSummary: IncidentSummary | null;
  onClose: () => void;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({
  incidentSummary,
  onClose
}) => {
  const [detail, setDetail] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'reasoning' | 'timeline' | 'evidence'>('overview');

  useEffect(() => {
    if (!incidentSummary) return;
    setLoading(true);
    api.getIncident(incidentSummary.incident_id)
      .then((data) => {
        setDetail(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load incident details:', err);
        setLoading(false);
      });
  }, [incidentSummary]);

  if (!incidentSummary) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950/80 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">
                {incidentSummary.incident_id}
              </span>
              <span className={`text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                incidentSummary.is_resolved
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-red-500/10 text-red-400 border-red-500/30'
              }`}>
                {incidentSummary.status.replace(/_/g, ' ')}
              </span>
              <span className="text-xs font-black text-amber-400 px-2 py-0.5 bg-amber-950/40 rounded border border-amber-800/40">
                Priority: {incidentSummary.priority_score} ({incidentSummary.priority_level})
              </span>
            </div>
            <h2 className="text-lg font-bold text-white">
              {incidentSummary.name}
            </h2>
            <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
              <MapPin className="w-3.5 h-3.5 text-slate-500" />
              <span>{incidentSummary.canonical_location}</span>
              <span className="text-slate-600">•</span>
              <span className="text-indigo-400 font-medium">Precision: {incidentSummary.location_precision}</span>
            </p>
            {incidentSummary.latitude && incidentSummary.longitude && (
              <a
                href={`https://www.google.com/maps/search/?api=1&query=${incidentSummary.latitude},${incidentSummary.longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 text-[11px] font-semibold rounded-md bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition"
              >
                <Navigation className="w-3 h-3 text-indigo-400" />
                Open Coordinates in Google Maps ({incidentSummary.latitude.toFixed(4)}, {incidentSummary.longitude.toFixed(4)})
              </a>
            )}
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 px-5 pt-3 bg-slate-900 border-b border-slate-800 text-xs">
          {[
            { id: 'overview', label: 'Situation Overview' },
            { id: 'reasoning', label: 'Why does AI believe this?' },
            { id: 'timeline', label: 'Evolution Timeline' },
            { id: 'evidence', label: `Evidence Ledger (${incidentSummary.evidence_count})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3 py-2 font-semibold border-b-2 transition cursor-pointer ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-400 bg-slate-800/40 rounded-t-lg'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {loading ? (
            <div className="text-center py-12 text-slate-400">Loading incident memory...</div>
          ) : !detail ? (
            <div className="text-center py-12 text-red-400">Error loading incident data.</div>
          ) : (
            <>
              {/* TAB 1: OVERVIEW */}
              {activeTab === 'overview' && (
                <div className="space-y-5">
                  {/* People Count Tracker & Conflict Warning */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                        <Users className="w-4 h-4 text-indigo-400" />
                        People Affected Intelligence
                      </h4>
                      {detail.has_people_conflict && (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 font-bold text-[10px]">
                          <AlertTriangle className="w-3 h-3" /> CONFLICT DETECTED
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-3 gap-3 text-center mb-3">
                      <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                        <span className="text-[10px] text-slate-400 block uppercase">Current Best Estimate</span>
                        <span className="text-xl font-bold text-indigo-400">{detail.current_people ?? 'Unknown'}</span>
                      </div>
                      <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                        <span className="text-[10px] text-slate-400 block uppercase">Max Reported Peak</span>
                        <span className="text-xl font-bold text-amber-400">{detail.max_reported_people ?? 'Unknown'}</span>
                      </div>
                      <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                        <span className="text-[10px] text-slate-400 block uppercase">Initial Report Count</span>
                        <span className="text-xl font-bold text-slate-300">{detail.initial_people ?? 'Unknown'}</span>
                      </div>
                    </div>

                    {/* Conflict Explanation & Evidence breakdown */}
                    {detail.has_people_conflict && detail.people_conflict_details && (
                      <div className="p-3 bg-amber-950/30 rounded-lg border border-amber-800/40 text-amber-200/90 text-xs mt-3">
                        <p className="font-semibold mb-1">
                          ⚠️ {detail.people_conflict_details.explanation}
                        </p>
                        <div className="mt-2 space-y-1">
                          <span className="text-[10px] text-amber-400/80 font-bold uppercase tracking-wider block">
                            Conflicting Observations:
                          </span>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-1">
                            {detail.people_conflict_details.evidence_list.map((obs, idx) => (
                              <div key={idx} className="p-2 bg-slate-900/90 rounded border border-amber-900/30 text-[11px]">
                                <div className="font-bold text-white">{obs.count} people</div>
                                <div className="text-slate-400 text-[10px]">Source: {obs.source_type.toUpperCase()} ({obs.source_id})</div>
                                <div className="text-slate-500 text-[10px]">{new Date(obs.timestamp).toLocaleTimeString()}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Vulnerable Populations & Required Resources */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2">
                        Vulnerable Populations
                      </h4>
                      {detail.vulnerable_people.length === 0 ? (
                        <p className="text-slate-500 italic">No specific vulnerable populations reported.</p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {detail.vulnerable_people.map((v) => (
                            <span key={v} className="px-2.5 py-1 bg-amber-500/10 text-amber-300 rounded-lg border border-amber-500/30 font-semibold text-xs flex items-center gap-1">
                              ⚠️ {v.toUpperCase()}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2">
                        Resources Dispatched / Required
                      </h4>
                      {detail.resources_needed.length === 0 ? (
                        <p className="text-slate-500 italic">Standard emergency dispatch.</p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {detail.resources_needed.map((r) => (
                            <span key={r} className="px-2.5 py-1 bg-indigo-500/10 text-indigo-300 rounded-lg border border-indigo-500/30 font-semibold text-xs flex items-center gap-1">
                              🚑 {r.replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Landmarks & Location Cues */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2">
                      Corroborating Landmarks & Geography
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {detail.landmarks.map((lm, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded border border-slate-700 text-xs">
                          📌 {lm}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: WHY DOES AI BELIEVE THIS? */}
              {activeTab === 'reasoning' && (
                <div className="space-y-4">
                  <div className="p-4 bg-indigo-950/20 rounded-xl border border-indigo-500/30">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-bold text-indigo-200 flex items-center gap-2">
                        <ShieldCheck className="w-5 h-5 text-indigo-400" />
                        AI Reasoning & Corroboration Engine
                      </h4>
                      <div className="text-right">
                        <span className="text-lg font-black text-indigo-400">{Math.round(detail.confidence * 100)}%</span>
                        <span className="text-[10px] text-slate-400 block uppercase">Confidence</span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 mb-3">
                      NEXUS RESQ maintains multi-factor evidence linking across channels. The AI determined these reports represent the same evolving physical emergency based on the following verified criteria:
                    </p>

                    <div className="space-y-2 mt-2">
                      {detail.why_ai_believes.map((reason, idx) => (
                        <div key={idx} className="flex items-start gap-2 p-2 bg-slate-900/90 rounded-lg border border-indigo-950 text-xs text-slate-200">
                          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                          <span>{reason.replace(/^✓\s*/, '')}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Multi-Factor Weight Breakdown */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">
                      Configured Multi-Factor Matching Weights
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                      <div className="p-2 bg-slate-900 rounded border border-slate-800">
                        <div className="font-bold text-indigo-400">30%</div>
                        <div className="text-[10px] text-slate-400">Semantic Sim</div>
                      </div>
                      <div className="p-2 bg-slate-900 rounded border border-slate-800">
                        <div className="font-bold text-indigo-400">25%</div>
                        <div className="text-[10px] text-slate-400">Location Sim</div>
                      </div>
                      <div className="p-2 bg-slate-900 rounded border border-slate-800">
                        <div className="font-bold text-indigo-400">15%</div>
                        <div className="text-[10px] text-slate-400">Landmark Sim</div>
                      </div>
                      <div className="p-2 bg-slate-900 rounded border border-slate-800">
                        <div className="font-bold text-indigo-400">10%</div>
                        <div className="text-[10px] text-slate-400">Time Decay</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: TIMELINE */}
              {activeTab === 'timeline' && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                    Evolving Incident History
                  </h4>
                  <div className="relative border-l border-slate-700 ml-3 space-y-4 py-2">
                    {detail.timeline.map((item, idx) => (
                      <div key={idx} className="relative pl-6">
                        <div className="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full bg-indigo-500 border-2 border-slate-900"></div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold text-[11px] text-indigo-400">{item.event_type}</span>
                          <span className="text-[10px] text-slate-500">{new Date(item.timestamp).toLocaleTimeString()}</span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 uppercase">
                            {item.stage}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                          {item.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 4: EVIDENCE LEDGER */}
              {activeTab === 'evidence' && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                    Raw Citizen & Channel Reports ({detail.evidence.length})
                  </h4>
                  <div className="space-y-2.5">
                    {detail.evidence.map((ev, idx) => (
                      <div key={idx} className="p-3 bg-slate-950 rounded-xl border border-slate-800 hover:border-slate-700 transition">
                        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-slate-300">{ev.source_id}</span>
                            <span className="uppercase font-bold px-1.5 py-0.2 rounded bg-slate-800 text-slate-200">
                              {ev.source_type} • {ev.sender}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-emerald-400 font-semibold">Reliability: {Math.round(ev.reliability * 100)}%</span>
                            <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-200 bg-slate-900/60 p-2 rounded-lg border border-slate-800/60">
                          {ev.raw_text}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
          <span>First discovered: {detail?.first_seen_stage.replace('_', ' ').toUpperCase()}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
