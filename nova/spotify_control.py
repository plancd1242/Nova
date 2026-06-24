from __future__ import annotations

from nova.config import settings


def spotify_command(_: str) -> str:
    if (
        not settings.spotify_client_id
        or settings.spotify_client_id.startswith("put_")
        or not settings.spotify_client_secret
        or settings.spotify_client_secret.startswith("put_")
    ):
        return "Spotify is not set up yet. Add Spotify keys to .env.local."
    return "Spotify setup is detected, but playback control is a later module."

