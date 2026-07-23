from __future__ import annotations

import time
from typing import Protocol

from nova.config import settings
from nova.speech_to_text import TranscriptionResult, get_speech_to_text
from nova.wake_word import get_wake_word_detector


class NovaCommandApp(Protocol):
    state: object

    def status_display(self, mode: str, extra_lines: list[str] | tuple[str, ...] | None = None) -> None:
        ...

    def handle_command(self, command: str) -> str:
        ...

    def say(self, text: str) -> None:
        ...


class VoiceLoop:
    def __init__(self, app: NovaCommandApp) -> None:
        self.app = app
        self.transcriber = get_speech_to_text()
        self.detector = get_wake_word_detector()

    def status(self) -> str:
        return self.transcriber.status()

    def listen_once(self) -> str:
        self.app.status_display("listening")
        result = self.transcriber.listen_once()
        if not result.ok:
            self.app.status_display("done")
            return result.message
        self.app.status_display("thinking")
        answer = self.app.handle_command(result.text)
        self.app.status_display("done")
        return self._voice_answer(result.text, answer)

    def run_forever(self) -> None:
        if not settings.voice_commands_enabled:
            self.app.say("Voice commands are disabled.")
            return
        if settings.voice_wake_word_enabled:
            self._run_wake_word_mode()
            return
        self._run_listen_once_loop()

    def _run_listen_once_loop(self) -> None:
        self.app.say("Nova voice mode is online. Press Control C to stop.")
        try:
            while getattr(self.app.state, "running", True):
                answer = self.listen_once()
                self.app.say(answer)
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.app.say("Nova voice mode is stopping.")

    def _run_wake_word_mode(self) -> None:
        status = self.detector.status()
        if not status.available:
            self.app.say(status.message)
            return
        self.app.say("Wake-word mode is online. Say hey Nova, then your command.")
        try:
            while getattr(self.app.state, "running", True):
                self.app.status_display("ready")
                wake = self.detector.wait_for_wake()
                if wake.status != "Detected":
                    self.app.say(wake.message)
                    break
                self.app.status_display("listening")
                self.app.say("Uh-huh?")
                command = self.transcriber.listen_for_command()
                self._handle_wake_command(command)
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.app.say("Wake-word listening is stopping.")

    def _handle_wake_command(self, result: TranscriptionResult) -> None:
        if not result.ok:
            self.app.status_display("done")
            self.app.say(result.message)
            return
        self.app.status_display("thinking")
        answer = self.app.handle_command(result.text)
        self.app.status_display("speaking")
        self.app.say(self._voice_answer(result.text, answer))
        self.app.status_display("done")

    def _voice_answer(self, heard: str, answer: str) -> str:
        if answer.strip().lower() == "i do not know that command yet.":
            return f'I heard "{heard}", but I do not know that command yet.'
        return answer
