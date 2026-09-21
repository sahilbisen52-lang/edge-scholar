"""
Whisper ASR provider for local speech-to-text.
Supports openai-whisper and faster-whisper backends.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

from app.core.errors import TranscriptionError, ModelLoadError

logger = logging.getLogger("edge_scholar.ai.whisper")


class WhisperProvider:
    """
    Local Whisper ASR provider.
    
    Tries faster-whisper first (more efficient), falls back to openai-whisper.
    Both run fully locally with no cloud dependency.
    """

    SUPPORTED_MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]

    def __init__(self) -> None:
        self._model = None
        self._backend: str = "none"
        self._model_name: str = ""

    @staticmethod
    def is_faster_whisper_available() -> bool:
        try:
            import faster_whisper  # noqa
            return True
        except ImportError:
            return False

    @staticmethod
    def is_openai_whisper_available() -> bool:
        try:
            import whisper  # noqa
            return True
        except ImportError:
            return False

    @staticmethod
    def is_available() -> bool:
        return (
            WhisperProvider.is_faster_whisper_available()
            or WhisperProvider.is_openai_whisper_available()
        )

    def load_model(self, model_name: str = "base", device: str = "cpu", **kwargs: Any) -> None:
        self._model_name = model_name
        if self.is_faster_whisper_available():
            self._load_faster_whisper(model_name, device)
        elif self.is_openai_whisper_available():
            self._load_openai_whisper(model_name, device)
        else:
            raise ModelLoadError(
                "No Whisper backend installed",
                user_message="Install faster-whisper or openai-whisper for audio transcription.",
            )

    def _load_faster_whisper(self, model_name: str, device: str) -> None:
        from faster_whisper import WhisperModel
        logger.info("Loading faster-whisper model: %s on %s", model_name, device)
        try:
            self._model = WhisperModel(model_name, device=device, compute_type="int8")
            self._backend = "faster-whisper"
            logger.info("faster-whisper model loaded.")
        except Exception as e:
            raise ModelLoadError(str(e))

    def _load_openai_whisper(self, model_name: str, device: str) -> None:
        import whisper
        logger.info("Loading openai-whisper model: %s on %s", model_name, device)
        try:
            self._model = whisper.load_model(model_name, device=device)
            self._backend = "openai-whisper"
            logger.info("openai-whisper model loaded.")
        except Exception as e:
            raise ModelLoadError(str(e))

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio file. Returns dict with:
        - text: full transcript
        - segments: list of {start, end, text}
        - language: detected language
        - duration_seconds: transcription time
        """
        if self._model is None:
            raise TranscriptionError(
                "Whisper model not loaded",
                user_message="Load an ASR model before transcribing.",
            )
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        t0 = time.perf_counter()
        try:
            if self._backend == "faster-whisper":
                return self._transcribe_faster(audio_path, language)
            else:
                return self._transcribe_openai(audio_path, language)
        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(str(e), user_message=f"Transcription failed: {e}")

    def _transcribe_faster(self, audio_path: Path, language: Optional[str]) -> dict:
        t0 = time.perf_counter()
        segments_gen, info = self._model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            word_timestamps=False,
        )
        segments = []
        full_text = []
        for seg in segments_gen:
            segments.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
            full_text.append(seg.text.strip())

        elapsed = time.perf_counter() - t0
        return {
            "text": " ".join(full_text),
            "segments": segments,
            "language": info.language if hasattr(info, "language") else (language or "en"),
            "duration_seconds": elapsed,
            "backend": "faster-whisper",
        }

    def _transcribe_openai(self, audio_path: Path, language: Optional[str]) -> dict:
        import whisper
        t0 = time.perf_counter()
        kwargs: dict = {}
        if language:
            kwargs["language"] = language
        result = self._model.transcribe(str(audio_path), **kwargs)
        elapsed = time.perf_counter() - t0
        segments = [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in result.get("segments", [])
        ]
        return {
            "text": result.get("text", "").strip(),
            "segments": segments,
            "language": result.get("language", "en"),
            "duration_seconds": elapsed,
            "backend": "openai-whisper",
        }

    def is_loaded(self) -> bool:
        return self._model is not None

    def backend(self) -> str:
        return self._backend

    def model_name(self) -> str:
        return self._model_name
