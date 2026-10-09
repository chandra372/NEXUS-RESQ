import math
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.schemas.events import UnifiedEvent, ExtractionResult, LocationResolutionResult, MatchDecision
from app.schemas.incident import IncidentSummary, IncidentDetail
from app.core.config import settings

logger = logging.getLogger(__name__)

class IncidentMatcher:
    """
    Computes a multi-factor incident match score:
    - semantic_similarity: 30%
    - location_similarity: 25%
    - landmark_similarity: 15%
    - time_similarity:     10%
    - hazard_similarity:   10%
    - resource_similarity:  5%
    - entity_similarity:    5%
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or settings.MATCH_WEIGHTS
        self.merge_threshold = settings.MERGE_THRESHOLD
        self.uncertain_threshold = settings.UNCERTAIN_THRESHOLD

    def match(
        self,
        event: UnifiedEvent,
        extraction: ExtractionResult,
        location: LocationResolutionResult,
        existing_incidents: List[IncidentDetail]
    ) -> MatchDecision:
        if not existing_incidents:
            return MatchDecision(
                decision="CREATE_NEW",
                matched_incident_id=None,
                score=0.0,
                reasons=["No existing active incidents to match with"]
            )

        best_score = -1.0
        best_incident_id = None
        best_reasons = []
        best_component_scores = {}

        for incident in existing_incidents:
            score, reasons, comp_scores = self._calculate_match_score(
                event, extraction, location, incident
            )
            if score > best_score:
                best_score = score
                best_incident_id = incident.incident_id
                best_reasons = reasons
                best_component_scores = comp_scores

        # Formulate Decision
        if best_score >= self.merge_threshold:
            decision = "MERGE"
        elif best_score >= self.uncertain_threshold:
            decision = "UNCERTAIN"
        else:
            decision = "CREATE_NEW"

        return MatchDecision(
            decision=decision,
            matched_incident_id=best_incident_id if decision in ["MERGE", "UNCERTAIN"] else None,
            score=round(best_score, 4),
            reasons=best_reasons,
            component_scores=best_component_scores
        )

    def _calculate_match_score(
        self,
        event: UnifiedEvent,
        extraction: ExtractionResult,
        location: LocationResolutionResult,
        incident: IncidentDetail
    ) -> Tuple[float, List[str], Dict[str, float]]:
        reasons = []
        comp_scores = {}
        raw_lower = event.raw_text.lower()

        is_relative_location = any(k in raw_lower for k in [
            "same location", "same place", "same incident", "same area", "at the location"
        ])

        # 1. Semantic Similarity (30%)
        incoming_tokens = set(raw_lower.split())
        incident_tokens = set((incident.name + " " + incident.canonical_location).lower().split())
        for e in incident.evidence[:8]:
            incident_tokens.update(e.raw_text.lower().split())

        intersection = incoming_tokens.intersection(incident_tokens)
        union = incoming_tokens.union(incident_tokens)
        sem_sim = len(intersection) / max(1, len(union)) if union else 0.0

        if extraction.incident_type and extraction.incident_type == incident.incident_type:
            sem_sim = min(1.0, sem_sim + 0.35)
        comp_scores["semantic_similarity"] = round(sem_sim, 3)

        # 2. Location Similarity (25%)
        loc_sim = 0.0
        if location.canonical_location and incident.canonical_location:
            if location.canonical_location.strip().lower() == incident.canonical_location.strip().lower():
                loc_sim = 1.0
                reasons.append(f"Canonical location matched: '{location.canonical_location}'")
            elif location.latitude and location.longitude and incident.latitude and incident.longitude:
                dist_km = self._haversine_distance(
                    location.latitude, location.longitude,
                    incident.latitude, incident.longitude
                )
                if dist_km < 1.0:
                    loc_sim = 0.95
                    reasons.append(f"Within 1km proximity ({dist_km:.2f}km)")
                elif dist_km < 3.0:
                    loc_sim = 0.60
                    reasons.append(f"Within 3km vicinity ({dist_km:.2f}km)")
                else:
                    loc_sim = 0.10
        elif is_relative_location:
            # Contextual relative reference
            if (extraction.people_count and incident.current_people == extraction.people_count) or \
               (extraction.resource_needed and extraction.resource_needed in incident.resources_needed) or \
               (extraction.incident_type and extraction.incident_type == incident.incident_type):
                loc_sim = 0.85
                reasons.append("Contextual reference to ongoing location confirmed by matching situation profile")
        comp_scores["location_similarity"] = round(loc_sim, 3)

        # 3. Landmark Similarity (15%)
        lm_sim = 0.0
        if location.landmarks and incident.landmarks:
            inc_lms_lower = [l.lower() for l in incident.landmarks]
            matched_lms = [l for l in location.landmarks if any(l.lower() in il or il in l.lower() for il in inc_lms_lower)]
            if matched_lms:
                lm_sim = min(1.0, len(matched_lms) / max(1, len(location.landmarks)) + 0.4)
                reasons.append(f"Landmarks corroborated: {', '.join(matched_lms[:3])}")
        elif loc_sim >= 0.85:
            lm_sim = 0.70
        comp_scores["landmark_similarity"] = round(lm_sim, 3)

        # 4. Time Similarity (10%)
        time_sim = 0.85
        try:
            t1 = datetime.fromisoformat(event.timestamp.replace("Z", ""))
            t2 = datetime.fromisoformat(incident.updated_at.replace("Z", ""))
            diff_hours = abs((t1 - t2).total_seconds()) / 3600.0
            if diff_hours <= 1.0:
                time_sim = 1.0
            elif diff_hours <= 3.0:
                time_sim = 0.85
            elif diff_hours <= 12.0:
                time_sim = 0.60
            else:
                time_sim = 0.30
        except Exception:
            pass
        comp_scores["time_similarity"] = round(time_sim, 3)

        # 5. Hazard Similarity (10%)
        haz_sim = 0.0
        if extraction.hazards and incident.hazards:
            common_haz = set(extraction.hazards).intersection(set(incident.hazards))
            if common_haz:
                haz_sim = 1.0
                reasons.append(f"Hazard verified: {', '.join(common_haz)}")
        elif not extraction.hazards:
            haz_sim = 0.5
        comp_scores["hazard_similarity"] = round(haz_sim, 3)

        # 6. Resource Similarity (5%)
        res_sim = 0.0
        if extraction.resource_needed and incident.resources_needed:
            if extraction.resource_needed in incident.resources_needed:
                res_sim = 1.0
                reasons.append(f"Matching resource requested: {extraction.resource_needed}")
            else:
                res_sim = 0.1
        elif not extraction.resource_needed:
            res_sim = 0.5
        comp_scores["resource_similarity"] = round(res_sim, 3)

        # 7. Context / Entity Similarity (5%)
        ent_sim = 0.0
        if extraction.people_count and incident.current_people:
            # People count matching or progressive update
            if extraction.people_count == incident.current_people or extraction.people_count == incident.max_reported_people:
                ent_sim += 0.5
                reasons.append(f"Matching casualty/evacuee count ({extraction.people_count})")
        if extraction.vulnerable_people and incident.vulnerable_people:
            common_vuln = set(extraction.vulnerable_people).intersection(set(incident.vulnerable_people))
            if common_vuln:
                ent_sim += 0.5
                reasons.append(f"Vulnerable population overlap: {', '.join(common_vuln)}")
        if extraction.incident_type and extraction.incident_type == incident.incident_type:
            ent_sim = min(1.0, ent_sim + 0.4)
        comp_scores["entity_similarity"] = round(min(1.0, ent_sim), 3)

        # Compute Total Weighted Score
        total_score = sum(self.weights.get(k, 0.0) * comp_scores[k] for k in comp_scores)

        # Strong correlation boost when multiple core anchors align
        if loc_sim >= 0.85 and (haz_sim >= 0.8 or res_sim >= 0.8 or sem_sim >= 0.35):
            total_score = max(total_score, 0.78)

        # Direct resource + hazard alignment boost (e.g. only one transformer fire or insulin rescue)
        if res_sim >= 0.9 and haz_sim >= 0.9:
            total_score = max(total_score, 0.75)

        return total_score, reasons, comp_scores

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c
