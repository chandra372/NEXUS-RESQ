import pytest
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.events import UnifiedEvent, ExtractionResult, LocationResolutionResult
from app.services.ai.classifier import EmergencyClassifier
from app.services.extraction.extractor import InformationExtractor
from app.services.location.resolver import LocationResolver
from app.services.clustering.matcher import IncidentMatcher
from app.services.priority.priority_engine import PriorityEngine
from app.services.evidence.evidence_engine import EvidenceEngine
from app.services.incidents.memory import IncidentMemoryStore
from app.services.ingestion.discovery import DatasetDiscovery
from app.schemas.incident import ObservationRecord

# 1. Dataset Ingestion & Discovery Tests
def test_dataset_discovery_stages():
    discovery = DatasetDiscovery()
    stages = discovery.discover_stages()
    assert len(stages) >= 3
    assert "stage_1" in stages
    assert "stage_2" in stages
    assert "stage_3" in stages

def test_csv_parsing():
    discovery = DatasetDiscovery()
    events = discovery.ingest_stage("stage_1", transcribe_audio=False)
    assert len(events) >= 150
    # Verify UnifiedEvent schema compliance
    evt = events[0]
    assert evt.event_id.startswith("evt_")
    assert evt.source in ["sms", "twitter", "whatsapp", "audio"]
    assert evt.raw_text != ""
    assert evt.stage_name == "stage_1"

def test_json_parsing():
    discovery = DatasetDiscovery()
    events = discovery.ingest_stage("stage_1", transcribe_audio=False)
    wa_events = [e for e in events if e.source == "whatsapp"]
    assert len(wa_events) == 50
    assert wa_events[0].sender is not None

def test_audio_handling_graceful():
    discovery = DatasetDiscovery()
    events = discovery.ingest_stage("stage_1", transcribe_audio=False)
    audio_events = [e for e in events if e.source == "audio"]
    assert len(audio_events) == 7
    assert audio_events[0].audio_path is not None

# 2. Classification Tests
def test_classification_emergency():
    clf = EmergencyClassifier()
    evt = UnifiedEvent(
        event_id="t1", source="sms", source_id="s1", timestamp="2026-10-07T08:00:00",
        raw_text="Rescue boat reached the location. 11 people are being evacuated.",
        language="en", sender="HELPLINE"
    )
    res = clf.classify(evt)
    assert res.intent == "EMERGENCY"
    assert res.confidence > 0.70

def test_classification_noise():
    clf = EmergencyClassifier()
    evt = UnifiedEvent(
        event_id="t2", source="sms", source_id="s2", timestamp="2026-10-07T08:00:00",
        raw_text="Swiggy working today or not?",
        language="en", sender="resident"
    )
    res = clf.classify(evt)
    assert res.intent == "NOISE"

def test_rumour_filtering():
    clf = EmergencyClassifier()
    evt = UnifiedEvent(
        event_id="t3", source="twitter", source_id="s3", timestamp="2026-10-07T08:00:00",
        raw_text="Forwarded message: Chennai will receive extreme rain at exactly midnight.",
        language="en", sender="@user"
    )
    res = clf.classify(evt)
    assert res.intent == "RUMOR"
    assert "UNVERIFIED_FORWARD" in res.risk_flags

# 3. Extraction Tests
def test_extraction_people_count():
    ex = InformationExtractor()
    evt = UnifiedEvent(
        event_id="t4", source="sms", source_id="s4", timestamp="2026-10-07T08:00:00",
        raw_text="Rescue team reached. All 18 people were affected and are safe.",
        language="en", sender="HELPLINE"
    )
    res = ex.extract(evt)
    assert res.people_count == 18

def test_extraction_unknown_people_count_is_none():
    ex = InformationExtractor()
    evt = UnifiedEvent(
        event_id="t5", source="sms", source_id="s5", timestamp="2026-10-07T08:00:00",
        raw_text="Transformer fire reported near EB compound.",
        language="en", sender="HELPLINE"
    )
    res = ex.extract(evt)
    assert res.people_count is None  # MUST be None, NEVER 0!

def test_extraction_vulnerable_people():
    ex = InformationExtractor()
    evt = UnifiedEvent(
        event_id="t6", source="sms", source_id="s6", timestamp="2026-10-07T08:00:00",
        raw_text="Elderly woman and diabetic patient need urgent assistance.",
        language="en", sender="HELPLINE"
    )
    res = ex.extract(evt)
    assert "elderly" in res.vulnerable_people
    assert "diabetic" in res.vulnerable_people

def test_extraction_resources():
    ex = InformationExtractor()
    evt1 = UnifiedEvent(
        event_id="t7", source="sms", source_id="s7", timestamp="2026-10-07T08:00:00",
        raw_text="Diabetic patient received insulin dispatch.", language="en", sender="HELPLINE"
    )
    assert ex.extract(evt1).resource_needed == "MEDICAL_INSULIN"

    evt2 = UnifiedEvent(
        event_id="t8", source="sms", source_id="s8", timestamp="2026-10-07T08:00:00",
        raw_text="Need NDRF boat for flood evacuation.", language="en", sender="HELPLINE"
    )
    assert ex.extract(evt2).resource_needed == "NDRF_BOAT"

    evt3 = UnifiedEvent(
        event_id="t9", source="sms", source_id="s9", timestamp="2026-10-07T08:00:00",
        raw_text="Fire tender required immediately.", language="en", sender="HELPLINE"
    )
    assert ex.extract(evt3).resource_needed == "FIRE_TENDER"

# 4. Location Resolution Tests
def test_location_resolution_exact_and_landmark():
    loc_res = LocationResolver()
    res1 = loc_res.resolve("behind Velachery MRTS west-side approach road")
    assert res1.canonical_location == "Velachery MRTS west-side approach"
    assert res1.latitude is not None and res1.longitude is not None
    assert res1.location_precision in ["landmark", "area"]

    res2 = loc_res.resolve("near Tambaram Sanatorium electrical compound approach")
    assert res2.canonical_location == "Tambaram Sanatorium railway station electrical compound approach"

    res3 = loc_res.resolve("second lane behind Medavakkam government school road")
    assert res3.canonical_location == "Medavakkam school-road residential lane"

def test_location_resolution_unknown():
    loc_res = LocationResolver()
    res = loc_res.resolve("No location details here whatsoever.")
    assert res.canonical_location is None
    assert res.location_precision == "unknown"

# 5. Matching & Duplicate Detection Tests
def test_incident_matching_and_duplicate_merge():
    mem = IncidentMemoryStore()
    matcher = IncidentMatcher()
    loc_res = LocationResolver()
    ex = InformationExtractor()

    evt1 = UnifiedEvent(
        event_id="m1", source="sms", source_id="s1", timestamp="2026-10-07T08:00:00",
        raw_text="Velachery MRTS west side flood with 2 diabetic people needing insulin.",
        language="en", sender="HELPLINE"
    )
    ext1 = ex.extract(evt1)
    loc1 = loc_res.resolve(evt1.raw_text, ext1.landmarks)
    inc = mem.create_incident(evt1, ext1, loc1)

    # Corroborating second event for same incident
    evt2 = UnifiedEvent(
        event_id="m2", source="whatsapp", source_id="w1", timestamp="2026-10-07T08:05:00",
        raw_text="Behind Velachery MRTS medical emergency with diabetic patient needing insulin.",
        language="en", sender="resident_1"
    )
    ext2 = ex.extract(evt2)
    loc2 = loc_res.resolve(evt2.raw_text, ext2.landmarks)

    decision = matcher.match(evt2, ext2, loc2, mem.get_all_incidents())
    assert decision.decision == "MERGE"
    assert decision.matched_incident_id == inc.incident_id

# 6. Priority Calculation Tests
def test_priority_calculation():
    score_crit, level_crit = PriorityEngine.calculate_priority(
        people_count=18, vulnerable_people=["children", "elderly"], hazards=["electrical_fire"],
        urgency="HIGH", status="ACTIVE", resources_needed=["FIRE_TENDER"]
    )
    assert score_crit >= 80
    assert level_crit == "CRITICAL"

    score_low, level_low = PriorityEngine.calculate_priority(
        people_count=0, vulnerable_people=[], hazards=[],
        urgency="LOW", status="RESOLVED", resources_needed=[]
    )
    assert score_low <= 30
    assert level_low == "LOW"

# 7. State Transitions & People Updates
def test_state_machine_escalation():
    mem = IncidentMemoryStore()
    loc_res = LocationResolver()
    ex = InformationExtractor()

    evt1 = UnifiedEvent(
        event_id="st1", source="sms", source_id="s1", timestamp="2026-10-07T08:00:00",
        raw_text="Velachery MRTS initial 2 people trapped.", language="en", sender="HELPLINE"
    )
    inc = mem.create_incident(evt1, ex.extract(evt1), loc_res.resolve(evt1.raw_text))
    assert inc.current_people == 2

    # Escalating report with 6 people
    evt2 = UnifiedEvent(
        event_id="st2", source="sms", source_id="s2", timestamp="2026-10-07T08:10:00",
        raw_text="Velachery MRTS water rising, 6 people now affected.", language="en", sender="HELPLINE"
    )
    updated = mem.update_incident(inc.incident_id, evt2, ex.extract(evt2), loc_res.resolve(evt2.raw_text))
    assert updated.current_people == 6
    assert updated.status == "ESCALATING"

# 8. Conflict Detection Tests
def test_people_conflict_detection():
    obs = [
        ObservationRecord(people_count=10, source_id="s1", source_type="sms", timestamp="2026-10-07T08:00:00", confidence=0.9),
        ObservationRecord(people_count=6, source_id="w1", source_type="whatsapp", timestamp="2026-10-07T08:05:00", confidence=0.7),
        ObservationRecord(people_count=8, source_id="t1", source_type="twitter", timestamp="2026-10-07T08:10:00", confidence=0.6),
    ]
    best_est, has_conflict, details = EvidenceEngine.evaluate_people_conflict(obs)
    assert has_conflict is True
    assert best_est in [6, 8, 10]
    assert details is not None
    assert details["unique_reported_counts"] == [6, 8, 10]

# 9. Resolved Incident Protection Tests
def test_resolved_incident_protection():
    mem = IncidentMemoryStore()
    loc_res = LocationResolver()
    ex = InformationExtractor()

    evt1 = UnifiedEvent(
        event_id="r1", source="sms", source_id="s1", timestamp="2026-10-07T08:00:00",
        raw_text="Tambaram transformer fire fully controlled and extinguished.", language="en", sender="HELPLINE",
        stage_number=3, stage_name="stage_3"
    )
    inc = mem.create_incident(evt1, ex.extract(evt1), loc_res.resolve(evt1.raw_text))
    assert inc.is_resolved is True
    assert inc.status == "RESOLVED"

    # Stale duplicate report arrives after resolution
    evt2 = UnifiedEvent(
        event_id="r2", source="twitter", source_id="t1", timestamp="2026-10-07T08:30:00",
        raw_text="Tambaram Sanatorium transformer fire area isolated.", language="en", sender="@user",
        stage_number=3, stage_name="stage_3"
    )
    updated = mem.update_incident(inc.incident_id, evt2, ex.extract(evt2), loc_res.resolve(evt2.raw_text))
    # MUST stay resolved! Stale report cannot reopen!
    assert updated.is_resolved is True
    assert updated.status == "RESOLVED"
