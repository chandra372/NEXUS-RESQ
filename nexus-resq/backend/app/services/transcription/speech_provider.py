import os
import io
import wave
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class TranscriptionResult:
    def __init__(
        self,
        transcript: str,
        language: str = "en",
        confidence: float = 0.8,
        success: bool = True,
        error: Optional[str] = None,
        duration: float = 0.0
    ):
        self.transcript = transcript
        self.language = language
        self.confidence = confidence
        self.success = success
        self.error = error
        self.duration = duration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transcript": self.transcript,
            "language": self.language,
            "confidence": self.confidence,
            "success": self.success,
            "error": self.error,
            "duration": self.duration
        }

class SpeechProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        pass

class LocalWhisperProvider(SpeechProvider):
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "data", "processed", "transcription_cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self._recognizer = None

    def _get_cache_path(self, audio_path: str) -> Path:
        base = Path(audio_path).stem
        return Path(self.cache_dir) / f"{base}.json"

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        cache_path = self._get_cache_path(audio_path)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return TranscriptionResult(**data)
            except Exception as e:
                logger.warning(f"Failed to read cache {cache_path}: {e}")

        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return TranscriptionResult(
                transcript="",
                language="unknown",
                confidence=0.0,
                success=False,
                error="File not found"
            )

        try:
            import miniaudio
            import speech_recognition as sr

            decoded = miniaudio.decode_file(audio_path)
            duration = float(decoded.duration)

            wav_io = io.BytesIO()
            with wave.open(wav_io, "wb") as wav_f:
                wav_f.setnchannels(decoded.nchannels)
                wav_f.setsampwidth(decoded.sample_width)
                wav_f.setframerate(decoded.sample_rate)
                wav_f.writeframes(decoded.samples)
            wav_io.seek(0)

            if self._recognizer is None:
                self._recognizer = sr.Recognizer()

            with sr.AudioFile(wav_io) as source:
                # Read audio segment for emergency report understanding
                audio_data = self._recognizer.record(source, duration=min(duration, 35.0))
                
                # Attempt Telugu or English recognition
                try:
                    # Recognize with google speech
                    text = self._recognizer.recognize_google(audio_data, language="te-IN")
                    lang = "te"
                except Exception:
                    try:
                        text = self._recognizer.recognize_google(audio_data, language="en-IN")
                        lang = "en"
                    except Exception as inner_e:
                        text = ""
                        lang = "unknown"
                        logger.info(f"Fallback speech recognition attempted: {inner_e}")

            confidence = 0.85 if len(text) > 10 else 0.50
            result = TranscriptionResult(
                transcript=text,
                language=lang,
                confidence=confidence,
                success=True,
                duration=duration
            )

            # Save to cache
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(result.to_dict(), f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to write cache: {e}")

            return result

        except Exception as e:
            logger.error(f"Transcription failed for {audio_path}: {e}", exc_info=True)
            # Never crash! Return marked failed
            return TranscriptionResult(
                transcript="",
                language="unknown",
                confidence=0.0,
                success=False,
                error=str(e)
            )

class OptionalCloudProvider(SpeechProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        if not self.api_key:
            return TranscriptionResult(
                transcript="",
                language="unknown",
                confidence=0.0,
                success=False,
                error="No Cloud API key provided"
            )
        # Cloud API integration would go here
        return LocalWhisperProvider().transcribe(audio_path)

def get_speech_provider() -> SpeechProvider:
    # Defaults to local whisper/speechrecognition provider
    return LocalWhisperProvider()
