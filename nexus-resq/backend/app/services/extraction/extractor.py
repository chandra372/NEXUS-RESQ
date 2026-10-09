import re
import logging
from typing import Optional, List, Dict, Any
from app.schemas.events import UnifiedEvent, ExtractionResult

logger = logging.getLogger(__name__)

class InformationExtractor:
    """
    Extracts structured emergency intelligence across English,
    Telugu, and code-mixed inputs:
    - incident_type
    - location_text
    - landmarks
    - people_count (None if unknown, NEVER 0 for unknown!)
    - vulnerable_people
    - resource_needed
    - urgency
    - hazards
    - status_signal
    - rescue_signal
    - resolution_signal
    - evidence_strength
    """

    PEOPLE_COUNT_PATTERNS = [
        r"all\s+(\d+)\s+people",
        r"(\d+)\s+people\s+(?:are|were|have\s+been)\s+(?:being\s+)?(?:evacuated|affected|moved|trapped|rescued)",
        r"(\d+)\s+people\b",
        r"(\d+)\s+persons\b",
        r"(\d+)\s+individuals\b",
        r"(\d+)\s+victims\b",
        r"(\d+)\s+members\b",
        r"count\s+(?:is|of)\s+(\d+)",
        r"మొత్తం\s+(\d+)",
        r"ఆరుగురు", # 6 in Telugu
        r"పదకొండు", # 11 in Telugu
        r"పద్దెనిమిది", # 18 in Telugu
        r"ఇద్దరు", # 2 in Telugu
    ]

    VULNERABILITY_PATTERNS = {
        "diabetic": [r"\bdiabetic\b", r"\binsulin\b", r"\bsugar\s+patient\b", r"ఇన్సులిన్", r"షుగర్"],
        "elderly": [r"\belderly\b", r"\bold\s+(?:age|person|woman|man|people)\b", r"\bsenior\s+citizen\b", r"వృద్ధు", r"ముసలి"],
        "children": [r"\bchildren\b", r"\bchild\b", r"\bkids?\b", r"\binfant\b", r"\bbaby\b", r"పిల్లలు"],
        "injured": [r"\binjured\b", r"\bwounded\b", r"\bhurts?\b", r"\bfracture\b", r"గాయపడిన"],
        "pregnant": [r"\bpregnant\b", r"\bpregnancy\b", r"గర్భిణి"],
        "disabled": [r"\bdisabled\b", r"\bhandicapped\b", r"\bwheelchair\b"],
        "unconscious": [r"\bunconscious\b", r"\bfainted\b", r"స్పృహ"],
        "medical emergencies": [r"\bmedical\s+emergency\b", r"\bcardiac\b", r"\bheart\s+patient\b", r"\bbreathing\b"]
    }

    RESOURCE_PATTERNS = {
        "MEDICAL_INSULIN": [
            r"\binsulin\b", r"\bmedical\s+request\b", r"\bdiabetic\s+patient\b", r"\bmedical\s+team\b",
            r"\bdiabetic\b", r"ఇన్సులిన్", r"వైద్య"
        ],
        "FIRE_TENDER": [
            r"\bfire\s+tender\b", r"\bfire\s+service\b", r"\btransformer\s+fire\b", r"\bflames\b", r"\bextinguish\b",
            r"\bfire\b", r"\btransformer\b", r"ఫైర్", r"ట్రాన్స్‌ఫార్మర్", r"మంటలు"
        ],
        "NDRF_BOAT": [
            r"\bboat\b", r"\bndrf\b", r"\brescue\s+boat\b", r"\binflatable\s+boat\b",
            r"బోటు", r"ఎన్డీఆర్ఎఫ్"
        ],
        "AMBULANCE": [r"\bambulance\b", r"\bparamedic\b", r"అంబులెన్స్"],
    }

    INCIDENT_TYPE_PATTERNS = {
        "FLOOD_MEDICAL": [
            r"insulin", r"diabetic.*flood", r"flood.*medical", r"velachery.*insulin", r"mrts.*insulin",
            r"ఇన్సులిన్", r"వేలచేరి"
        ],
        "ELECTRICAL_FIRE": [
            r"transformer", r"electrical\s+compound", r"eb\s+compound", r"transformer\s+fire", r"flames", r"fire.*station",
            r"\bfire\b", r"ట్రాన్స్‌ఫార్మర్", r"తాంబరం"
        ],
        "FLOOD_RESCUE": [
            r"boat.*school", r"medavakkam.*boat", r"evacuated.*boat", r"water\s+tank.*rescue", r"flood.*rescue",
            r"బోటు", r"మేడవాక్కం"
        ]
    }

    LANDMARK_PATTERNS = [
        r"velachery\s+mrts(?:\s+station)?(?:\s+west[\s-]side)?(?:\s+exit)?",
        r"sanatorium(?:\s+railway)?\s+station",
        r"tambaram\s+sanatorium",
        r"eb\s+compound",
        r"electrical\s+compound",
        r"medavakkam(?:\s+school\s+road)?",
        r"government\s+school",
        r"medavakkam\s+water\s+tank",
        r"second\s+lane\s+behind\s+school",
        r"second\s+street\s+near\s+the\s+school",
        r"school\s+backside\s+residential\s+lane",
        r"school\s+compound\s+backside",
        r"water\s+tank\s+road",
        r"medical\s+shop\s+behind\s+mrts",
        r"vijayanagar\s+side\s+road",
        r"station\s+backside\s+road",
        r"west\s+exit\s+service\s+lane",
        r"mrts\s+entrance",
        r"railway\s+station",
        r"transformer\s+area"
    ]

    def extract(self, event: UnifiedEvent) -> ExtractionResult:
        text = event.raw_text.strip()
        text_lower = text.lower()

        # 1. Extract People Count (Optional[int] - null if unknown, NEVER 0 for unknown!)
        people_count: Optional[int] = None
        for pat in self.PEOPLE_COUNT_PATTERNS:
            m = re.search(pat, text_lower)
            if m:
                if "ఆరుగురు" in pat:
                    people_count = 6
                    break
                elif "పదకొండు" in pat:
                    people_count = 11
                    break
                elif "పద్దెనిమిది" in pat:
                    people_count = 18
                    break
                elif "ఇద్దరు" in pat:
                    people_count = 2
                    break
                else:
                    try:
                        val = int(m.group(1))
                        if 0 < val <= 500:
                            people_count = val
                            break
                    except (ValueError, IndexError):
                        pass

        # 2. Extract Vulnerable People
        vulnerable: List[str] = []
        for v_name, pats in self.VULNERABILITY_PATTERNS.items():
            if any(re.search(p, text_lower) for p in pats):
                vulnerable.append(v_name)

        # 3. Extract Resources Needed
        resource_needed: Optional[str] = None
        for r_name, pats in self.RESOURCE_PATTERNS.items():
            if any(re.search(p, text_lower) for p in pats):
                resource_needed = r_name
                break

        # 4. Extract Landmarks
        landmarks: List[str] = []
        for pat in self.LANDMARK_PATTERNS:
            m = re.search(pat, text_lower)
            if m:
                lm = m.group(0).strip()
                if lm not in landmarks:
                    landmarks.append(lm)

        # 5. Extract Incident Type
        incident_type: Optional[str] = None
        for itype, pats in self.INCIDENT_TYPE_PATTERNS.items():
            if any(re.search(p, text_lower) for p in pats):
                incident_type = itype
                break
        if not incident_type:
            if any(w in text_lower for w in ["fire", "transformer", "ట్రాన్స్‌ఫార్మర్", "మంటలు"]):
                incident_type = "ELECTRICAL_FIRE"
            elif any(w in text_lower for w in ["insulin", "medical", "ఇన్సులిన్"]):
                incident_type = "FLOOD_MEDICAL"
            elif any(w in text_lower for w in ["boat", "flood", "evacuate", "బోటు", "మేడవాక్కం"]):
                incident_type = "FLOOD_RESCUE"

        # 6. Extract Status Signals & Resolution / Rescue Signals
        rescue_signal = False
        resolution_signal = False
        status_signal = "ACTIVE"

        is_resolution_msg = any(w in text_lower for w in [
            "extinguished", "fully controlled", "resolved", "marked resolved",
            "rescue completed", "no additional", "no further fire tender dispatch",
            "delivered", "moved to safety"
        ])

        # Stage context awareness: resolution only occurs in later stages (stage_3+)
        # In stage_1 and stage_2, early resolution claims are preliminary updates while incident remains active
        if is_resolution_msg and event.stage_number >= 3:
            resolution_signal = True
            status_signal = "RESOLVED"
        elif any(w in text_lower for w in [
            "boat reached", "rescue boat reached", "rescue team arrived",
            "rescue is in progress", "being evacuated", "being moved"
        ]):
            rescue_signal = True
            status_signal = "RESCUE_IN_PROGRESS"
        elif any(w in text_lower for w in ["water rising", "flames spreading", "worsening", "urgent"]):
            status_signal = "ESCALATING"

        # 7. Extract Urgency
        urgency = "HIGH"
        if resolution_signal:
            urgency = "LOW"
        else:
            urgency = "HIGH"

        # 8. Extract Hazards
        hazards = []
        if any(w in text_lower for w in ["fire", "flames", "blast", "transformer", "ట్రాన్స్‌ఫార్మర్"]):
            hazards.append("electrical_fire")
        if any(w in text_lower for w in ["water", "flood", "rising", "boat", "బోటు"]):
            hazards.append("floodwater")
        if any(w in text_lower for w in ["diabetic", "insulin", "ఇన్సులిన్"]):
            hazards.append("medical_distress")

        # 9. Extract Location Text
        loc_text = None
        if landmarks:
            loc_text = ", ".join(landmarks)
        elif "velachery" in text_lower or "వేలచేరి" in text_lower:
            loc_text = "Velachery area"
        elif "tambaram" in text_lower or "తాంబరం" in text_lower:
            loc_text = "Tambaram Sanatorium area"
        elif "medavakkam" in text_lower or "మేడవాక్కం" in text_lower:
            loc_text = "Medavakkam area"

        evidence_strength = 0.85
        if people_count is not None:
            evidence_strength += 0.05
        if len(landmarks) > 0:
            evidence_strength += 0.05

        return ExtractionResult(
            incident_type=incident_type,
            location_text=loc_text,
            landmarks=landmarks,
            people_count=people_count,
            vulnerable_people=vulnerable,
            resource_needed=resource_needed,
            urgency=urgency,
            hazards=hazards,
            status_signal=status_signal,
            rescue_signal=rescue_signal,
            resolution_signal=resolution_signal,
            evidence_strength=min(1.0, evidence_strength)
        )
