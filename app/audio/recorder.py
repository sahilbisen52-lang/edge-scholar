"""Microphone recorder using sounddevice."""
from __future__ import annotations

import logging
import wave
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger("edge_scholar.audio")

SAMPLE_RATE = 16000  # 16kHz — standard for Whisper
CHANNELS = 1
DTYPE = np.float32


class AudioRecorder:
    def __init__(self) -> None:
        self._recording = False
        self._frames: list[np.ndarray] = []
        self._stream = None

    @staticmethod
    def is_available() -> bool:
        try:
            import sounddevice  # noqa
            return True
        except ImportError:
            return False

    def start(self) -> None:
        if not self.is_available():
            raise RuntimeError("sounddevice not installed. Run: pip install sounddevice")
        import sounddevice as sd
        self._frames = []
        self._recording = True

        def callback(indata: np.ndarray, frames: int, time_info, status) -> None:
            if status:
                logger.warning("Audio callback status: %s", status)
            if self._recording:
                self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=callback,
        )
        self._stream.start()
        logger.info("Recording started (%.0f Hz, %d ch)", SAMPLE_RATE, CHANNELS)

    def stop(self) -> np.ndarray:
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._frames:
            audio = np.concatenate(self._frames, axis=0).flatten()
        else:
            audio = np.zeros(SAMPLE_RATE, dtype=DTYPE)
        logger.info("Recording stopped. Samples: %d (%.1fs)", len(audio), len(audio) / SAMPLE_RATE)
        return audio

    def save_wav(self, audio: np.ndarray, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        audio_int = (audio * 32767).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_int.tobytes())
        logger.info("Saved WAV: %s", path)

    def is_recording(self) -> bool:
        return self._recording
