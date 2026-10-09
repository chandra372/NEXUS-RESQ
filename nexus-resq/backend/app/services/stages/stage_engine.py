import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict

from app.schemas.events import UnifiedEvent
from app.schemas.incident import (
    IncidentDetail, StageMetrics, OverallStats, ReplayStatus
)
from app.services.ingestion.discovery import DatasetDiscovery
from app.services.ai.classifier import EmergencyClassifier
from app.services.extraction.extractor import InformationExtractor
from app.services.location.resolver import LocationResolver
from app.services.clustering.matcher import IncidentMatcher
from app.services.incidents.memory import IncidentMemoryStore
from app.core.config import settings

logger = logging.getLogger(__name__)

class StageEngine:
    """
    Generic Stage Engine and Replay Manager.
    Orchestrates the full multi-modal pipeline:
    RAW EVENT -> CLASSIFY -> EXTRACT -> RESOLVE LOCATION -> MATCH -> MEMORY UPDATE -> METRICS -> NOTIFY
    Supports:
    - Any number of stages (stage_1, stage_2, stage_3, stage_4, ...)
    - Step-by-step or automated replay at 1x, 5x, 20x speed
    - Pause, Start, Reset, Next Stage controls
    - Zero ground-truth leakage
    """

    def __init__(self):
        self.discovery = DatasetDiscovery()
        self.classifier = EmergencyClassifier()
        self.extractor = InformationExtractor()
        self.location_resolver = LocationResolver()
        self.matcher = IncidentMatcher()
        self.memory = IncidentMemoryStore()

        self.stages: List[str] = self.discovery.discover_stages()
        self.current_stage_idx: int = 0
        self.is_running: bool = False
        self.is_paused: bool = False
        self.speed: int = 5  # Default 5x speed for snappy demo
        self.is_loading: bool = False  # True while background load is in progress

        # Preloaded events per stage
        self._stage_events: Dict[str, List[UnifiedEvent]] = {}
        self._event_cursor: int = 0
        self._stage_metrics: Dict[str, StageMetrics] = {}
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []

        # Initialize metrics for discovered stages
        for stg in self.stages:
            self._stage_metrics[stg] = StageMetrics(stage_name=stg)

        # Load stage events eagerly but cap audio transcription time per file
        self._load_stage_events()

    def _load_stage_events(self):
        """Load all stages. Audio transcription is skipped at startup to keep it fast."""
        self.is_loading = True
        try:
            for stg in self.stages:
                # Skip audio transcription on initial load (use cached results only)
                self._stage_events[stg] = self.discovery.ingest_stage(stg, transcribe_audio=False)
                self._stage_metrics[stg].reports_received = len(self._stage_events[stg])
            logger.info(f"Loaded {len(self.stages)} stages: {[len(v) for v in self._stage_events.values()]}")
        finally:
            self.is_loading = False

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]):
        self._listeners.append(callback)

    def _emit(self, event_type: str, data: Dict[str, Any]):
        payload = {"event_type": event_type, "timestamp": time.time(), "data": data}
        for cb in self._listeners:
            try:
                cb(payload)
            except Exception as e:
                logger.error(f"Listener error: {e}")

    @property
    def current_stage(self) -> str:
        if 0 <= self.current_stage_idx < len(self.stages):
            return self.stages[self.current_stage_idx]
        return self.stages[0] if self.stages else "stage_1"

    def get_status(self) -> ReplayStatus:
        stg = self.current_stage
        events = self._stage_events.get(stg, [])
        total = len(events)
        pct = (self._event_cursor / total * 100.0) if total > 0 else 0.0

        return ReplayStatus(
            is_running=self.is_running,
            is_paused=self.is_paused,
            current_stage=stg,
            stage_index=self.current_stage_idx,
            total_stages=len(self.stages),
            processed_count=self._event_cursor,
            total_count=total,
            speed=self.speed,
            progress_percentage=round(pct, 1)
        )

    def get_overall_stats(self) -> OverallStats:
        incidents = self.memory.get_all_incidents()
        active = sum(1 for i in incidents if i.status in ["ACTIVE", "DETECTED", "ESCALATING", "RESCUE_IN_PROGRESS"])
        critical = sum(1 for i in incidents if i.priority_level == "CRITICAL")
        resolved = sum(1 for i in incidents if i.is_resolved)

        total_received = sum(m.reports_received for m in self._stage_metrics.values())
        total_processed = sum(m.reports_processed for m in self._stage_metrics.values())
        total_noise = sum(m.noise for m in self._stage_metrics.values())
        total_rumors = sum(m.rumours for m in self._stage_metrics.values())

        return OverallStats(
            reports_received=total_received,
            reports_processed=total_processed,
            active_incidents=active,
            critical_incidents=critical,
            resolved_incidents=resolved,
            noise_count=total_noise,
            rumor_count=total_rumors,
            current_stage=self.current_stage,
            stages_available=self.stages,
            stage_metrics=self._stage_metrics,
            ai_provider=settings.AI_PROVIDER_NAME,
            speech_provider=settings.SPEECH_PROVIDER_NAME
        )

    def process_event(self, event: UnifiedEvent) -> Dict[str, Any]:
        """
        Process a single unified event through the multimodal pipeline:
        1. Classify (Emergency / Noise / Rumor / Info)
        2. Extract details
        3. Resolve location
        4. Match with existing incidents
        5. Update memory / state machine
        6. Update metrics
        7. Emit real-time events
        """
        stg = event.stage_name
        metrics = self._stage_metrics.setdefault(stg, StageMetrics(stage_name=stg))
        metrics.reports_processed += 1

        # 1. Classification
        classification = self.classifier.classify(event)

        if classification.intent == "NOISE":
            metrics.noise += 1
            self._emit("noise_detected", {
                "event_id": event.event_id,
                "source": event.source,
                "text": event.raw_text,
                "reason": classification.reason
            })
            return {"status": "NOISE", "event_id": event.event_id}

        if classification.intent == "RUMOR":
            metrics.rumours += 1
            rumor_item = {
                "rumor_id": f"RUMOR-{len(self.memory.get_rumors())+1:03d}",
                "source": event.source,
                "sender": event.sender,
                "timestamp": event.timestamp,
                "message": event.raw_text,
                "reason": classification.reason,
                "confidence": classification.confidence,
                "stage": event.stage_name
            }
            self.memory.add_rumor(rumor_item)
            self._emit("rumor_detected", rumor_item)
            return {"status": "RUMOR", "rumor": rumor_item}

        # 2. Information Extraction
        metrics.emergencies += 1
        extraction = self.extractor.extract(event)

        # 3. Location Resolution
        location = self.location_resolver.resolve(event.raw_text, extraction.landmarks)

        # 4. Incident Matching
        existing_incidents = self.memory.get_all_incidents()
        match_decision = self.matcher.match(event, extraction, location, existing_incidents)

        result_incident: IncidentDetail

        if match_decision.decision == "MERGE" and match_decision.matched_incident_id:
            metrics.duplicates_merged += 1
            metrics.existing_incidents_updated += 1

            prev_inc = self.memory.get_incident(match_decision.matched_incident_id)
            prev_status = prev_inc.status if prev_inc else "UNKNOWN"
            prev_people = prev_inc.current_people if prev_inc else None

            result_incident = self.memory.update_incident(
                match_decision.matched_incident_id,
                event,
                extraction,
                location
            )

            # Check escalations or resolutions
            if result_incident.status == "ESCALATING" and prev_status != "ESCALATING":
                metrics.escalations += 1
                self._emit("incident_escalated", {"incident": result_incident.model_dump()})
            elif result_incident.status == "RESOLVED" and prev_status != "RESOLVED":
                metrics.resolutions += 1
                self._emit("incident_resolved", {"incident": result_incident.model_dump()})
            else:
                self._emit("incident_updated", {"incident": result_incident.model_dump()})

            if result_incident.has_people_conflict:
                metrics.conflicts += 1
                self._emit("conflict_detected", {
                    "incident_id": result_incident.incident_id,
                    "details": result_incident.people_conflict_details
                })

        else:
            # CREATE_NEW (or UNCERTAIN without high match confidence)
            metrics.new_incidents += 1
            result_incident = self.memory.create_incident(event, extraction, location)
            self._emit("incident_created", {"incident": result_incident.model_dump()})

        self._emit("stats_updated", self.get_overall_stats().model_dump())
        return {
            "status": "PROCESSED",
            "incident_id": result_incident.incident_id,
            "decision": match_decision.decision,
            "match_score": match_decision.score
        }

    def process_next_event(self) -> Optional[Dict[str, Any]]:
        stg = self.current_stage
        events = self._stage_events.get(stg, [])
        if self._event_cursor >= len(events):
            return None

        event = events[self._event_cursor]
        self._event_cursor += 1
        return self.process_event(event)

    def process_all_current_stage(self) -> int:
        stg = self.current_stage
        events = self._stage_events.get(stg, [])
        t0 = time.time()
        count = 0
        while self._event_cursor < len(events):
            event = events[self._event_cursor]
            self._event_cursor += 1
            self.process_event(event)
            count += 1
        elapsed = time.time() - t0
        self._stage_metrics[stg].processing_time_seconds = round(elapsed, 2)
        self._emit("stage_completed", {"stage": stg, "processed": count, "elapsed": elapsed})
        return count

    def advance_to_next_stage(self) -> bool:
        """
        Advances to next stage while PRESERVING all incident memory!
        """
        # Finish current stage if not finished
        if self._event_cursor < len(self._stage_events.get(self.current_stage, [])):
            self.process_all_current_stage()

        if self.current_stage_idx + 1 < len(self.stages):
            self.current_stage_idx += 1
            self._event_cursor = 0
            new_stage = self.current_stage
            logger.info(f"Advanced to stage {new_stage} (Memory preserved: {len(self.memory.get_all_incidents())} incidents)")
            self._emit("stage_started", {"stage": new_stage, "stage_index": self.current_stage_idx})
            return True
        return False

    def reset(self):
        self.is_running = False
        self.is_paused = False
        self.current_stage_idx = 0
        self._event_cursor = 0
        self.memory.reset()
        for stg in self.stages:
            self._stage_metrics[stg] = StageMetrics(stage_name=stg, reports_received=len(self._stage_events.get(stg, [])))
        self._emit("reset", {})

# Singleton instance
stage_engine = StageEngine()
