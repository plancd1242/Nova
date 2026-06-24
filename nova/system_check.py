from __future__ import annotations

import shutil
from datetime import datetime

from nova.config import DATA_DIR, settings


def masked_status(value: str, placeholder_prefix: str = "put_") -> str:
    if not value or value.startswith(placeholder_prefix):
        return "missing"
    return "configured"


def system_check(led_ready: bool) -> str:
    checks = [
        f"Voice: {'eSpeak NG found' if shutil.which('espeak-ng') else 'eSpeak NG missing, print fallback ready'}",
        f"LED: {'hardware mode ready' if led_ready else 'text fallback ready'}",
        f"Storage: {DATA_DIR} ready",
        f"Weather key: {masked_status(settings.openweather_api_key)}",
        f"Google search keys: {masked_status(settings.google_api_key)} and {masked_status(settings.google_search_engine_id)}",
        f"Spotify keys: {masked_status(settings.spotify_client_id)} and {masked_status(settings.spotify_client_secret)}",
        f"Time: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
        "Microphone: placeholder ready, typed mode active",
        "Privacy: audio recordings are not saved by default",
    ]
    return "System check. " + " | ".join(checks)

