import asyncio
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.schemas.incident import (
    IncidentDetail, IncidentSummary, TimelineItem, EvidenceItem,
    OverallStats, ReplayStatus, StageMetrics
)
from app.services.stages.stage_engine import stage_engine
from app.services.transcription.speech_provider import get_speech_provider
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections
active_connections: List[WebSocket] = []

def ws_broadcaster(event_payload: Dict[str, Any]):
    # Broadcast to connected websockets
    for conn in list(active_connections):
        try:
            asyncio.create_task(conn.send_json(event_payload))
        except Exception:
            pass

# Connect stage engine event emitter to websocket broadcaster
stage_engine.add_listener(ws_broadcaster)

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ai_provider": settings.AI_PROVIDER_NAME,
        "speech_provider": settings.SPEECH_PROVIDER_NAME
    }

@router.get("/stats", response_model=OverallStats)
def get_stats():
    return stage_engine.get_overall_stats()

@router.get("/stages")
def get_stages():
    return {
        "stages": stage_engine.stages,
        "current_stage": stage_engine.current_stage,
        "stage_index": stage_engine.current_stage_idx
    }

@router.get("/incidents", response_model=List[IncidentSummary])
def get_incidents(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    stage: Optional[str] = None
):
    incidents = stage_engine.memory.get_all_incidents()
    if status:
        incidents = [i for i in incidents if i.status.upper() == status.upper()]
    if priority:
        incidents = [i for i in incidents if i.priority_level.upper() == priority.upper()]
    if stage:
        incidents = [i for i in incidents if i.last_updated_stage.lower() == stage.lower()]
    return incidents

@router.get("/incidents/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: str):
    inc = stage_engine.memory.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@router.get("/incidents/{incident_id}/timeline", response_model=List[TimelineItem])
def get_incident_timeline(incident_id: str):
    inc = stage_engine.memory.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc.timeline

@router.get("/incidents/{incident_id}/evidence", response_model=List[EvidenceItem])
def get_incident_evidence(incident_id: str):
    inc = stage_engine.memory.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc.evidence

@router.get("/incidents/{incident_id}/sources")
def get_incident_sources(incident_id: str):
    inc = stage_engine.memory.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    sources = []
    for ev in inc.evidence:
        sources.append({
            "source_id": ev.source_id,
            "source_type": ev.source_type,
            "sender": ev.sender,
            "timestamp": ev.timestamp,
            "reliability": ev.reliability,
            "text": ev.raw_text
        })
    return {"incident_id": incident_id, "total_sources": len(sources), "sources": sources}

@router.get("/reports")
def get_reports(limit: int = 50, stage: Optional[str] = None):
    # Returns raw ingested reports
    stg = stage or stage_engine.current_stage
    events = stage_engine._stage_events.get(stg, [])
    return {
        "stage": stg,
        "total_reports": len(events),
        "reports": [e.model_dump() for e in events[:limit]]
    }

@router.get("/rumors")
def get_rumors():
    return {"rumors": stage_engine.memory.get_rumors()}

@router.post("/process")
def process_single_step():
    res = stage_engine.process_next_event()
    return {"result": res, "status": stage_engine.get_status().model_dump()}

@router.post("/process/all")
def process_all_current():
    count = stage_engine.process_all_current_stage()
    return {"processed": count, "status": stage_engine.get_status().model_dump()}

@router.post("/replay/start")
def start_replay(speed: int = 5):
    stage_engine.is_running = True
    stage_engine.is_paused = False
    stage_engine.speed = speed
    return {"message": "Replay started", "status": stage_engine.get_status().model_dump()}

@router.post("/replay/pause")
def pause_replay():
    stage_engine.is_paused = True
    stage_engine.is_running = False
    return {"message": "Replay paused", "status": stage_engine.get_status().model_dump()}

@router.post("/replay/reset")
def reset_replay():
    stage_engine.reset()
    return {"message": "Replay reset", "status": stage_engine.get_status().model_dump()}

@router.post("/replay/next-stage")
def next_stage():
    advanced = stage_engine.advance_to_next_stage()
    return {
        "advanced": advanced,
        "current_stage": stage_engine.current_stage,
        "status": stage_engine.get_status().model_dump()
    }

@router.get("/replay/status", response_model=ReplayStatus)
def get_replay_status():
    return stage_engine.get_status()

@router.post("/audio/transcribe")
async def transcribe_audio_file(file: UploadFile = File(...)):
    import tempfile, os
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    provider = get_speech_provider()
    res = provider.transcribe(tmp_path)
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return res.to_dict()

@router.get("/evaluation")
def run_evaluation_benchmark():
    from evaluation.evaluate import Evaluator
    evaluator = Evaluator()
    results = evaluator.run_evaluation()
    return results

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send initial state
        await websocket.send_json({
            "event_type": "initial_state",
            "data": {
                "stats": stage_engine.get_overall_stats().model_dump(),
                "status": stage_engine.get_status().model_dump()
            }
        })
        while True:
            # Keep connection alive, listen for client pings or commands
            msg = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)
