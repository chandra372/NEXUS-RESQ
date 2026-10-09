# NEXUS RESQ — Hackathon Live Demo Guide

## The Core Pitch
> *"During large-scale floods or urban fires, emergency response centers receive thousands of frantic WhatsApp messages, tweets, and helpline calls. Showing dispatchers 1,000 raw messages creates paralysis. NEXUS RESQ synthesizes thousands of noisy observations into a handful of continuously updated, evidence-backed incident timelines."*

---

## 5-Minute Demonstration Walkthrough

### Step 1: Clean Slate (0:00 - 0:30)
1. Open the dashboard at `http://localhost:5173` or `http://localhost:8000`.
2. Observe the clean, responder-oriented dark interface:
   - Live stream progress: 0 / 471 reports
   - Active Incidents: 0
   - Center: Interactive Chennai Operations Map
   - Right: Empty Critical Alerts and Rumor Feed

### Step 2: Stage 1 — Initial Discovery (0:30 - 1:30)
1. Click **Process Stage** in the top toolbar.
2. Watch NEXUS RESQ ingest 157 reports (SMS, WhatsApp, Twitter, and Audio calls).
3. **Key Visuals to Show Judges:**
   - Instead of 157 cards, NEXUS RESQ clusters them into core emerging situations:
     - **Velachery Flood Medical Emergency** (Insulin request, diabetic patient)
     - **Tambaram Transformer Fire** (EB compound fire tender request)
     - **Medavakkam Flood Rescue** (School road boat request)
   - Noise chatter ("Swiggy working today?", "Office timings?") is filtered into the Noise metric.
   - Click any card -> Point to **"Why does AI believe this?"**:
     - *✓ Same landmark: Velachery MRTS*
     - *✓ Clustered around geographic epicenter*
     - *✓ Corroborating reports across SMS, WhatsApp, Twitter*

### Step 3: Stage 2 — Escalation & Conflict Detection (1:30 - 2:45)
1. Click **Next Stage** (Notice: Memory is preserved!).
2. Click **Process Stage**.
3. **Key Visuals to Show Judges:**
   - **Escalation Detected:** Casualty numbers increase (Velachery: 2 -> 6; Tambaram: 12 -> 18; Medavakkam: 7 -> 11).
   - Priority scores dynamically elevate to **CRITICAL**.
   - **Conflict Detection:** Point to the **CONFLICT DETECTED** badge on the incident card. Open the card to show:
     - Current best estimate
     - Conflicting source reports breakdown with timestamps
     - Explanatory rationale: *"Never hide uncertainty from responders."*

### Step 4: Stage 3 — Response, Resolution & Protection (2:45 - 4:00)
1. Click **Next Stage** -> Click **Process Stage**.
2. **Key Visuals to Show Judges:**
   - **Resolution Detection:** Fire service extinguishes the transformer; medical team delivers insulin.
   - Incidents transition from `ACTIVE` / `ESCALATING` to `RESOLVED` (Green badges on map).
   - **Resolved Incident Protection:** Point to the terminal or audit log showing:
     - *"Ignoring post-resolution stale/duplicate report for INC-001"*
     - Subsequent duplicates or delayed messages are prevented from re-triggering alarms.
   - Active incident persistence: Medavakkam flood evacuation remains `ACTIVE` as evacuations continue.

### Step 5: Independent Evaluation Benchmark (4:00 - 5:00)
1. Click **View Benchmark** in the top bar.
2. The modal runs the evaluation suite live against `ground_truth.json`:
   - Emergency Classification Accuracy: **100.0%**
   - Noise Classification Accuracy: **92.06%**
   - Location Resolution Accuracy: **91.01%**
   - Incident Clustering Accuracy (ARI): **93.66%**
   - Status Transition Accuracy: **95.77%**
3. Emphasize: **Zero ground-truth leakage into inference.** The system discovered the incidents organically.
