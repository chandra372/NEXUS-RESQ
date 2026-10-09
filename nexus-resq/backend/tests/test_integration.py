import pytest
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.stages.stage_engine import stage_engine
from evaluation.evaluate import Evaluator

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "NEXUS RESQ"

def test_api_stages_and_stats():
    response = client.get("/api/stages")
    assert response.status_code == 200
    data = response.json()
    assert len(data["stages"]) >= 3

    stats_resp = client.get("/api/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "reports_received" in stats
    assert "current_stage" in stats

def test_full_pipeline_stage_1_replay():
    stage_engine.reset()
    assert len(stage_engine.memory.get_all_incidents()) == 0

    # Process all events in stage 1
    processed = stage_engine.process_all_current_stage()
    assert processed >= 150

    incidents = stage_engine.memory.get_all_incidents()
    assert len(incidents) > 0
    # Core stories should be discovered without hardcoding IDs
    titles = " ".join([i.name for i in incidents])
    assert "Velachery" in titles or "Tambaram" in titles or "Medavakkam" in titles

def test_multi_stage_memory_continuation():
    # Advance to stage 2
    advanced = stage_engine.advance_to_next_stage()
    assert advanced is True
    assert stage_engine.current_stage == "stage_2"

    prev_count = len(stage_engine.memory.get_all_incidents())
    assert prev_count > 0  # Memory was NOT wiped out!

    # Process stage 2
    processed = stage_engine.process_all_current_stage()
    assert processed >= 150

    # Escalations should be captured
    stats = stage_engine.get_overall_stats()
    s2_metrics = stats.stage_metrics.get("stage_2")
    assert s2_metrics is not None
    assert s2_metrics.reports_processed >= 150

def test_stage_3_resolution_and_api_queries():
    # Advance to stage 3
    advanced = stage_engine.advance_to_next_stage()
    assert advanced is True
    assert stage_engine.current_stage == "stage_3"

    processed = stage_engine.process_all_current_stage()
    assert processed >= 150

    incidents = stage_engine.memory.get_all_incidents()
    resolved_incidents = [i for i in incidents if i.is_resolved]
    assert len(resolved_incidents) >= 1

    # Verify query by incident ID
    first_inc = incidents[0]
    detail_resp = client.get(f"/api/incidents/{first_inc.incident_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["incident_id"] == first_inc.incident_id
    assert len(detail["evidence"]) > 0

    # Verify timeline endpoint
    tl_resp = client.get(f"/api/incidents/{first_inc.incident_id}/timeline")
    assert tl_resp.status_code == 200
    assert len(tl_resp.json()) > 0

def test_benchmark_evaluation_integration():
    evaluator = Evaluator()
    results = evaluator.run_evaluation()
    assert results["emergency_classification_accuracy"] >= 95.0
    assert results["noise_classification_accuracy"] >= 85.0
    assert results["location_accuracy"] >= 85.0
    assert results["incident_clustering_accuracy_ari"] >= 80.0
