# NEXUS RESQ — API Documentation

Base URL: `http://localhost:8000/api`

---

## Health & System Info

### `GET /api/health`
Returns system status, active version, and AI/speech provider modes.
```json
{
  "status": "healthy",
  "service": "NEXUS RESQ",
  "version": "1.0.0",
  "ai_provider": "Local/Fallback Rule & Embeddings Engine",
  "speech_provider": "Local STT (SpeechRecognition / Whisper Compatible)"
}
```

### `GET /api/stats`
Returns aggregate stream metrics, active/critical incidents, noise filtered, and per-stage breakdowns.

### `GET /api/stages`
Returns discovered lifecycle stages (`stage_1`, `stage_2`, `stage_3`, etc.) and the active stage index.

---

## Incidents & Situational Intelligence

### `GET /api/incidents`
Query discovered incidents with optional filters:
- `status`: `ACTIVE`, `ESCALATING`, `RESCUE_IN_PROGRESS`, `RESOLVED`, `DETECTED`
- `priority`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- `stage`: `stage_1`, `stage_2`, etc.

### `GET /api/incidents/{incident_id}`
Returns the comprehensive incident object including canonical location, current casualty estimate, conflict flags, AI reasoning, and audit ledger.

### `GET /api/incidents/{incident_id}/timeline`
Returns the chronological transition and observation history.

### `GET /api/incidents/{incident_id}/evidence`
Returns all corroborating raw source reports with reliability weightings.

### `GET /api/incidents/{incident_id}/sources`
Returns compact source report audit logs.

### `GET /api/rumors`
Returns isolated unverified/rumor broadcasts with suppression rationale and confidence ratings.

---

## Stream Replay & Ingestion

### `POST /api/process`
Advances the event stream by 1 report.

### `POST /api/process/all`
Processes all remaining reports in the active stage.

### `POST /api/replay/start?speed=5`
Starts automated background stream processing at specified speed (`1x`, `5x`, `20x`).

### `POST /api/replay/pause`
Pauses active replay.

### `POST /api/replay/reset`
Resets all in-memory incidents, metrics, and cursor.

### `POST /api/replay/next-stage`
Advances to the next lifecycle stage while **preserving all incident memory**.

### `GET /api/replay/status`
Returns live replay progress and cursor statistics.

---

## Multimodal Audio & Evaluation

### `POST /api/audio/transcribe`
Upload an audio file (`.mp3`, `.wav`) for real speech-to-text transcription.

### `GET /api/evaluation`
Executes an independent benchmark run against `ground_truth.json` and returns accuracy scores for intent classification, location resolution, resource extraction, status transitions, and clustering Adjusted Rand Index (ARI).

---

## Real-Time WebSocket

### `WS /api/ws`
Streams live updates:
- `incident_created`
- `incident_updated`
- `incident_escalated`
- `incident_resolved`
- `conflict_detected`
- `rumor_detected`
- `stage_completed`
- `stats_updated`
