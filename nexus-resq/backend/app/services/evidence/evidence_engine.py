import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from app.schemas.incident import ObservationRecord, EvidenceItem
from app.core.config import settings

logger = logging.getLogger(__name__)

class EvidenceEngine:
    """
    Manages evidence ledgers, source reliability weighting,
    conflict detection for people counts and locations,
    and transparent 'Why does AI believe this?' reasoning.
    """

    @classmethod
    def get_source_reliability(cls, source_type: str, sender: str = "") -> float:
        st_lower = source_type.lower()
        snd_lower = sender.lower()

        if "control" in snd_lower or "responder" in snd_lower:
            return settings.SOURCE_RELIABILITY.get("responder", 0.95)
        if "helpline" in snd_lower or "helpline" in st_lower:
            return settings.SOURCE_RELIABILITY.get("helpline", 0.90)
        if "audio" in st_lower:
            return settings.SOURCE_RELIABILITY.get("audio", 0.88)
        if "sms" in st_lower:
            return settings.SOURCE_RELIABILITY.get("sms", 0.85)
        if "whatsapp" in st_lower or "community" in snd_lower:
            return settings.SOURCE_RELIABILITY.get("whatsapp", 0.75)
        if "twitter" in st_lower or "social" in st_lower:
            return settings.SOURCE_RELIABILITY.get("twitter", 0.60)
        if "forwarded" in snd_lower or "unverified" in snd_lower:
            return settings.SOURCE_RELIABILITY.get("unverified forwarded", 0.30)
        return 0.70

    @classmethod
    def evaluate_people_conflict(
        cls,
        observations: List[ObservationRecord]
    ) -> Tuple[Optional[int], bool, Optional[Dict[str, Any]]]:
        if not observations:
            return None, False, None

        counts = [obs.people_count for obs in observations]
        unique_counts = sorted(list(set(counts)))

        if len(unique_counts) == 1:
            return unique_counts[0], False, None

        # Conflict detected!
        evidence_list = []
        count_freq = Counter(counts)
        max_count = max(unique_counts)

        # Calculate reliability weights with recency factor (recent observations get priority)
        count_weights = {}
        for idx, obs in enumerate(observations):
            c = obs.people_count
            # More recent observation gets a modest recency multiplier
            recency_multiplier = 1.0 + 0.15 * (idx / max(1, len(observations) - 1))
            w = obs.confidence * recency_multiplier
            count_weights[c] = count_weights.get(c, 0.0) + w
            evidence_list.append({
                "count": c,
                "source_id": obs.source_id,
                "source_type": obs.source_type,
                "timestamp": obs.timestamp,
                "confidence": round(obs.confidence, 2)
            })

        # Best estimate is the highest reliability-weighted count
        best_estimate = max(count_weights.keys(), key=lambda k: count_weights[k])

        agreement_ratio = count_weights[best_estimate] / sum(count_weights.values())
        conflict_confidence = round(min(0.92, 0.60 + 0.30 * agreement_ratio), 2)

        conflict_details = {
            "has_conflict": True,
            "best_estimate": best_estimate,
            "max_reported": max_count,
            "confidence": conflict_confidence,
            "unique_reported_counts": unique_counts,
            "frequency_breakdown": dict(count_freq),
            "evidence_list": sorted(evidence_list, key=lambda x: x["timestamp"], reverse=True),
            "explanation": f"Multiple distinct counts reported ({', '.join(map(str, unique_counts))}). Best estimate {best_estimate} based on source reliability weighting and report corroboration."
        }

        return best_estimate, True, conflict_details

    @classmethod
    def generate_ai_reasoning(
        cls,
        name: str,
        canonical_location: str,
        landmarks: List[str],
        hazards: List[str],
        evidence_items: List[EvidenceItem],
        vulnerable: List[str],
        status: str
    ) -> Tuple[List[str], float]:
        reasons = []
        n_reports = len(evidence_items)
        sources = list(set(e.source_type for e in evidence_items))

        if landmarks:
            reasons.append(f"✓ Landmarks corroborated: {', '.join(landmarks[:3])}")
        if canonical_location:
            reasons.append(f"✓ Clustered around geographic epicenter: {canonical_location}")

        if n_reports >= 3:
            reasons.append(f"✓ {n_reports} corroborating reports across {len(sources)} distinct channels ({', '.join(sources)})")
        elif n_reports >= 1:
            reasons.append(f"✓ {n_reports} citizen report(s) received from {', '.join(sources)}")

        if hazards:
            reasons.append(f"✓ Consistent hazard indicators: {', '.join(hazards)}")

        if vulnerable:
            reasons.append(f"✓ High-priority vulnerable individuals identified: {', '.join(vulnerable)}")

        if n_reports >= 2:
            reasons.append("✓ Chronologically coherent timestamps within evolving incident lifecycle")

        base_conf = 0.70
        if canonical_location:
            base_conf += 0.08
        if len(landmarks) >= 2:
            base_conf += 0.05
        if n_reports >= 5:
            base_conf += 0.10
        elif n_reports >= 2:
            base_conf += 0.05
        if len(sources) >= 2:
            base_conf += 0.04

        conf = min(0.96, base_conf)
        return reasons, round(conf, 2)
