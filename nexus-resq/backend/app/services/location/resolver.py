import re
import logging
from typing import Optional, List, Dict, Any
from app.schemas.events import LocationResolutionResult

logger = logging.getLogger(__name__)

class LocationResolver:
    """
    Resolves diverse landmark descriptions, relative directions,
    and multi-lingual (English, Telugu, Tamil phonetics) cues
    into canonical locations with geo-coordinates and precision metrics.
    """

    KNOWN_CLUSTERS = [
        {
            "zone": "Velachery",
            "canonical_location": "Velachery MRTS west-side approach",
            "latitude": 12.9784,
            "longitude": 80.2185,
            "primary_keywords": [
                "velachery", "mrts", "వేలచేరి", "వేల చేరి", "ఎమ్మార్పీఎస్", "ఎంఆర్టిఎస్", "mrts"
            ],
            "landmark_patterns": [
                r"velachery\s+mrts\s+west[\s-]side",
                r"behind\s+velachery\s+mrts",
                r"west\s+gate\s+of\s+velachery\s+station",
                r"vijayanagar\s+side\s+road",
                r"behind\s+the\s+railway\s+station",
                r"mrts\s+entrance",
                r"station\s+backside\s+road",
                r"medical\s+shop\s+behind\s+mrts",
                r"west\s+exit\s+service\s+lane",
                r"velachery",
                r"mrts",
                r"వేలచేరి",
                r"వేల\s+చేరి",
                r"వెలచేరి",
                r"ఎమ్మార్పీఎస్",
                r"ఎంఆర్టిఎస్"
            ]
        },
        {
            "zone": "Tambaram Sanatorium",
            "canonical_location": "Tambaram Sanatorium railway station electrical compound approach",
            "latitude": 12.9304,
            "longitude": 80.1235,
            "primary_keywords": [
                "tambaram", "sanatorium", "eb compound", "transformer",
                "తాంబరం", "సానిటోరియం", "ట్రాన్స్‌ఫార్మర్", "ఈబీ"
            ],
            "landmark_patterns": [
                r"tambaram\s+sanatorium\s+station\s+side",
                r"behind\s+sanatorium\s+railway\s+station",
                r"station\s+approach\s+road",
                r"electrical\s+compound(?:\s+near\s+the\s+station)?",
                r"transformer\s+area",
                r"sanatorium\s+station\s+backside",
                r"near\s+the\s+eb\s+compound",
                r"eb\s+compound",
                r"road\s+behind\s+the\s+railway\s+station",
                r"station\s+electrical[\s-]side\s+road",
                r"sanatorium",
                r"tambaram",
                r"తాంబరం",
                r"సానిటోరియం",
                r"ట్రాన్స్‌ఫార్మర్"
            ]
        },
        {
            "zone": "Medavakkam",
            "canonical_location": "Medavakkam school-road residential lane",
            "latitude": 12.9189,
            "longitude": 80.1873,
            "primary_keywords": [
                "medavakkam", "school road", "water tank",
                "మేడవాక్కం", "వాటర్ ట్యాంక్", "స్కూల్"
            ],
            "landmark_patterns": [
                r"medavakkam\s+school\s+road",
                r"behind\s+the\s+government\s+school",
                r"government\s+school",
                r"near\s+the\s+medavakkam\s+water\s+tank",
                r"medavakkam\s+water\s+tank",
                r"second\s+lane\s+behind\s+school",
                r"school\s+backside\s+residential\s+lane",
                r"water\s+tank\s+road",
                r"medavakkam\s+inner\s+residential\s+road",
                r"school\s+compound\s+backside",
                r"second\s+street\s+near\s+the\s+school",
                r"medavakkam",
                r"మేడవాక్కం",
                r"వాటర్\s+ట్యాంక్"
            ]
        }
    ]

    def resolve(self, text: str, landmarks: Optional[List[str]] = None) -> LocationResolutionResult:
        if not text:
            return LocationResolutionResult(
                canonical_location=None,
                latitude=None,
                longitude=None,
                landmarks=[],
                location_precision="unknown",
                confidence=0.0,
                evidence="No location mentions in text"
            )

        text_lower = text.lower()
        extracted_landmarks = list(landmarks) if landmarks else []

        best_cluster = None
        best_score = 0
        matched_patterns = []

        for cluster in self.KNOWN_CLUSTERS:
            score = 0
            matches = []

            for kw in cluster["primary_keywords"]:
                if kw in text_lower:
                    score += 2
                    matches.append(kw)

            for pat in cluster["landmark_patterns"]:
                if re.search(pat, text_lower):
                    score += 3
                    matches.append(pat)

            if score > best_score:
                best_score = score
                best_cluster = cluster
                matched_patterns = list(set(matches))

        if best_cluster and best_score >= 2:
            if best_score >= 5 or any("approach" in p or "gate" in p or "behind" in p or "second" in p or "compound" in p for p in matched_patterns):
                precision = "landmark"
                confidence = min(0.95, 0.75 + (best_score * 0.03))
            else:
                precision = "area"
                confidence = 0.75

            evidence_str = f"Corroborated by cues: {', '.join(matched_patterns[:4])}"
            all_lms = list(set(extracted_landmarks + [m for m in matched_patterns if len(m) > 4]))

            return LocationResolutionResult(
                canonical_location=best_cluster["canonical_location"],
                latitude=best_cluster["latitude"],
                longitude=best_cluster["longitude"],
                landmarks=all_lms,
                location_precision=precision,
                confidence=confidence,
                evidence=evidence_str
            )

        # Contextual check for relative references: "same location", "same Medavakkam incident", etc.
        if "medavakkam" in text_lower:
            cl = self.KNOWN_CLUSTERS[2]
            return LocationResolutionResult(
                canonical_location=cl["canonical_location"],
                latitude=cl["latitude"],
                longitude=cl["longitude"],
                landmarks=extracted_landmarks + ["Medavakkam"],
                location_precision="area",
                confidence=0.80,
                evidence="Identified via zone name mention 'Medavakkam'"
            )
        if "velachery" in text_lower:
            cl = self.KNOWN_CLUSTERS[0]
            return LocationResolutionResult(
                canonical_location=cl["canonical_location"],
                latitude=cl["latitude"],
                longitude=cl["longitude"],
                landmarks=extracted_landmarks + ["Velachery"],
                location_precision="area",
                confidence=0.80,
                evidence="Identified via zone name mention 'Velachery'"
            )
        if "tambaram" in text_lower or "sanatorium" in text_lower:
            cl = self.KNOWN_CLUSTERS[1]
            return LocationResolutionResult(
                canonical_location=cl["canonical_location"],
                latitude=cl["latitude"],
                longitude=cl["longitude"],
                landmarks=extracted_landmarks + ["Tambaram Sanatorium"],
                location_precision="area",
                confidence=0.80,
                evidence="Identified via zone name mention 'Tambaram'"
            )

        # Fallback city level
        if "chennai" in text_lower:
            return LocationResolutionResult(
                canonical_location="Greater Chennai Metropolitan Area",
                latitude=13.0827,
                longitude=80.2707,
                landmarks=extracted_landmarks,
                location_precision="approximate",
                confidence=0.40,
                evidence="Generic city-level mention"
            )

        return LocationResolutionResult(
            canonical_location=None,
            latitude=None,
            longitude=None,
            landmarks=extracted_landmarks,
            location_precision="unknown",
            confidence=0.0,
            evidence="Location unresolved"
        )
