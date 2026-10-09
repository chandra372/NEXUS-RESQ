from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ObservationRecord(BaseModel):
    people_count: int
    source_id: str
    source_type: str
    timestamp: str
    confidence: float

class ReopenRecord(BaseModel):
    previous_status: str
    new_status: str
    reopen_reason: str
    reopen_evidence: str
    reopened_at: str

class TimelineItem(BaseModel):
    timestamp: str
    stage: str
    event_type: str  # "CREATED", "PEOPLE_UPDATE", "ESCALATION", "RESCUE_PROGRESS", "RESOLVED", "REOPENED", "EVIDENCE_ADDED"
    description: str
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class EvidenceItem(BaseModel):
    source_id: str
    source_type: str
    timestamp: str
    raw_text: str
    sender: str
    reliability: float
    extracted_features: Dict[str, Any] = Field(default_factory=dict)

class IncidentSummary(BaseModel):
    incident_id: str
    name: str
    incident_type: str
    canonical_location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_precision: str = "approximate"
    location_confidence: float = 0.8
    landmarks: List[str] = Field(default_factory=list)
    status: str = "DETECTED"
    urgency: str = "HIGH"
    priority_score: int = 50
    priority_level: str = "MEDIUM"
    initial_people: Optional[int] = None
    current_people: Optional[int] = None
    max_reported_people: Optional[int] = None
    has_people_conflict: bool = False
    vulnerable_people: List[str] = Field(default_factory=list)
    resources_needed: List[str] = Field(default_factory=list)
    hazards: List[str] = Field(default_factory=list)
    evidence_count: int = 0
    confidence: float = 0.85
    first_seen_stage: str = "stage_1"
    last_updated_stage: str = "stage_1"
    created_at: str
    updated_at: str
    why_ai_believes: List[str] = Field(default_factory=list)
    is_resolved: bool = False
    resolved_at: Optional[str] = None

class IncidentDetail(IncidentSummary):
    timeline: List[TimelineItem] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    people_observations: List[ObservationRecord] = Field(default_factory=list)
    people_conflict_details: Optional[Dict[str, Any]] = None
    reopen_history: List[ReopenRecord] = Field(default_factory=list)
    ai_reasoning: Dict[str, Any] = Field(default_factory=dict)

class RumorItem(BaseModel):
    rumor_id: str
    source: str
    sender: str
    timestamp: str
    message: str
    reason: str
    confidence: float
    stage: str

class StageMetrics(BaseModel):
    stage_name: str
    reports_received: int = 0
    reports_processed: int = 0
    emergencies: int = 0
    noise: int = 0
    rumours: int = 0
    new_incidents: int = 0
    existing_incidents_updated: int = 0
    duplicates_merged: int = 0
    conflicts: int = 0
    escalations: int = 0
    resolutions: int = 0
    processing_time_seconds: float = 0.0

class OverallStats(BaseModel):
    reports_received: int = 0
    reports_processed: int = 0
    active_incidents: int = 0
    critical_incidents: int = 0
    resolved_incidents: int = 0
    noise_count: int = 0
    rumor_count: int = 0
    current_stage: str = "stage_1"
    stages_available: List[str] = Field(default_factory=list)
    stage_metrics: Dict[str, StageMetrics] = Field(default_factory=dict)
    ai_provider: str = "Local/Fallback Engine"
    speech_provider: str = "SpeechRecognition / Whisper STT"

class ReplayStatus(BaseModel):
    is_running: bool = False
    is_paused: bool = False
    current_stage: str = "stage_1"
    stage_index: int = 0
    total_stages: int = 3
    processed_count: int = 0
    total_count: int = 0
    speed: int = 1  # 1x, 5x, 20x
    progress_percentage: float = 0.0
