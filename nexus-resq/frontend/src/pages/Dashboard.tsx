import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  IncidentSummary, OverallStats, ReplayStatus, RumorItem, FilterState 
} from '../types';
import { api } from '../services/api';
import { Header } from '../components/Header';
import { MetricsBar } from '../components/MetricsBar';
import { Filters } from '../components/Filters';
import { LiveMap } from '../components/LiveMap';
import { CriticalAlerts } from '../components/CriticalAlerts';
import { RumorFeed } from '../components/RumorFeed';
import { IncidentList } from '../components/IncidentList';
import { IncidentDetailModal } from '../components/IncidentDetailModal';
import { EvaluationModal } from '../components/EvaluationModal';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<OverallStats | null>(null);
  const [replayStatus, setReplayStatus] = useState<ReplayStatus | null>(null);
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [rumors, setRumors] = useState<RumorItem[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentSummary | null>(null);
  const [isEvalOpen, setIsEvalOpen] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(5);

  const [filters, setFilters] = useState<FilterState>({
    status: '',
    priority: '',
    stage: '',
    search: '',
  });

  const wsRef = useRef<WebSocket | null>(null);

  // Load initial data
  const refreshData = useCallback(async () => {
    try {
      const [s, rStatus, incList, rumList] = await Promise.all([
        api.getStats(),
        api.getReplayStatus(),
        api.getIncidents(),
        api.getRumors(),
      ]);
      setStats(s);
      setReplayStatus(rStatus);
      setIncidents(incList);
      setRumors(rumList.rumors || []);
    } catch (e) {
      console.error('Failed to load dashboard data:', e);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Setup WebSocket connection for real-time streaming
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws`;

    const connectWs = () => {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const { event_type, data } = payload;

          if (event_type === 'initial_state') {
            setStats(data.stats);
            setReplayStatus(data.status);
          } else if (
            event_type === 'incident_created' ||
            event_type === 'incident_updated' ||
            event_type === 'incident_escalated' ||
            event_type === 'incident_resolved'
          ) {
            // Refresh incident list
            api.getIncidents().then(setIncidents);
            api.getStats().then(setStats);
            api.getReplayStatus().then(setReplayStatus);
          } else if (event_type === 'rumor_detected') {
            api.getRumors().then((r) => setRumors(r.rumors || []));
            api.getStats().then(setStats);
          } else if (event_type === 'stats_updated') {
            setStats(data);
          } else if (event_type === 'stage_completed' || event_type === 'stage_started' || event_type === 'reset') {
            refreshData();
          }
        } catch (err) {
          console.error('WebSocket message parsing error:', err);
        }
      };

      ws.onclose = () => {
        // Reconnect after 3 seconds if disconnected
        setTimeout(connectWs, 3000);
      };
    };

    connectWs();

    return () => {
      wsRef.current?.close();
    };
  }, [refreshData]);

  // Replay handlers
  const handleStart = async (s: number) => {
    await api.startReplay(s);
    refreshData();
  };

  const handlePause = async () => {
    await api.pauseReplay();
    refreshData();
  };

  const handleReset = async () => {
    await api.resetReplay();
    refreshData();
  };

  const handleNextStage = async () => {
    await api.nextStage();
    refreshData();
  };

  const handleProcessStep = async () => {
    await api.processStep();
    refreshData();
  };

  const handleProcessAll = async () => {
    await api.processAll();
    refreshData();
  };

  // Filtered incidents
  const filteredIncidents = incidents.filter((inc) => {
    if (filters.status && inc.status.toUpperCase() !== filters.status.toUpperCase()) {
      return false;
    }
    if (filters.priority && inc.priority_level.toUpperCase() !== filters.priority.toUpperCase()) {
      return false;
    }
    if (filters.stage && inc.last_updated_stage.toLowerCase() !== filters.stage.toLowerCase()) {
      return false;
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      const match =
        inc.name.toLowerCase().includes(q) ||
        inc.canonical_location.toLowerCase().includes(q) ||
        inc.incident_id.toLowerCase().includes(q) ||
        inc.landmarks.some((l) => l.toLowerCase().includes(q));
      if (!match) return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <Header
        stats={stats}
        replayStatus={replayStatus}
        onStart={handleStart}
        onPause={handlePause}
        onReset={handleReset}
        onNextStage={handleNextStage}
        onProcessStep={handleProcessStep}
        onProcessAll={handleProcessAll}
        onOpenEval={() => setIsEvalOpen(true)}
        speed={speed}
        setSpeed={setSpeed}
      />

      {/* Metrics Bar */}
      <MetricsBar stats={stats} replayStatus={replayStatus} />

      {/* Main Operational Grid */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Filters (2 cols on lg) */}
        <div className="lg:col-span-3 xl:col-span-2 space-y-4">
          <Filters
            filters={filters}
            onChange={setFilters}
            stages={stats?.stages_available || ['stage_1', 'stage_2', 'stage_3']}
          />
        </div>

        {/* Center Column: Live Map & Incident List (7 cols on lg) */}
        <div className="lg:col-span-6 xl:col-span-7 space-y-6">
          <LiveMap
            incidents={filteredIncidents}
            selectedIncident={selectedIncident}
            onSelectIncident={setSelectedIncident}
          />

          <IncidentList
            incidents={filteredIncidents}
            selectedIncident={selectedIncident}
            onSelectIncident={setSelectedIncident}
          />
        </div>

        {/* Right Column: Critical Alerts & Rumor Feed (3 cols on lg) */}
        <div className="lg:col-span-3 xl:col-span-3 space-y-6">
          <CriticalAlerts
            incidents={incidents}
            onSelectIncident={setSelectedIncident}
          />

          <RumorFeed rumors={rumors} />
        </div>
      </main>

      {/* Incident Detail Drawer/Modal */}
      <IncidentDetailModal
        incidentSummary={selectedIncident}
        onClose={() => setSelectedIncident(null)}
      />

      {/* Evaluation Modal */}
      <EvaluationModal
        isOpen={isEvalOpen}
        onClose={() => setIsEvalOpen(false)}
      />
    </div>
  );
};
