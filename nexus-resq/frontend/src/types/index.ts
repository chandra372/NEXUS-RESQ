export type IncidentStatus = 
  | 'DETECTED' 
  | 'ACTIVE' 
  | 'ESCALATING' 
  | 'RESCUE_IN_PROGRESS' 
  | 'RESOLVED' 
  | 'UNCONFIRMED';

export type PriorityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ObservationRecord {
  people_count: number;
  source_id: string;
  source_type: string;
  timestamp: string;
  confidence: number;
}

export interface ReopenRecord {
  previous_status: string;
  new_status: string;
  reopen_reason: string;
  reopen_evidence: string;
  reopened_at: string;
}

export interface TimelineItem {
  timestamp: string;
  stage: string;
  event_type: string;
  description: string;
  source_id?: string;
  source_type?: string;
  details?: Record<string, any>;
}

export interface EvidenceItem {
  source_id: string;
  source_type: string;
  timestamp: string;
  raw_text: string;
  sender: string;
  reliability: number;
  extracted_features?: Record<string, any>;
}

export interface PeopleConflictDetails {
  has_conflict: boolean;
  best_estimate: number;
  max_reported: number;
  confidence: number;
  unique_reported_counts: number[];
  frequency_breakdown: Record<number, number>;
  evidence_list: Array<{
    count: number;
    source_id: string;
    source_type: string;
    timestamp: string;
    confidence: number;
  }>;
  explanation: string;
}

export interface IncidentSummary {
  incident_id: string;
  name: string;
  incident_type: string;
  canonical_location: string;
  latitude?: number;
  longitude?: number;
  location_precision: string;
  location_confidence: number;
  landmarks: string[];
  status: IncidentStatus;
  urgency: 'HIGH' | 'MEDIUM' | 'LOW';
  priority_score: number;
  priority_level: PriorityLevel;
  initial_people?: number | null;
  current_people?: number | null;
  max_reported_people?: number | null;
  has_people_conflict: boolean;
  vulnerable_people: string[];
  resources_needed: string[];
  hazards: string[];
  evidence_count: number;
  confidence: number;
  first_seen_stage: string;
  last_updated_stage: string;
  created_at: string;
  updated_at: string;
  why_ai_believes: string[];
  is_resolved: boolean;
  resolved_at?: string;
}

export interface IncidentDetail extends IncidentSummary {
  timeline: TimelineItem[];
  evidence: EvidenceItem[];
  people_observations: ObservationRecord[];
  people_conflict_details?: PeopleConflictDetails | null;
  reopen_history: ReopenRecord[];
  ai_reasoning: Record<string, any>;
}

export interface RumorItem {
  rumor_id: string;
  source: string;
  sender: string;
  timestamp: string;
  message: string;
  reason: string;
  confidence: number;
  stage: string;
}

export interface StageMetrics {
  stage_name: string;
  reports_received: number;
  reports_processed: number;
  emergencies: number;
  noise: number;
  rumours: number;
  new_incidents: number;
  existing_incidents_updated: number;
  duplicates_merged: number;
  conflicts: number;
  escalations: number;
  resolutions: number;
  processing_time_seconds: number;
}

export interface OverallStats {
  reports_received: number;
  reports_processed: number;
  active_incidents: number;
  critical_incidents: number;
  resolved_incidents: number;
  noise_count: number;
  rumor_count: number;
  current_stage: string;
  stages_available: string[];
  stage_metrics: Record<string, StageMetrics>;
  ai_provider: string;
  speech_provider: string;
}

export interface ReplayStatus {
  is_running: boolean;
  is_paused: boolean;
  current_stage: string;
  stage_index: number;
  total_stages: number;
  processed_count: number;
  total_count: number;
  speed: number;
  progress_percentage: number;
}

export interface EvaluationResults {
  total_records_evaluated: number;
  emergency_classification_accuracy: number;
  noise_classification_accuracy: number;
  incident_clustering_accuracy_ari: number;
  location_accuracy: number;
  resource_extraction_accuracy: number;
  status_accuracy: number;
  people_count_mae: number;
  discovered_incidents_count: number;
  ground_truth_stories_count: number;
  per_stage_results: Record<string, {
    events_processed: number;
    emergency_classification_accuracy: number;
    noise_classification_accuracy: number;
    location_accuracy: number;
    resource_accuracy: number;
    status_accuracy: number;
    people_mae: number;
  }>;
}

export interface FilterState {
  status: string;
  priority: string;
  stage: string;
  search: string;
}
