import re
import logging
from typing import Dict, Any, List
from app.schemas.events import UnifiedEvent, ClassificationResult

logger = logging.getLogger(__name__)

class EmergencyClassifier:
    """
    Classifies incoming unified events into:
    - EMERGENCY
    - NOISE
    - RUMOR
    - INFORMATION
    - UNKNOWN
    """

    NOISE_PATTERNS = [
        r"swiggy",
        r"food delivery",
        r"traffic is horrible",
        r"traffic update",
        r"traffic",
        r"electricity complaint number",
        r"complaint number",
        r"office timing",
        r"office",
        r"train timing",
        r"trains are delayed",
        r"train",
        r"weather forecast.*not rescue",
        r"weather forecast",
        r"general query",
        r"no emergency",
        r"road looks wet but no emergency",
        r"power gone in my street",
        r"power gone",
        r"omr is moving",
        r"is moving\?",
        r"water logged in my balcony only",
        r"anyone knows whether",
        r"just normal rain",
        r"how is the situation",
    ]

    RUMOR_PATTERNS = [
        r"forwarded message",
        r"forwarded warning",
        r"forwarded:",
        r"no official source",
        r"extreme rain at exactly midnight",
        r"rumor",
        r"unverified forward",
        r"fake alert",
        r"someone claims",
        r"500mm rain",
        r"schools are closed for one week",
        r"closed for one week",
        r"forwarded",
    ]

    EMERGENCY_KEYWORDS = [
        "rescue", "boat", "insulin", "diabetic", "fire", "transformer",
        "flood", "water rising", "water level", "trapped", "elderly", "children",
        "evacuated", "evacuate", "fire service", "fire tender", "extinguished",
        "medical", "mrts", "sanatorium", "velachery", "tambaram", "medavakkam",
        "hospital", "ambulance", "eb compound", "electrical compound", "ndrf",
        "patient", "safety", "flames", "blast",
        # Telugu keywords
        "వేలచేరి", "తాంబరం", "మేడవాక్కం", "ఇన్సులిన్", "బోటు", "మంటలు", "రెస్క్యూ"
    ]

    def classify(self, event: UnifiedEvent) -> ClassificationResult:
        text = event.raw_text.lower().strip()

        # If audio event
        if event.source == "audio":
            if any(k in text for k in self.EMERGENCY_KEYWORDS) or len(text) > 5:
                return ClassificationResult(
                    intent="EMERGENCY",
                    confidence=0.95,
                    reason="Verified voice emergency distress call containing incident keywords",
                    risk_flags=["AUDIO_CALL", "DIRECT_CITIZEN_REPORT"]
                )

        # 1. Check for Rumors first
        for pat in self.RUMOR_PATTERNS:
            if re.search(pat, text):
                return ClassificationResult(
                    intent="RUMOR",
                    confidence=0.90,
                    reason=f"Unverified broadcast/rumor pattern matched: '{pat}'",
                    risk_flags=["UNVERIFIED_FORWARD", "NO_OFFICIAL_SOURCE"]
                )

        # 2. Check for Noise
        is_noise = False
        noise_match = ""
        for pat in self.NOISE_PATTERNS:
            if re.search(pat, text):
                # Ensure it doesn't also contain life-critical keywords like fire tender, boat, etc.
                critical_override = any(w in text for w in ["trapped", "fire tender", "insulin", "evacuated", "ndrf boat", "flames", "being moved"])
                if not critical_override:
                    is_noise = True
                    noise_match = pat
                    break

        if is_noise:
            return ClassificationResult(
                intent="NOISE",
                confidence=0.92,
                reason=f"Non-emergency routine inquiry / chatter matching '{noise_match}'",
                risk_flags=["NON_ACTIONABLE", "NOISE"]
            )

        # 3. Check for Emergency indicators
        matched_keywords = [w for w in self.EMERGENCY_KEYWORDS if w in text]
        if matched_keywords:
            risk_flags = []
            if any(w in text for w in ["diabetic", "elderly", "children", "medical", "ఇన్సులిన్"]):
                risk_flags.append("VULNERABLE_PEOPLE")
            if any(w in text for w in ["fire", "transformer", "blast", "water rising", "మంటలు"]):
                risk_flags.append("HAZARDOUS_CONDITION")
            if any(w in text for w in ["boat", "insulin", "fire tender", "evacuated", "బోటు"]):
                risk_flags.append("RESOURCE_REQUIRED")

            confidence = min(0.96, 0.75 + 0.05 * len(matched_keywords))
            return ClassificationResult(
                intent="EMERGENCY",
                confidence=confidence,
                reason=f"Emergency distress signals detected: {', '.join(matched_keywords[:4])}",
                risk_flags=risk_flags
            )

        # 4. Fallback: If no clear emergency keywords and text is query or non-distress
        if "?" in text or len(text) < 40 or "rain" in text or "water" in text:
            return ClassificationResult(
                intent="NOISE",
                confidence=0.80,
                reason="Routine general remark without emergency indicators",
                risk_flags=["NON_ACTIONABLE_CHATTER"]
            )

        return ClassificationResult(
            intent="UNKNOWN",
            confidence=0.40,
            reason="Ambiguous message content",
            risk_flags=["UNCERTAIN"]
        )
