"""Audio transcription pipeline."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.ai.whisper_provider import WhisperProvider
from app.rag.prompt_templates import lecture_summary_prompt
from app.ai.base_provider import AIProvider
from app.core.errors import TranscriptionError, ModelNotLoadedError

logger = logging.getLogger("edge_scholar.audio")


class TranscriptionService:
    def __init__(
        self,
        whisper: WhisperProvider,
        llm_provider: Optional[AIProvider] = None,
    ) -> None:
        self.whisper = whisper
        self.llm = llm_provider

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> dict:
        if not self.whisper.is_loaded():
            raise TranscriptionError(
                "Whisper not loaded",
                user_message="Load the Whisper ASR model before transcribing.",
            )
        result = self.whisper.transcribe(audio_path, language=language)
        return result

    def summarize_lecture(self, transcript: str) -> str:
        if not self.llm:
            return "⚠️ No LLM provider configured for summarization."
        prompt = lecture_summary_prompt(transcript)
        try:
            result = self.llm.generate(prompt, max_tokens=700, temperature=0.2)
            return result.text
        except ModelNotLoadedError:
            return "⚠️ No model loaded."
        except Exception as e:
            return f"⚠️ Summarization failed: {e}"

    def format_transcript_with_timestamps(self, segments: list[dict]) -> str:
        lines = []
        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "").strip()
            start_str = _fmt_time(start)
            end_str = _fmt_time(end)
            lines.append(f"[{start_str} – {end_str}] {text}")
        return "\n".join(lines)


def _fmt_time(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"
