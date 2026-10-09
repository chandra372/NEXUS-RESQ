import { 
  IncidentSummary, IncidentDetail, OverallStats, ReplayStatus, 
  TimelineItem, EvidenceItem, RumorItem, EvaluationResults 
} from '../types';

const API_BASE = '/api';

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  async getStats(): Promise<OverallStats> {
    const res = await fetch(`${API_BASE}/stats`);
    return res.json();
  },

  async getStages() {
    const res = await fetch(`${API_BASE}/stages`);
    return res.json();
  },

  async getIncidents(params?: { status?: string; priority?: string; stage?: string }): Promise<IncidentSummary[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.priority) query.append('priority', params.priority);
    if (params?.stage) query.append('stage', params.stage);
    const res = await fetch(`${API_BASE}/incidents?${query.toString()}`);
    return res.json();
  },

  async getIncident(id: string): Promise<IncidentDetail> {
    const res = await fetch(`${API_BASE}/incidents/${id}`);
    if (!res.ok) throw new Error('Incident not found');
    return res.json();
  },

  async getIncidentTimeline(id: string): Promise<TimelineItem[]> {
    const res = await fetch(`${API_BASE}/incidents/${id}/timeline`);
    return res.json();
  },

  async getIncidentEvidence(id: string): Promise<EvidenceItem[]> {
    const res = await fetch(`${API_BASE}/incidents/${id}/evidence`);
    return res.json();
  },

  async getRumors(): Promise<{ rumors: RumorItem[] }> {
    const res = await fetch(`${API_BASE}/rumors`);
    return res.json();
  },

  async getReplayStatus(): Promise<ReplayStatus> {
    const res = await fetch(`${API_BASE}/replay/status`);
    return res.json();
  },

  async startReplay(speed: number = 5): Promise<any> {
    const res = await fetch(`${API_BASE}/replay/start?speed=${speed}`, { method: 'POST' });
    return res.json();
  },

  async pauseReplay(): Promise<any> {
    const res = await fetch(`${API_BASE}/replay/pause`, { method: 'POST' });
    return res.json();
  },

  async resetReplay(): Promise<any> {
    const res = await fetch(`${API_BASE}/replay/reset`, { method: 'POST' });
    return res.json();
  },

  async nextStage(): Promise<any> {
    const res = await fetch(`${API_BASE}/replay/next-stage`, { method: 'POST' });
    return res.json();
  },

  async processStep(): Promise<any> {
    const res = await fetch(`${API_BASE}/process`, { method: 'POST' });
    return res.json();
  },

  async processAll(): Promise<any> {
    const res = await fetch(`${API_BASE}/process/all`, { method: 'POST' });
    return res.json();
  },

  async getEvaluation(): Promise<EvaluationResults> {
    const res = await fetch(`${API_BASE}/evaluation`);
    return res.json();
  }
};
