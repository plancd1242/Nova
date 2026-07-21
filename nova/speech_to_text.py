from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any

from nova.config import ROOT_DIR, settings
from nova.microphone import Microphone
from nova.vosk_model_manager import get_vosk_model_manager


@dataclass(frozen=True)
class TranscriptionResult:
    ok: bool
    text: str
    status: str
    message: str


class VoskSpeechToText:
    def __init__(self) -> None:
        self.microphone = Microphone()
        self.sample_rate = settings.voice_sample_rate
        self.model_path = self._model_path()
        self._model: Any | None = None

    def status(self) -> str:
        if not settings.voice_commands_enabled:
            return "Voice commands are disabled."
        if settings.voice_transcription_engine.lower() != "vosk":
            return "Voice commands are configured for an unsupported transcription engine."
        mic_status = self.microphone.status()
        if not mic_status.available:
            return mic_status.message
        if not self._vosk_available():
            return "Vosk is not installed."
        model = get_vosk_model_manager().ensure_model()
        if not model.ok:
            return model.message
        return "Offline Vosk voice commands are available."

    def listen_once(self, seconds: float | None = None) -> TranscriptionResult:
        ready = self._ready_result()
        if ready is not None:
            return ready

        recognizer = self._recognizer()
        deadline = time.time() + max(1.0, seconds or settings.voice_record_seconds)

        try:
            self.microphone.stream(
                lambda audio: self._accept_audio(recognizer, audio),
                lambda: time.time() >= deadline,
            )
        except Exception as exc:
            return TranscriptionResult(False, "", "Microphone Error", f"Microphone listening failed: {type(exc).__name__}.")

        text = self._result_text(recognizer.FinalResult())
        if not text:
            return TranscriptionResult(False, "", "No Speech", "I did not hear a command.")
        return TranscriptionResult(True, text, "Recognized", text)

    def listen_for_command(self) -> TranscriptionResult:
        ready = self._ready_result()
        if ready is not None:
            return ready

        recognizer = self._recognizer()
        final_texts: list[str] = []
        last_voice = time.time()
        started = time.time()

        def on_audio(audio: bytes) -> None:
            nonlocal last_voice
            if recognizer.AcceptWaveform(audio):
                text = self._result_text(recognizer.Result())
                if text:
                    final_texts.append(text)
                    last_voice = time.time()
            else:
                partial = self._result_text(recognizer.PartialResult(), key="partial")
                if partial:
                    last_voice = time.time()

        def should_stop() -> bool:
            timed_out = time.time() - started >= settings.voice_command_timeout_seconds
            silence_after_speech = bool(final_texts) and time.time() - last_voice >= settings.voice_silence_seconds
            return timed_out or silence_after_speech

        try:
            self.microphone.stream(on_audio, should_stop)
        except Exception as exc:
            return TranscriptionResult(False, "", "Microphone Error", f"Microphone listening failed: {type(exc).__name__}.")

        final = self._result_text(recognizer.FinalResult())
        if final:
            final_texts.append(final)
        text = " ".join(part for part in final_texts if part).strip()
        if not text:
            return TranscriptionResult(False, "", "No Speech", "I did not hear a command.")
        return TranscriptionResult(True, text, "Recognized", text)

    def new_recognizer(self) -> Any:
        return self._recognizer()

    def model_ready(self) -> bool:
        return self._ready_result() is None

    def _accept_audio(self, recognizer: Any, audio: bytes) -> None:
        recognizer.AcceptWaveform(audio)

    def _recognizer(self) -> Any:
        from vosk import KaldiRecognizer  # type: ignore

        recognizer = KaldiRecognizer(self._load_model(), self.sample_rate)
        recognizer.SetWords(False)
        return recognizer

    def _load_model(self) -> Any:
        if self._model is None:
            from vosk import Model, SetLogLevel  # type: ignore

            SetLogLevel(-1)
            self._model = Model(str(self.model_path))
        return self._model

    def _ready_result(self) -> TranscriptionResult | None:
        if not settings.voice_commands_enabled:
            return TranscriptionResult(False, "", "Disabled", "Voice commands are disabled.")
        if settings.voice_transcription_engine.lower() != "vosk":
            return TranscriptionResult(False, "", "Unsupported", "Only offline Vosk transcription is supported right now.")
        mic_status = self.microphone.status()
        if not mic_status.available:
            return TranscriptionResult(False, "", mic_status.status, mic_status.message)
        if not self._vosk_available():
            return TranscriptionResult(False, "", "Not Installed", "Vosk is not installed.")
        model = get_vosk_model_manager().ensure_model()
        if not model.ok:
            return TranscriptionResult(False, "", "Missing Model", model.message)
        return None

    def _vosk_available(self) -> bool:
        try:
            import vosk  # type: ignore

            _ = vosk
            return True
        except Exception:
            return False

    def _model_path(self) -> Path:
        path = Path(settings.vosk_model_path)
        return path if path.is_absolute() else ROOT_DIR / path

    def _result_text(self, raw: str, key: str = "text") -> str:
        try:
            data = json.loads(raw)
            return str(data.get(key, "")).strip()
        except Exception:
            return ""


def get_speech_to_text() -> VoskSpeechToText:
    return VoskSpeechToText()
