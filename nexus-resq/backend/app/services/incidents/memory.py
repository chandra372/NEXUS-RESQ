import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from app.schemas.events import UnifiedEvent, ExtractionResult, LocationResolutionResult
from app.schemas.incident import (
    IncidentDetail, IncidentSummary, TimelineItem, EvidenceItem,
    ObservationRecord, ReopenRecord
)
from app.services.priority.priority_engine import PriorityEngine
from app.services.evidence.evidence_engine import EvidenceEngine

logger = logging.getLogger(__name__)

class IncidentMemoryStore:
    """
    In-memory persistent evolving store for incidents, evidence ledgers,
    timeline state transitions, people count observations, and resolved protection.
    """

    def __init__(self):
        self._incidents: Dict[str, IncidentDetail] = {}
        self._incident_counter: int = 0
        self._rumors: List[Dict[str, Any]] = []
        self._processed_events: List[str] = []

    def get_all_incidents(self) -> List[IncidentDetail]:
        return list(self._incidents.values())

    def get_incident(self, incident_id: str) -> Optional[IncidentDetail]:
        return self._incidents.get(incident_id)

    def get_rumors(self) -> List[Dict[str, Any]]:
        return list(self._rumors)

    def add_rumor(self, rumor_item: Dict[str, Any]):
        self._rumors.append(rumor_item)

    def reset(self):
        self._incidents.clear()
        self._incident_counter = 0
        self._rumors.clear()
        self._processed_events.clear()

    def create_incident(
        self,
        event: UnifiedEvent,
        extraction: ExtractionResult,
        location: LocationResolutionResult
    ) -> IncidentDetail:
        self._incident_counter += 1
        inc_id = f"INC-{self._incident_counter:03d}"

        zone_title = location.canonical_location or "Emergency Alert"
        type_str = extraction.incident_type or "CRITICAL_SITUATION"
        title = f"{type_str.replace('_', ' ').title()} - {zone_title}"

        now_str = event.timestamp

        initial_people = extraction.people_count
        current_people = extraction.people_count
        max_people = extraction.people_count
        obs_records = []
        if extraction.people_count is not None:
            obs = ObservationRecord(
                people_count=extraction.people_count,
                source_id=event.source_id,
                source_type=event.source,
                timestamp=event.timestamp,
                confidence=extraction.evidence_strength
            )
            obs_records.append(obs)

        status = "ACTIVE"
        if extraction.resolution_signal:
            status = "RESOLVED"
        elif extraction.rescue_signal:
            status = "RESCUE_IN_PROGRESS"
        elif extraction.urgency == "HIGH":
            status = "ACTIVE"
        else:
            status = "DETECTED"

        resources = [extraction.resource_needed] if extraction.resource_needed else []
        hazards = list(extraction.hazards)

        p_score, p_level = PriorityEngine.calculate_priority(
            current_people,
            extraction.vulnerable_people,
            hazards,
            extraction.urgency,
            status,
            resources,
            extraction.evidence_strength
        )

        reliability = EvidenceEngine.get_source_reliability(event.source, event.sender)
        ev_item = EvidenceItem(
            source_id=event.source_id,
            source_type=event.source,
            timestamp=event.timestamp,
            raw_text=event.raw_text,
            sender=event.sender,
            reliability=reliability,
            extracted_features={
                "people_count": extraction.people_count,
                "vulnerable": extraction.vulnerable_people,
                "landmarks": extraction.landmarks,
                "resource": extraction.resource_needed
            }
        )

        t_item = TimelineItem(
            timestamp=event.timestamp,
            stage=event.stage_name,
            event_type="CREATED",
            description=f"Incident detected via {event.source.upper()} ({event.source_id}): {event.raw_text[:90]}",
            source_id=event.source_id,
            source_type=event.source,
            details={"initial_status": status, "priority": p_level}
        )

        why_ai, conf = EvidenceEngine.generate_ai_reasoning(
            title,
            location.canonical_location or "",
            location.landmarks,
            hazards,
            [ev_item],
            extraction.vulnerable_people,
            status
        )

        incident = IncidentDetail(
            incident_id=inc_id,
            name=title,
            incident_type=type_str,
            canonical_location=location.canonical_location or "Chennai Metropolitan Area",
            latitude=location.latitude,
            longitude=location.longitude,
            location_precision=location.location_precision,
            location_confidence=location.confidence,
            landmarks=list(set(location.landmarks + extraction.landmarks)),
            status=status,
            urgency=extraction.urgency,
            priority_score=p_score,
            priority_level=p_level,
            initial_people=initial_people,
            current_people=current_people,
            max_reported_people=max_people,
            has_people_conflict=False,
            vulnerable_people=list(set(extraction.vulnerable_people)),
            resources_needed=resources,
            hazards=hazards,
            evidence_count=1,
            confidence=conf,
            first_seen_stage=event.stage_name,
            last_updated_stage=event.stage_name,
            created_at=now_str,
            updated_at=now_str,
            why_ai_believes=why_ai,
            is_resolved=(status == "RESOLVED"),
            resolved_at=(now_str if status == "RESOLVED" else None),
            timeline=[t_item],
            evidence=[ev_item],
            people_observations=obs_records,
            people_conflict_details=None,
            reopen_history=[]
        )

        self._incidents[inc_id] = incident
        self._processed_events.append(event.event_id)
        logger.info(f"Created new incident {inc_id}: {title}")
        return incident

    def update_incident(
        self,
        incident_id: str,
        event: UnifiedEvent,
        extraction: ExtractionResult,
        location: LocationResolutionResult
    ) -> IncidentDetail:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # 1. Resolved Incident Protection Check
        if incident.is_resolved:
            raw_lower = event.raw_text.lower()
            # Stale duplicate check: check for words indicating past or contained event
            is_stale_or_duplicate = any(w in raw_lower for w in [
                "isolated", "extinguished", "controlled", "same incident", "same location",
                "completed", "delivered", "safety", "no further", "no additional", "area isolated"
            ]) or extraction.resolution_signal

            # Only explicit new danger triggers reopening
            has_credible_fresh_danger = any(w in raw_lower for w in [
                "spread", "reignited", "re-ignited", "new fire", "explosion", "water rising again",
                "trapped again", "second fire", "collapse"
            ])

            if not has_credible_fresh_danger or is_stale_or_duplicate:
                logger.info(f"Ignoring post-resolution stale/duplicate report for {incident_id}: {event.source_id}")
                reliability = EvidenceEngine.get_source_reliability(event.source, event.sender)
                incident.evidence.append(EvidenceItem(
                    source_id=event.source_id,
                    source_type=event.source,
                    timestamp=event.timestamp,
                    raw_text=event.raw_text,
                    sender=event.sender,
                    reliability=reliability,
                    extracted_features={"status": "SUPPRESSED_POST_RESOLUTION"}
                ))
                return incident

            # Credible new emergency triggers reopen
            reopen_rec = ReopenRecord(
                previous_status=incident.status,
                new_status="ACTIVE",
                reopen_reason=f"New severe distress signals detected: {event.raw_text[:80]}",
                reopen_evidence=f"Report {event.source_id} via {event.source}",
                reopened_at=event.timestamp
            )
            incident.reopen_history.append(reopen_rec)
            incident.is_resolved = False
            incident.resolved_at = None
            incident.status = "ACTIVE"
            incident.timeline.append(TimelineItem(
                timestamp=event.timestamp,
                stage=event.stage_name,
                event_type="REOPENED",
                description=f"Incident REOPENED due to credible new distress evidence: {event.source_id}",
                source_id=event.source_id,
                source_type=event.source
            ))

        # 2. Update Location Landmarks
        for lm in extraction.landmarks + location.landmarks:
            if lm and lm not in incident.landmarks:
                incident.landmarks.append(lm)

        if location.canonical_location and not incident.canonical_location:
            incident.canonical_location = location.canonical_location
            incident.latitude = location.latitude
            incident.longitude = location.longitude

        # 3. Update Vulnerable People & Resources & Hazards
        for v in extraction.vulnerable_people:
            if v not in incident.vulnerable_people:
                incident.vulnerable_people.append(v)
                incident.timeline.append(TimelineItem(
                    timestamp=event.timestamp,
                    stage=event.stage_name,
                    event_type="VULNERABILITY_DETECTED",
                    description=f"Vulnerable population verified: {v.upper()}",
                    source_id=event.source_id,
                    source_type=event.source
                ))

        if extraction.resource_needed and extraction.resource_needed not in incident.resources_needed:
            incident.resources_needed.append(extraction.resource_needed)
            incident.timeline.append(TimelineItem(
                timestamp=event.timestamp,
                stage=event.stage_name,
                event_type="RESOURCE_UPDATE",
                description=f"Resource dispatch request: {extraction.resource_needed}",
                source_id=event.source_id,
                source_type=event.source
            ))

        for h in extraction.hazards:
            if h not in incident.hazards:
                incident.hazards.append(h)

        # 4. Update People Count & Run Conflict Detection
        if extraction.people_count is not None:
            obs = ObservationRecord(
                people_count=extraction.people_count,
                source_id=event.source_id,
                source_type=event.source,
                timestamp=event.timestamp,
                confidence=extraction.evidence_strength
            )
            incident.people_observations.append(obs)

            best_est, has_conflict, conflict_details = EvidenceEngine.evaluate_people_conflict(
                incident.people_observations
            )
            prev_people = incident.current_people
            incident.current_people = best_est
            incident.has_people_conflict = has_conflict
            incident.people_conflict_details = conflict_details

            all_counts = [o.people_count for o in incident.people_observations]
            incident.max_reported_people = max(all_counts)

            if prev_people is not None and best_est is not None and best_est > prev_people:
                incident.timeline.append(TimelineItem(
                    timestamp=event.timestamp,
                    stage=event.stage_name,
                    event_type="ESCALATION",
                    description=f"People affected escalated from {prev_people} to {best_est}",
                    source_id=event.source_id,
                    source_type=event.source,
                    details={"previous": prev_people, "new": best_est}
                ))

        # 5. Deterministic State Transitions
        old_status = incident.status
        if extraction.resolution_signal:
            incident.status = "RESOLVED"
            incident.is_resolved = True
            incident.resolved_at = event.timestamp
            incident.timeline.append(TimelineItem(
                timestamp=event.timestamp,
                stage=event.stage_name,
                event_type="RESOLVED",
                description=f"Credible resolution verified via {event.source_id}: Emergency successfully controlled/rescued",
                source_id=event.source_id,
                source_type=event.source
            ))

        elif extraction.rescue_signal and incident.status in ["DETECTED", "ACTIVE", "ESCALATING"]:
            incident.status = "RESCUE_IN_PROGRESS"
            incident.timeline.append(TimelineItem(
                timestamp=event.timestamp,
                stage=event.stage_name,
                event_type="RESCUE_PROGRESS",
                description=f"Rescue team deployment confirmed: Evacuation in progress",
                source_id=event.source_id,
                source_type=event.source
            ))

        elif (incident.current_people and incident.initial_people and incident.current_people > incident.initial_people) and incident.status == "ACTIVE":
            incident.status = "ESCALATING"

        # 6. Append Evidence Item
        reliability = EvidenceEngine.get_source_reliability(event.source, event.sender)
        incident.evidence.append(EvidenceItem(
            source_id=event.source_id,
            source_type=event.source,
            timestamp=event.timestamp,
            raw_text=event.raw_text,
            sender=event.sender,
            reliability=reliability,
            extracted_features={
                "people_count": extraction.people_count,
                "vulnerable": extraction.vulnerable_people,
                "landmarks": extraction.landmarks,
                "resource": extraction.resource_needed,
                "status_signal": extraction.status_signal
            }
        ))
        incident.evidence_count = len(incident.evidence)

        # 7. Recalculate Priority & AI Reasoning
        p_score, p_level = PriorityEngine.calculate_priority(
            incident.current_people,
            incident.vulnerable_people,
            incident.hazards,
            extraction.urgency,
            incident.status,
            incident.resources_needed,
            incident.confidence
        )
        incident.priority_score = p_score
        incident.priority_level = p_level

        why_ai, conf = EvidenceEngine.generate_ai_reasoning(
            incident.name,
            incident.canonical_location,
            incident.landmarks,
            incident.hazards,
            incident.evidence,
            incident.vulnerable_people,
            incident.status
        )
        incident.why_ai_believes = why_ai
        incident.confidence = conf
        incident.last_updated_stage = event.stage_name
        incident.updated_at = event.timestamp

        self._processed_events.append(event.event_id)
        return incident
