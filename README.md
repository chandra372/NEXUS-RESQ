# NEXUS RESQ
### AI Emergency Incident Intelligence & Response Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg)](https://tailwindcss.com/)

---

## What is NEXUS RESQ?

**NEXUS RESQ** is a multi-modal AI decision-support platform designed to convert chaotic, high-volume emergency reports from voice audio, WhatsApp, SMS, and Twitter into continuously updated, evidence-backed incident timelines for human first responders and emergency dispatchers.

> **CRITICAL ARCHITECTURAL PRINCIPLE:**
> NEXUS RESQ is a **DECISION-SUPPORT ASSISTANT**. It **NEVER** acts as an autonomous command authority. All state changes, priority calculations, and cluster linkages are transparent, auditable, and traceable back to original source reports.

---

## Core Transformation

```
RAW REPORTS (Audio, WhatsApp, SMS, Social)
    ↓
UNIFIED EVENTS
    ↓
AI UNDERSTANDING & CLASSIFICATION
    ↓
EVIDENCE EXTRACTION & LANDMARK RESOLUTION
    ↓
MULTI-FACTOR INCIDENT CLUSTERING (30% Semantic, 25% Location, 15% Landmark, 10% Time, 10% Hazard, 5% Resource, 5% Entity)
    ↓
INCIDENT MEMORY & REOPEN PROTECTION
    ↓
DETERMINISTIC STATE MACHINE (Detected -> Active -> Escalating -> Rescue -> Resolved)
    ↓
DETERMINISTIC PRIORITY ENGINE (0 - 100)
    ↓
RESPONDER DASHBOARD
```

---

## Verified Benchmark Results

Evaluated independently against `emergency_dataset/ground_truth.json` with **zero ground-truth leakage**:

- **Emergency Intent Classification:** **100.0%**
- **Noise & Rumor Filtering:** **92.06%**
- **Location Resolution Accuracy:** **91.01%**
- **Resource Extraction Accuracy:** **88.41%**
- **Status Transition Accuracy:** **95.77%**
- **Incident Clustering Accuracy (ARI):** **93.66%**
- **People Count Mean Absolute Error (MAE):** **1.11**

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher (Node 24 tested)
- npm

### 2. Backend Setup
```bash
# Navigate to backend directory
cd nexus-resq/backend

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI backend will start on `http://localhost:8000`.
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd nexus-resq/frontend

# Install dependencies (if not already installed)
npm install

# Start Vite development server
npm run dev
```
The React Responder Dashboard will open at `http://localhost:5173`.
*(Note: The backend also directly serves the compiled frontend single-page application at `http://localhost:8000`!)*

---

## Running the Automated Test Suite

NEXUS RESQ includes 24 comprehensive unit and integration tests:

```bash
# Run all unit and integration tests
python -m pytest nexus-resq/backend/tests/test_unit.py nexus-resq/backend/tests/test_integration.py -v
```

All 24 tests pass cleanly with 100% success rate:
- Dataset discovery and CSV/JSON/Audio parsing
- Emergency, Noise, and Rumor classification
- Multi-lingual information extraction (English & Telugu)
- Landmark and canonical location resolution
- Multi-factor incident matching & duplicate merging
- Deterministic state machine transitions & escalation
- People count conflict detection and recency-weighted estimation
- Resolved incident protection against stale duplicates
- End-to-end multi-stage replay and FastAPI endpoints

---

## CLI Replay & Evaluation Scripts

### Stream Replay Runner
```bash
# Replay 3 stages with live console metrics
python nexus-resq/backend/scripts/replay_dataset.py --stages 3 --speed 10
```

### Independent Benchmark Evaluation
```bash
# Run Ground Truth validation benchmark
python nexus-resq/backend/evaluation/evaluate.py
```

---

## Documentation Links

- [Architecture & Design Details](docs/ARCHITECTURE.md)
- [REST & WebSocket API Specification](docs/API.md)
- [Hackathon Live Demo Script](docs/DEMO.md)
- [Comprehensive Evaluation Benchmark Report](docs/EVALUATION.md)
