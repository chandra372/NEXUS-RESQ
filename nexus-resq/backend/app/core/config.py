import os
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel, Field

# Load .env so DATASET_PATH and other vars are picked up by os.getenv
try:
    from dotenv import load_dotenv as _load_dotenv
    _env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if _env_file.exists():
        _load_dotenv(_env_file, override=False)
except ImportError:
    pass  # python-dotenv not installed; rely on shell env vars

class Settings(BaseModel):
    PROJECT_NAME: str = "NEXUS RESQ"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Dataset path resolution
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATASET_PATH: str = Field(
        default_factory=lambda: os.getenv(
            "DATASET_PATH",
            str(Path(__file__).resolve().parent.parent.parent.parent.parent / "large_emergency_dataset")
        )
    )
    
    # Matching Weights (from Hackathon Specification)
    MATCH_WEIGHTS: Dict[str, float] = {
        "semantic_similarity": 0.30,
        "location_similarity": 0.25,
        "landmark_similarity": 0.15,
        "time_similarity": 0.10,
        "hazard_similarity": 0.10,
        "resource_similarity": 0.05,
        "entity_similarity": 0.05
    }
    
    # Matching Thresholds
    MERGE_THRESHOLD: float = 0.62
    UNCERTAIN_THRESHOLD: float = 0.38
    
    # Source Reliability Defaults
    SOURCE_RELIABILITY: Dict[str, float] = {
        "responder": 0.95,
        "helpline": 0.90,
        "sms": 0.85,
        "audio": 0.88,
        "community": 0.75,
        "whatsapp": 0.75,
        "social media": 0.60,
        "twitter": 0.60,
        "unverified forwarded": 0.30
    }
    
    # Priority Levels
    PRIORITY_LEVELS: Dict[str, tuple] = {
        "LOW": (0, 30),
        "MEDIUM": (31, 60),
        "HIGH": (61, 80),
        "CRITICAL": (81, 100)
    }
    
    AI_PROVIDER_NAME: str = "Local/Fallback Rule & Embeddings Engine"
    SPEECH_PROVIDER_NAME: str = "Local STT (SpeechRecognition / Whisper Compatible)"

settings = Settings()

def get_dataset_dir() -> Path:
    candidates = [
        Path(settings.DATASET_PATH),
        Path("large_emergency_dataset"),
        Path("../large_emergency_dataset"),
        Path("../../large_emergency_dataset"),
        Path(__file__).resolve().parent.parent.parent.parent / "large_emergency_dataset",
        Path(__file__).resolve().parent.parent.parent.parent.parent / "large_emergency_dataset",
        # Legacy fallbacks
        Path("emergency_dataset"),
        Path("../emergency_dataset"),
        Path("../../emergency_dataset"),
        Path("data/raw"),
        Path("../data/raw"),
    ]
    for c in candidates:
        if c.exists() and ((c / "manifest.json").exists() or (c / "ground_truth.json").exists()):
            return c.resolve()
    # If not found, return first candidate as path
    return candidates[0].resolve()
