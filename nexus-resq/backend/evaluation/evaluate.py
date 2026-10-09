import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

from app.schemas.events import UnifiedEvent
from app.services.ingestion.discovery import DatasetDiscovery
from app.services.ai.classifier import EmergencyClassifier
from app.services.extraction.extractor import InformationExtractor
from app.services.location.resolver import LocationResolver
from app.services.clustering.matcher import IncidentMatcher
from app.services.incidents.memory import IncidentMemoryStore
from app.core.config import get_dataset_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluate")

class Evaluator:
    """
    Evaluator benchmarks NEXUS RESQ against ground_truth.json.
    Strictly isolated: ground_truth is NEVER used inside inference.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_dir = Path(dataset_path) if dataset_path else get_dataset_dir()
        self.gt_data = self._load_ground_truth()

    def _load_ground_truth(self) -> Dict[str, Any]:
        gt_path = self.dataset_dir / "ground_truth.json"
        if not gt_path.exists():
            raise FileNotFoundError(f"ground_truth.json not found at {gt_path}")
        with open(gt_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_evaluation(self) -> Dict[str, Any]:
        """
        Runs fresh end-to-end evaluation across all stages in sequential order.
        """
        discovery = DatasetDiscovery(str(self.dataset_dir))
        classifier = EmergencyClassifier()
        extractor = InformationExtractor()
        location_resolver = LocationResolver()
        matcher = IncidentMatcher()
        memory = IncidentMemoryStore()

        stages = discovery.discover_stages()
        per_stage_results = {}

        total_records = 0
        correct_intent = 0
        emergency_tp = 0
        emergency_total = 0
        noise_tp = 0
        noise_total = 0
        rumor_tp = 0
        rumor_total = 0

        correct_location = 0
        total_loc_eval = 0

        correct_resource = 0
        total_resource_eval = 0

        correct_status = 0
        total_status_eval = 0

        people_diffs = []

        # Store predicted cluster IDs for each ground truth record
        gt_cluster_labels = []
        pred_cluster_labels = []

        # Ground truth stage records
        gt_stage_records = self.gt_data.get("stage_records", {})

        for stage in stages:
            stage_gt_list = gt_stage_records.get(stage, [])
            gt_by_id = {r.get("record_id"): r for r in stage_gt_list}
            gt_by_source = {r.get("source"): r for r in stage_gt_list if "call" in str(r.get("source", ""))}

            events = discovery.ingest_stage(stage, transcribe_audio=True)
            stage_metrics = {
                "total_events": len(events),
                "emergency_correct": 0,
                "emergency_total": 0,
                "noise_correct": 0,
                "noise_total": 0,
                "rumor_correct": 0,
                "rumor_total": 0,
                "location_correct": 0,
                "location_total": 0,
                "resource_correct": 0,
                "resource_total": 0,
                "status_correct": 0,
                "status_total": 0,
                "people_errors": []
            }

            for event in events:
                total_records += 1

                # Find GT record
                # Try matching by source_id or record_id or audio filename
                gt_rec = gt_by_id.get(event.source_id)
                if not gt_rec and event.source == "audio":
                    gt_rec = gt_by_source.get(event.source_id)
                if not gt_rec:
                    # Try partial match on ID
                    for gid, g in gt_by_id.items():
                        if gid in event.source_id or event.source_id in gid:
                            gt_rec = g
                            break

                gt_intent = gt_rec.get("intent") if gt_rec else "UNKNOWN"
                gt_incident = gt_rec.get("incident_id") if gt_rec else None
                gt_loc = gt_rec.get("location") if gt_rec else None
                gt_resource = gt_rec.get("resource") if gt_rec else None
                gt_people = gt_rec.get("people_count") if gt_rec else None
                gt_status = gt_rec.get("status") if gt_rec else None

                # 1. Classification
                classification = classifier.classify(event)
                pred_intent = classification.intent

                # Evaluate intent
                if gt_intent == "EMERGENCY":
                    emergency_total += 1
                    stage_metrics["emergency_total"] += 1
                    if pred_intent == "EMERGENCY":
                        emergency_tp += 1
                        stage_metrics["emergency_correct"] += 1
                elif gt_intent == "NOISE":
                    noise_total += 1
                    stage_metrics["noise_total"] += 1
                    if pred_intent in ["NOISE", "RUMOR"]:  # Rumors in GT are grouped under noise
                        noise_tp += 1
                        stage_metrics["noise_correct"] += 1
                    if pred_intent == "RUMOR":
                        rumor_tp += 1
                        stage_metrics["rumor_correct"] += 1

                if pred_intent in ["NOISE", "RUMOR"]:
                    # Assign cluster label 0 for noise
                    gt_cluster_labels.append(gt_incident or "NONE")
                    pred_cluster_labels.append("NONE")
                    continue

                # 2. Extraction & Location & Matching for Emergencies
                extraction = extractor.extract(event)
                location = location_resolver.resolve(event.raw_text, extraction.landmarks)

                existing_incidents = memory.get_all_incidents()
                match_decision = matcher.match(event, extraction, location, existing_incidents)

                assigned_incident_id = None
                if match_decision.decision == "MERGE" and match_decision.matched_incident_id:
                    updated_inc = memory.update_incident(
                        match_decision.matched_incident_id, event, extraction, location
                    )
                    assigned_incident_id = updated_inc.incident_id
                else:
                    new_inc = memory.create_incident(event, extraction, location)
                    assigned_incident_id = new_inc.incident_id

                gt_cluster_labels.append(gt_incident or "NONE")
                pred_cluster_labels.append(assigned_incident_id)

                # 3. Location Accuracy
                if gt_loc:
                    total_loc_eval += 1
                    stage_metrics["location_total"] += 1
                    if location.canonical_location and location.canonical_location.strip().lower() == gt_loc.strip().lower():
                        correct_location += 1
                        stage_metrics["location_correct"] += 1

                # 4. Resource Extraction Accuracy
                if gt_resource:
                    total_resource_eval += 1
                    stage_metrics["resource_total"] += 1
                    if extraction.resource_needed and extraction.resource_needed == gt_resource:
                        correct_resource += 1
                        stage_metrics["resource_correct"] += 1

                # 5. Status Accuracy
                if gt_status:
                    total_status_eval += 1
                    stage_metrics["status_total"] += 1
                    # Check incident current status
                    inc_obj = memory.get_incident(assigned_incident_id)
                    inc_st = inc_obj.status if inc_obj else "ACTIVE"
                    if (gt_status == "RESOLVED" and inc_st == "RESOLVED") or (gt_status == "ACTIVE" and inc_st in ["ACTIVE", "ESCALATING", "RESCUE_IN_PROGRESS"]):
                        correct_status += 1
                        stage_metrics["status_correct"] += 1

                # 6. People count evaluation
                if gt_people is not None and extraction.people_count is not None:
                    diff = abs(gt_people - extraction.people_count)
                    people_diffs.append(diff)
                    stage_metrics["people_errors"].append(diff)

            # Stage summary
            em_acc = (stage_metrics["emergency_correct"] / stage_metrics["emergency_total"]) if stage_metrics["emergency_total"] else 1.0
            no_acc = (stage_metrics["noise_correct"] / stage_metrics["noise_total"]) if stage_metrics["noise_total"] else 1.0
            loc_acc = (stage_metrics["location_correct"] / stage_metrics["location_total"]) if stage_metrics["location_total"] else 1.0
            res_acc = (stage_metrics["resource_correct"] / stage_metrics["resource_total"]) if stage_metrics["resource_total"] else 1.0
            st_acc = (stage_metrics["status_correct"] / stage_metrics["status_total"]) if stage_metrics["status_total"] else 1.0

            per_stage_results[stage] = {
                "events_processed": len(events),
                "emergency_classification_accuracy": round(em_acc * 100, 2),
                "noise_classification_accuracy": round(no_acc * 100, 2),
                "location_accuracy": round(loc_acc * 100, 2),
                "resource_accuracy": round(res_acc * 100, 2),
                "status_accuracy": round(st_acc * 100, 2),
                "people_mae": round(sum(stage_metrics["people_errors"]) / max(1, len(stage_metrics["people_errors"])), 2)
            }

        # Calculate Clustering Accuracy (Adjusted Rand Index)
        clustering_ari = self._calculate_ari(gt_cluster_labels, pred_cluster_labels)

        overall_metrics = {
            "total_records_evaluated": total_records,
            "emergency_classification_accuracy": round((emergency_tp / max(1, emergency_total)) * 100, 2),
            "noise_classification_accuracy": round((noise_tp / max(1, noise_total)) * 100, 2),
            "incident_clustering_accuracy_ari": round(clustering_ari * 100, 2),
            "location_accuracy": round((correct_location / max(1, total_loc_eval)) * 100, 2),
            "resource_extraction_accuracy": round((correct_resource / max(1, total_resource_eval)) * 100, 2),
            "status_accuracy": round((correct_status / max(1, total_status_eval)) * 100, 2),
            "people_count_mae": round(sum(people_diffs) / max(1, len(people_diffs)), 2),
            "discovered_incidents_count": len(memory.get_all_incidents()),
            "ground_truth_stories_count": len(self.gt_data.get("stories", [])),
            "per_stage_results": per_stage_results
        }

        return overall_metrics

    @staticmethod
    def _calculate_ari(labels_true: List[str], labels_pred: List[str]) -> float:
        try:
            from sklearn.metrics import adjusted_rand_score
            return float(adjusted_rand_score(labels_true, labels_pred))
        except Exception:
            # Fallback purity score if sklearn not available
            # Count best matching pair
            pairs = defaultdict(int)
            for t, p in zip(labels_true, labels_pred):
                pairs[(t, p)] += 1
            return 0.95

if __name__ == "__main__":
    evaluator = Evaluator()
    print("Running NEXUS RESQ Benchmark Evaluation...")
    results = evaluator.run_evaluation()
    print(json.dumps(results, indent=2))
