import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.schemas.events import UnifiedEvent
from app.services.transcription.speech_provider import get_speech_provider
from app.core.config import get_dataset_dir

logger = logging.getLogger(__name__)

class DatasetDiscovery:
    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_dir = Path(dataset_path) if dataset_path else get_dataset_dir()
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        manifest_file = self.dataset_dir / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading manifest.json: {e}")
        return {}

    def discover_stages(self) -> List[str]:
        stages = []
        if self.manifest and "stages" in self.manifest:
            val = self.manifest["stages"]
            if isinstance(val, dict):
                stages = list(val.keys())
            # If val is an int (count), skip — we'll discover from filesystem below

        # Always check directory system for stage folders
        if self.dataset_dir.exists():
            dir_stages = sorted([
                d.name for d in self.dataset_dir.iterdir()
                if d.is_dir() and d.name.startswith("stage_")
            ])
            for ds in dir_stages:
                if ds not in stages:
                    stages.append(ds)

        stages.sort(key=lambda x: int(x.split("_")[1]) if "_" in x and x.split("_")[1].isdigit() else 999)
        return stages

    def ingest_stage(self, stage_name: str, transcribe_audio: bool = True) -> List[UnifiedEvent]:
        stage_dir = self.dataset_dir / stage_name
        if not stage_dir.exists():
            logger.warning(f"Stage directory does not exist: {stage_dir}")
            return []

        events: List[UnifiedEvent] = []
        stage_num = int(stage_name.split("_")[1]) if "_" in stage_name and stage_name.split("_")[1].isdigit() else 1

        # 1. Inspect social_and_sms directory
        social_dir = stage_dir / "social_and_sms"
        if social_dir.exists():
            for file_path in sorted(social_dir.iterdir()):
                if file_path.suffix.lower() == ".csv":
                    events.extend(self._parse_csv_file(file_path, stage_name, stage_num))
                elif file_path.suffix.lower() == ".json":
                    events.extend(self._parse_json_file(file_path, stage_name, stage_num))

        # 2. Inspect audio_calls directory
        audio_dir = stage_dir / "audio_calls"
        if audio_dir.exists():
            audio_files = sorted([
                f for f in audio_dir.iterdir()
                if f.suffix.lower() in [".mp3", ".wav", ".m4a", ".ogg"]
            ])
            speech_provider = get_speech_provider() if transcribe_audio else None

            for a_file in audio_files:
                audio_event = self._parse_audio_file(a_file, stage_name, stage_num, speech_provider)
                if audio_event:
                    events.append(audio_event)

        # Sort events by timestamp
        def get_ts(evt: UnifiedEvent):
            try:
                return evt.timestamp
            except Exception:
                return ""

        events.sort(key=get_ts)
        logger.info(f"Ingested {len(events)} events for {stage_name}")
        return events

    def _parse_csv_file(self, file_path: Path, stage_name: str, stage_num: int) -> List[UnifiedEvent]:
        events = []
        filename_lower = file_path.name.lower()
        source_type = "sms" if "sms" in filename_lower else ("twitter" if "twit" in filename_lower else "csv")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Detect ID column
                    rec_id = row.get("sms_id") or row.get("tweet_id") or row.get("id") or row.get("record_id")
                    if not rec_id:
                        rec_id = f"{stage_name}_{source_type}_{len(events)+1}"

                    # Detect text column
                    text = row.get("message") or row.get("text") or row.get("content") or ""

                    # Detect timestamp
                    ts = row.get("timestamp") or "2026-10-07T08:00:00"

                    # Detect sender
                    sender = row.get("sender") or row.get("username") or row.get("user") or "unknown"

                    evt = UnifiedEvent(
                        event_id=f"evt_{rec_id}",
                        source=source_type,
                        source_id=rec_id,
                        timestamp=ts,
                        raw_text=text,
                        language="en",
                        sender=sender,
                        audio_path=None,
                        stage_number=stage_num,
                        stage_name=stage_name,
                        metadata={"filename": file_path.name, "raw_row": row}
                    )
                    events.append(evt)
        except Exception as e:
            logger.error(f"Failed to parse CSV file {file_path}: {e}")

        return events

    def _parse_json_file(self, file_path: Path, stage_name: str, stage_num: int) -> List[UnifiedEvent]:
        events = []
        source_type = "whatsapp" if "whatsapp" in file_path.name.lower() else "json"

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)

            messages = data.get("messages", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for row in messages:
                rec_id = row.get("message_id") or row.get("id") or row.get("record_id") or f"{stage_name}_wa_{len(events)+1}"
                text = row.get("text") or row.get("message") or row.get("content") or ""
                ts = row.get("timestamp") or "2026-10-07T08:00:00"
                sender = row.get("sender") or "resident"

                evt = UnifiedEvent(
                    event_id=f"evt_{rec_id}",
                    source=source_type,
                    source_id=rec_id,
                    timestamp=ts,
                    raw_text=text,
                    language="en",
                    sender=sender,
                    audio_path=None,
                    stage_number=stage_num,
                    stage_name=stage_name,
                    metadata={"filename": file_path.name, "raw_row": row}
                )
                events.append(evt)
        except Exception as e:
            logger.error(f"Failed to parse JSON file {file_path}: {e}")

        return events

    def _parse_audio_file(
        self,
        file_path: Path,
        stage_name: str,
        stage_num: int,
        speech_provider: Optional[Any]
    ) -> Optional[UnifiedEvent]:
        rec_id = file_path.stem
        # Generate transcription
        transcript = ""
        language = "te"
        confidence = 0.5

        if speech_provider:
            trans_result = speech_provider.transcribe(str(file_path))
            transcript = trans_result.transcript
            language = trans_result.language
            confidence = trans_result.confidence

        # Fallback text if transcription is empty or in progress
        raw_text = transcript if transcript else f"[Audio Call {file_path.name}]"

        return UnifiedEvent(
            event_id=f"evt_{rec_id}",
            source="audio",
            source_id=file_path.name,
            timestamp="2026-10-07T08:00:00",
            raw_text=raw_text,
            language=language,
            sender="CALLER",
            audio_path=str(file_path.resolve()),
            stage_number=stage_num,
            stage_name=stage_name,
            metadata={
                "audio_filename": file_path.name,
                "file_size": file_path.stat().st_size,
                "transcription_confidence": confidence
            }
        )
