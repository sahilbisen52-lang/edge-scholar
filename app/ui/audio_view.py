"""
Audio Notes view — Local speech-to-text transcription and lecture study tools.
Supports microphone recording, audio file import, and Whisper ASR.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QRunnable, QThreadPool, Signal, QObject, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QFileDialog, QFrame, QProgressBar
)

from app.core.app_context import AppContext
from app.audio.recorder import AudioRecorder
from app.ai.whisper_provider import WhisperProvider
from app.ui.styles.theme import (
    ACCENT, TEXT_SECONDARY, BG_SURFACE, BORDER, TEXT_PRIMARY,
    TEXT_MUTED, SUCCESS, WARNING, ERROR, BG_ELEVATED, BG_DARK
)

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = logging.getLogger("edge_scholar.ui.audio")


class AudioWorkerSignals(QObject):
    transcription_done = Signal(dict)
    tool_done = Signal(str, str)
    error = Signal(str)


class AudioTranscribeWorker(QRunnable):
    def __init__(self, ctx: AppContext, audio_path: Path):
        super().__init__()
        self.ctx = ctx
        self.audio_path = audio_path
        self.signals = AudioWorkerSignals()

    def run(self) -> None:
        try:
            whisper = WhisperProvider()
            if not whisper.is_available():
                # Provide an educational mock transcript if Whisper is not installed
                res = {
                    "text": (
                        "[Note: faster-whisper/openai-whisper is not currently installed. "
                        "Here is a sample lecture transcript from an Operating Systems lecture]\n\n"
                        "Today we will cover CPU scheduling algorithms. First, First-Come First-Served or FCFS "
                        "is the simplest algorithm where the process requesting the CPU first gets allocated first. "
                        "However, it suffers from the convoy effect. Second, Shortest Job First or SJF yields "
                        "minimal average waiting time but requires predicting future CPU burst durations. "
                        "Third, Round Robin allocates a fixed time quantum to each active process in turn, "
                        "providing good response time for interactive systems."
                    ),
                    "segments": [
                        {"start": 0.0, "end": 12.0, "text": "Today we will cover CPU scheduling algorithms."},
                        {"start": 12.5, "end": 28.0, "text": "First, First-Come First-Served or FCFS is the simplest algorithm."},
                        {"start": 28.5, "end": 45.0, "text": "Second, Shortest Job First yields minimal average waiting time."},
                        {"start": 45.5, "end": 65.0, "text": "Third, Round Robin allocates a fixed time quantum to each active process."}
                    ],
                    "language": "en",
                    "duration_seconds": 1.2,
                    "backend": "Sample Demonstration Transcript",
                }
                self.signals.transcription_done.emit(res)
                return

            whisper.load_model(self.ctx.settings.selected_asr_model)
            res = whisper.transcribe(self.audio_path)
            self.signals.transcription_done.emit(res)

        except Exception as e:
            logger.exception("Audio transcription failed: %s", e)
            self.signals.error.emit(str(e))


class AudioToolWorker(QRunnable):
    def __init__(self, ctx: AppContext, tool_type: str, transcript: str):
        super().__init__()
        self.ctx = ctx
        self.tool_type = tool_type
        self.transcript = transcript
        self.signals = AudioWorkerSignals()

    def run(self) -> None:
        try:
            from app.ai.provider_factory import ProviderFactory
            from app.utils.paths import get_models_dir

            factory = ProviderFactory(
                preferred=self.ctx.settings.preferred_runtime,
                models_dir=get_models_dir(),
            )
            provider = factory.create()

            if self.tool_type == "summary":
                from app.rag.prompt_templates import lecture_summary_prompt
                prompt = lecture_summary_prompt(self.transcript)
            elif self.tool_type == "quiz":
                from app.rag.prompt_templates import quiz_prompt
                prompt = quiz_prompt(self.transcript, "Lecture Audio")
            elif self.tool_type == "notes":
                from app.rag.prompt_templates import notes_prompt
                prompt = notes_prompt(self.transcript, "Lecture Audio")
            else:
                prompt = f"Summarize and extract key terms from: {self.transcript[:4000]}"

            res = provider.generate(prompt, max_tokens=600, temperature=0.2)
            self.signals.tool_done.emit(self.tool_type, res.text)

        except Exception as e:
            logger.exception("Audio study tool %s failed: %s", self.tool_type, e)
            self.signals.error.emit(str(e))


class AudioView(QWidget):
    def __init__(self, ctx: AppContext, main_window: "MainWindow") -> None:
        super().__init__()
        self.ctx = ctx
        self.main_window = main_window
        self._pool = QThreadPool.globalInstance()
        self._recorder = AudioRecorder()
        self._record_timer = QTimer(self)
        self._record_seconds = 0
        self._last_transcript = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Header
        top_row = QHBoxLayout()
        header = QLabel("Audio Notes & Transcription")
        header.setObjectName("heading_label")
        top_row.addWidget(header)
        top_row.addStretch()

        badge = QLabel("LOCAL ASR • ZERO CLOUD UPLOAD")
        badge.setStyleSheet(
            f"background-color: {BG_ELEVATED}; border: 1px solid {BORDER}; "
            f"border-radius: 4px; padding: 4px 10px; color: {TEXT_SECONDARY}; "
            f"font-size: 11px; font-weight: 600;"
        )
        top_row.addWidget(badge)
        layout.addLayout(top_row)

        sub = QLabel(
            "Transcribe lecture recordings and spoken notes completely on-device. "
            "Convert recordings into summaries, key concepts, and exam questions."
        )
        sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(sub)

        # Controls bar
        ctrl_card = QFrame()
        ctrl_card.setObjectName("card")
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(12)

        self.record_btn = QPushButton("🎙️ Start Recording")
        self.record_btn.setObjectName("primary_btn")
        self.record_btn.setFixedHeight(38)
        self.record_btn.clicked.connect(self._toggle_recording)
        ctrl_layout.addWidget(self.record_btn)

        self.upload_btn = QPushButton("📁 Upload Audio File")
        self.upload_btn.setObjectName("secondary_btn")
        self.upload_btn.setFixedHeight(38)
        self.upload_btn.clicked.connect(self._upload_audio)
        ctrl_layout.addWidget(self.upload_btn)

        ctrl_layout.addStretch()

        self.rec_status_lbl = QLabel("Microphone: Ready")
        self.rec_status_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; font-weight: 600;")
        ctrl_layout.addWidget(self.rec_status_lbl)

        layout.addWidget(ctrl_card)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 12px;")
        self.status_lbl.hide()
        layout.addWidget(self.status_lbl)

        # Transcript display
        disp_title = QLabel("Lecture Transcript:")
        disp_title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 14px;")
        layout.addWidget(disp_title)

        self.transcript_box = QTextEdit()
        self.transcript_box.setReadOnly(True)
        self.transcript_box.setStyleSheet(
            f"background-color: {BG_DARK}; border: 1px solid {BORDER}; "
            f"border-radius: 8px; font-size: 14px; color: {TEXT_PRIMARY}; padding: 12px;"
        )
        self.transcript_box.setPlaceholderText(
            "Spoken lecture transcript will appear here with timestamp segments...\n\n"
            "Click 'Upload Audio File' (.wav, .mp3) or 'Start Recording' to begin."
        )
        layout.addWidget(self.transcript_box, 1)

        # Actions Row
        act_row = QHBoxLayout()
        act_row.setSpacing(10)

        self.btn_sum = QPushButton("📝 Summarize Lecture")
        self.btn_sum.setObjectName("secondary_btn")
        self.btn_sum.setFixedHeight(36)
        self.btn_sum.clicked.connect(lambda: self._run_audio_tool("summary"))
        act_row.addWidget(self.btn_sum)

        self.btn_notes = QPushButton("📋 Generate Notes")
        self.btn_notes.setObjectName("secondary_btn")
        self.btn_notes.setFixedHeight(36)
        self.btn_notes.clicked.connect(lambda: self._run_audio_tool("notes"))
        act_row.addWidget(self.btn_notes)

        self.btn_quiz = QPushButton("🎓 Generate Quiz")
        self.btn_quiz.setObjectName("secondary_btn")
        self.btn_quiz.setFixedHeight(36)
        self.btn_quiz.clicked.connect(lambda: self._run_audio_tool("quiz"))
        act_row.addWidget(self.btn_quiz)

        act_row.addStretch()

        self.btn_copy = QPushButton("📋 Copy Transcript")
        self.btn_copy.setObjectName("secondary_btn")
        self.btn_copy.setFixedHeight(36)
        self.btn_copy.clicked.connect(self._copy_transcript)
        act_row.addWidget(self.btn_copy)

        for b in [self.btn_sum, self.btn_notes, self.btn_quiz, self.btn_copy]:
            b.setEnabled(False)

        layout.addLayout(act_row)

        self._record_timer.timeout.connect(self._update_record_time)

    def _toggle_recording(self) -> None:
        if not self._recorder.is_recording():
            if not self._recorder.is_available():
                QMessageBox.warning(
                    self, "Microphone Unavailable",
                    "Microphone recording requires 'sounddevice'.\n"
                    "You can still upload existing audio files (.wav, .mp3) to transcribe."
                )
                return
            try:
                self._recorder.start()
                self._record_seconds = 0
                self._record_timer.start(1000)
                self.record_btn.setText("⏹ Stop Recording")
                self.rec_status_lbl.setText("🔴 Recording: 00:00")
                self.rec_status_lbl.setStyleSheet(f"color: {ERROR}; font-weight: 700;")
                self.upload_btn.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Recording Error", f"Could not start microphone: {e}")
        else:
            self._record_timer.stop()
            self.record_btn.setText("🎙️ Start Recording")
            self.rec_status_lbl.setText("Microphone: Ready")
            self.rec_status_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600;")
            self.upload_btn.setEnabled(True)

            try:
                audio_data = self._recorder.stop()
                save_path = self.ctx.data_dir / "transcripts" / "recorded_lecture.wav"
                self._recorder.save_wav(audio_data, save_path)
                self._process_audio_file(save_path)
            except Exception as e:
                QMessageBox.critical(self, "Recording Save Error", f"Could not process recording: {e}")

    def _update_record_time(self) -> None:
        self._record_seconds += 1
        mins = self._record_seconds // 60
        secs = self._record_seconds % 60
        self.rec_status_lbl.setText(f"🔴 Recording: {mins:02d}:{secs:02d}")

    def _upload_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio Recording", str(Path.home()),
            "Audio Files (*.wav *.mp3 *.m4a *.ogg *.flac);;All Files (*.*)"
        )
        if path:
            self._process_audio_file(Path(path))

    def _process_audio_file(self, path: Path) -> None:
        self.progress_bar.show()
        self.status_lbl.setText(f"Transcribing '{path.name}' on-device...")
        self.status_lbl.show()
        self.record_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)

        worker = AudioTranscribeWorker(self.ctx, path)
        worker.signals.transcription_done.connect(self._on_transcription_done)
        worker.signals.error.connect(self._on_transcription_error)
        self._pool.start(worker)

    def _on_transcription_done(self, res: dict) -> None:
        self.progress_bar.hide()
        self.record_btn.setEnabled(True)
        self.upload_btn.setEnabled(True)
        self.status_lbl.setText(f"✅ Transcribed in {res.get('duration_seconds', 0):.2f}s ({res.get('backend', 'local')})")

        text = res.get("text", "")
        segments = res.get("segments", [])
        self._last_transcript = text

        if segments:
            lines = []
            for s in segments:
                start = s.get("start", 0)
                end = s.get("end", 0)
                st_str = f"{int(start//60):02d}:{int(start%60):02d}"
                en_str = f"{int(end//60):02d}:{int(end%60):02d}"
                lines.append(f"[{st_str} - {en_str}]  {s.get('text', '')}")
            self.transcript_box.setPlainText("\n".join(lines))
        else:
            self.transcript_box.setPlainText(text)

        for b in [self.btn_sum, self.btn_notes, self.btn_quiz, self.btn_copy]:
            b.setEnabled(True)

    def _on_transcription_error(self, err: str) -> None:
        self.progress_bar.hide()
        self.record_btn.setEnabled(True)
        self.upload_btn.setEnabled(True)
        self.status_lbl.setText(f"❌ Transcription failed: {err}")
        QMessageBox.critical(self, "Transcription Error", f"Transcription failed:\n\n{err}")

    def _run_audio_tool(self, tool_type: str) -> None:
        if not self._last_transcript.strip():
            QMessageBox.warning(self, "No Transcript", "Please transcribe an audio file or recording first.")
            return

        self.progress_bar.show()
        self.status_lbl.setText(f"Generating {tool_type} from lecture transcript...")
        self.status_lbl.show()

        worker = AudioToolWorker(self.ctx, tool_type, self._last_transcript)
        worker.signals.tool_done.connect(self._on_tool_done)
        worker.signals.error.connect(self._on_transcription_error)
        self._pool.start(worker)

    def _on_tool_done(self, tool_type: str, result_text: str) -> None:
        self.progress_bar.hide()
        self.status_lbl.setText(f"✅ Generated {tool_type} from lecture transcript!")

        # Append to transcript box with clean separator
        current = self.transcript_box.toPlainText()
        header = f"\n\n{'═' * 50}\n🎓 LECTURE {tool_type.upper()}:\n{'═' * 50}\n"
        self.transcript_box.setPlainText(current + header + result_text)
        sb = self.transcript_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _copy_transcript(self) -> None:
        content = self.transcript_box.toPlainText().strip()
        if content:
            QGuiApplication.clipboard().setText(content)
            self.status_lbl.setText("📋 Copied to clipboard!")
            self.status_lbl.show()
