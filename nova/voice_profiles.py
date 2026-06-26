from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from nova.accounts import Accounts
from nova.config import ROOT_DIR, settings


@dataclass(frozen=True)
class VoiceLoginResult:
    status: str
    user: str | None = None
    confidence: float = 0.0


class VoiceProfileManager:
    def __init__(self, accounts: Accounts | None = None) -> None:
        self.accounts = accounts or Accounts()
        profile_path = Path(settings.voice_profile_dir)
        self.profile_dir = profile_path if profile_path.is_absolute() else ROOT_DIR / profile_path
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    def status(self) -> str:
        if not settings.voice_login_enabled:
            return "Voice login is disabled."
        if not settings.microphone_enabled:
            return "Voice login is unavailable because the microphone is disabled or missing."
        return "Voice login is enabled, but acoustic recognition is not installed yet."

    def create_profile_from_phrase(self, user: str, phrase: str = "Hi Nova") -> str:
        if not settings.voice_login_enabled:
            return "Voice login is disabled. Typed account switching still works."
        if not settings.microphone_enabled:
            return "Voice profile setup is unavailable because the microphone is disabled or missing."

        signature = self._signature(phrase)
        metadata = {
            "type": "phrase_signature_placeholder",
            "training_phrase": phrase,
            "signature": signature,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "local_only": True,
            "audio_file": None,
        }
        self.accounts.set_voice_profile(user, metadata)
        return f"Local voice profile metadata saved for {user}. Audio upload is disabled."

    def identify_from_phrase(self, phrase: str) -> VoiceLoginResult:
        if not settings.voice_login_enabled or not settings.microphone_enabled:
            return VoiceLoginResult("Unavailable")
        signature = self._signature(phrase)
        for user, profile in self.accounts.get_voice_profiles().items():
            if profile.get("signature") == signature:
                self.accounts.switch(user)
                return VoiceLoginResult("Matched", user=user, confidence=1.0)
        return VoiceLoginResult("Unsure", confidence=0.0)

    def missing_microphone_test(self) -> str:
        if settings.microphone_enabled:
            return "Microphone is enabled in settings; real hardware still needs Raspberry Pi testing."
        return "Microphone missing fallback OK. Typed account switching still works."

    def _signature(self, phrase: str) -> str:
        normalized = " ".join(phrase.strip().lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
