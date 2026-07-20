from __future__ import annotations

from dataclasses import dataclass
import json
import threading
import time
from typing import Callable

from nova.config import settings
from nova.microphone import Microphone
from nova.speech_to_text import VoskSpeechToText


@dataclass(frozen=True)
class WakeWordStatus:
    available: bool
    running: bool
    status: str
    message: str


class WakeWordDetector:
    """Offline Vosk wake-word detector.

    This is not a specialized wake-word engine. It continuously runs Vosk and
    watches partial/final transcripts for configured phrases such as "hey nova".
    """

    def __init__(self) -> None:
        self.microphone = Microphone()
        self.transcriber = VoskSpeechToText()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_wake = 0.0

    def is_available(self) -> bool:
        return self.status().available

    def status(self) -> WakeWordStatus:
        if not settings.voice_wake_word_enabled:
            return WakeWordStatus(False, self.running, "Disabled", "Wake-word listening is disabled.")
        transcriber_status = self.transcriber.status()
        if transcriber_status != "Offline Vosk voice commands are available.":
            return WakeWordStatus(False, self.running, "Unavailable", transcriber_status)
        return WakeWordStatus(True, self.running, "Available", "Offline Vosk wake-word listening is available.")

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self, on_wake: Callable[[], None]) -> str:
        current = self.status()
        if not current.available:
            return current.message
        if self.running:
            return "Wake-word listener is already running."
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, args=(on_wake,), daemon=True, name="nova-vosk-wake-word")
        self._thread.start()
        return "Wake-word listener started."

    def wait_for_wake(self) -> WakeWordStatus:
        current = self.status()
        if not current.available:
            return current

        recognizer = self.transcriber.new_recognizer()
        woke = False
        stop = False

        def on_audio(audio: bytes) -> None:
            nonlocal woke, stop
            try:
                if recognizer.AcceptWaveform(audio):
                    text = self._text(recognizer.Result(), "text")
                else:
                    text = self._text(recognizer.PartialResult(), "partial")
                if self._contains_wake_word(text):
                    now = time.time()
                    if now - self._last_wake >= settings.voice_wake_cooldown_seconds:
                        self._last_wake = now
                        woke = True
                        stop = True
            except Exception:
                stop = True

        try:
            self.microphone.stream(on_audio, lambda: stop)
        except Exception as exc:
            return WakeWordStatus(False, False, "Unavailable", f"Wake-word listening failed: {type(exc).__name__}.")
        if woke:
            return WakeWordStatus(True, False, "Detected", "Wake word detected.")
        return WakeWordStatus(False, False, "Stopped", "Wake-word listening stopped.")

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)
        self._thread = None

    def _loop(self, on_wake: Callable[[], None]) -> None:
        recognizer = self.transcriber.new_recognizer()

        def on_audio(audio: bytes) -> None:
            nonlocal recognizer
            try:
                if recognizer.AcceptWaveform(audio):
                    text = self._text(recognizer.Result(), "text")
                else:
                    text = self._text(recognizer.PartialResult(), "partial")
                if self._contains_wake_word(text):
                    now = time.time()
                    if now - self._last_wake >= settings.voice_wake_cooldown_seconds:
                        self._last_wake = now
                        on_wake()
                        recognizer = self.transcriber.new_recognizer()
            except Exception:
                self._stop.set()

        try:
            self.microphone.stream(on_audio, self._stop.is_set)
        except Exception:
            self._stop.set()

    def _contains_wake_word(self, text: str) -> bool:
        normalized = " ".join(text.lower().split())
        if not normalized:
            return False
        wake_words = [word.strip().lower() for word in settings.voice_wake_words.split(",") if word.strip()]
        return any(word in normalized for word in wake_words)

    def _text(self, raw: str, key: str) -> str:
        try:
            data = json.loads(raw)
            return str(data.get(key, "")).strip()
        except Exception:
            return ""


_detector: WakeWordDetector | None = None


def get_wake_word_detector() -> WakeWordDetector:
    global _detector
    if _detector is None:
        _detector = WakeWordDetector()
    return _detector
