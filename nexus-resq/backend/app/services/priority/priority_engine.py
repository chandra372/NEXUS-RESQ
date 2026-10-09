import logging
from typing import Tuple, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class PriorityEngine:
    """
    Calculates a deterministic 0-100 numerical priority score based on:
    - people affected
    - vulnerable people
    - hazard severity
    - urgency
    - escalation
    - resource requirements
    - evidence confidence
    - recency
    """

    @classmethod
    def calculate_priority(
        cls,
        people_count: Optional[int],
        vulnerable_people: List[str],
        hazards: List[str],
        urgency: str,
        status: str,
        resources_needed: List[str],
        confidence: float = 0.85
    ) -> Tuple[int, str]:
        # If incident is RESOLVED, priority drops to LOW
        if status == "RESOLVED":
            return 15, "LOW"

        score = 0

        # 1. People Affected (max 25 points)
        if people_count is not None:
            if people_count > 15:
                score += 25
            elif people_count >= 10:
                score += 22
            elif people_count >= 5:
                score += 18
            elif people_count > 0:
                score += 12
        else:
            score += 10  # Default baseline when count is unconfirmed

        # 2. Vulnerable People (max 20 points, 6 points per vulnerability)
        vuln_score = min(20, len(vulnerable_people) * 7)
        score += vuln_score

        # 3. Hazard Severity (max 20 points)
        hazard_pts = 0
        if any("fire" in h or "transformer" in h for h in hazards):
            hazard_pts = max(hazard_pts, 20)
        if any("flood" in h or "rising" in h for h in hazards):
            hazard_pts = max(hazard_pts, 18)
        if any("medical" in h or "insulin" in h for h in hazards):
            hazard_pts = max(hazard_pts, 17)
        if hazard_pts == 0 and hazards:
            hazard_pts = 10
        score += hazard_pts

        # 4. Urgency (max 15 points)
        if urgency == "HIGH":
            score += 15
        elif urgency == "MEDIUM":
            score += 8
        else:
            score += 3

        # 5. Escalation / State Progress (max 10 points)
        if status == "ESCALATING":
            score += 10
        elif status == "ACTIVE":
            score += 5
        elif status == "RESCUE_IN_PROGRESS":
            score += 3

        # 6. Resource Requirements (max 5 points)
        if len(resources_needed) > 0:
            score += 5

        # 7. Evidence Confidence (max 5 points)
        if confidence >= 0.85:
            score += 5
        elif confidence >= 0.60:
            score += 3

        # Clamp between 0 and 100
        final_score = max(0, min(100, score))

        # Map to Level
        if final_score >= 81:
            level = "CRITICAL"
        elif final_score >= 61:
            level = "HIGH"
        elif final_score >= 31:
            level = "MEDIUM"
        else:
            level = "LOW"

        return final_score, level
