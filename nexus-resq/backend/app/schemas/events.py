from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class UnifiedEvent(BaseModel):
    event_id: str
    source: str  # "whatsapp", "sms", "twitter", "audio"
    source_id: str
    timestamp: str
    raw_text: str
    language: str = "en"
    sender: str
    audio_path: Optional[str] = None
    stage_number: int = 1
    stage_name: str = "stage_1"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ClassificationResult(BaseModel):
    intent: str  # "EMERGENCY", "NOISE", "RUMOR", "INFORMATION", "UNKNOWN"
    confidence: float
    reason: str
    risk_flags: List[str] = Field(default_factory=list)

class ExtractionResult(BaseModel):
    incident_type: Optional[str] = None
    location_text: Optional[str] = None
    landmarks: List[str] = Field(default_factory=list)
    people_count: Optional[int] = None  # None if unknown, NEVER 0 for unknown
    vulnerable_people: List[str] = Field(default_factory=list)
    resource_needed: Optional[str] = None
    urgency: str = "LOW"  # "HIGH", "MEDIUM", "LOW"
    hazards: List[str] = Field(default_factory=list)
    status_signal: Optional[str] = None  # "ACTIVE", "ESCALATING", "RESCUE_IN_PROGRESS", "RESOLVED"
    rescue_signal: bool = False
    resolution_signal: bool = False
    evidence_strength: float = 0.5

class LocationResolutionResult(BaseModel):
    canonical_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmarks: List[str] = Field(default_factory=list)
    location_precision: str = "unknown"  # "exact", "landmark", "area", "approximate", "unknown"
    confidence: float = 0.0
    evidence: str = ""

class MatchDecision(BaseModel):
    decision: str  # "MERGE", "CREATE_NEW", "UNCERTAIN"
    matched_incident_id: Optional[str] = None
    score: float = 0.0
    reasons: List[str] = Field(default_factory=list)
    component_scores: Dict[str, float] = Field(default_factory=dict)
