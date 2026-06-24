from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv, find_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None


# ------------------------------------------------------------
# Load secret keys from .env.local or .env
# ------------------------------------------------------------

def _load_env_files() -> None:
    if load_dotenv is None:
        return

    # Load .env.local first if it exists
    if find_dotenv is not None:
        env_local = find_dotenv(".env.local", usecwd=True)
        if env_local:
            load_dotenv(env_local, override=False)

        env_file = find_dotenv(".env", usecwd=True)
        if env_file:
            load_dotenv(env_file, override=False)
    else:
        load_dotenv(".env.local", override=False)
        load_dotenv(".env", override=False)


_load_env_files()


# ------------------------------------------------------------
# Settings
# ------------------------------------------------------------

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "").strip()

# Good default model.
# You can change it later if you want.
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip()

# Offline backup voice
OFFLINE_VOICE = os.getenv("NOVA_OFFLINE_VOICE", "en+f3").strip()
OFFLINE_SPEED = os.getenv("NOVA_OFFLINE_SPEED", "140").strip()
OFFLINE_PITCH = os.getenv("NOVA_OFFLINE_PITCH", "45").strip()

# If this is true, Nova will print what she says in Terminal too.
PRINT_SPEECH = os.getenv("NOVA_PRINT_SPEECH", "true").lower() in ("1", "true", "yes", "on")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _safe_text(text: str) -> str:
    text = str(text or "").strip()
    if not text:
        return "Okay."
    return text


def _run_command(command: list[str]) -> bool:
    try:
        subprocess.run(command, check=True)
        return True
    except Exception:
        return False


def _play_audio_file(path: Path) -> bool:
    """
    Plays an audio file using whatever player exists.
    On Raspberry Pi, mpg123 is the easiest for MP3.
    """
    players = [
        ["mpg123", "-q", str(path)],
        ["mpv", "--really-quiet", str(path)],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
        ["afplay", str(path)],  # Mac fallback
    ]

    for command in players:
        if shutil.which(command[0]):
            return _run_command(command)

    print("Nova could not find an audio player. Install mpg123:")
    print("sudo apt install -y mpg123")
    return False


# ------------------------------------------------------------
# Offline voice
# ------------------------------------------------------------

def say_offline(text: str) -> None:
    """
    Private safe voice.
    This stays on the Raspberry Pi.
    """
    text = _safe_text(text)

    if PRINT_SPEECH:
        print(f"Nova offline: {text}")

    if shutil.which("espeak-ng"):
        worked = _run_command([
            "espeak-ng",
            "-v", OFFLINE_VOICE,
            "-s", OFFLINE_SPEED,
            "-p", OFFLINE_PITCH,
            text,
        ])
        if worked:
            return

    print("Nova could not use eSpeak NG.")
    print("Install it with:")
    print("sudo apt install -y espeak-ng alsa-utils")


# ------------------------------------------------------------
# Online realistic voice
# ------------------------------------------------------------

def say_online(text: str) -> bool:
    """
    Realistic online voice.
    This sends ONLY Nova's final reply text to ElevenLabs.
    It does NOT send microphone audio.
    """
    text = _safe_text(text)

    if PRINT_SPEECH:
        print(f"Nova online: {text}")

    if not ELEVENLABS_API_KEY:
        print("ElevenLabs API key is missing. Falling back to offline voice.")
        return False

    if not ELEVENLABS_VOICE_ID:
        print("ElevenLabs voice ID is missing. Falling back to offline voice.")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.25,
            "use_speaker_boost": True,
        },
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            params={"output_format": "mp3_44100_128"},
            timeout=30,
        )

        if response.status_code != 200:
            print(f"ElevenLabs voice failed: {response.status_code}")
            try:
                print(response.json())
            except Exception:
                print(response.text[:500])
            return False

        temp_dir = Path(tempfile.gettempdir())
        audio_path = temp_dir / "nova_voice.mp3"
        audio_path.write_bytes(response.content)

        return _play_audio_file(audio_path)

    except Exception as error:
        print(f"ElevenLabs voice error: {error}")
        return False


# ------------------------------------------------------------
# Main Nova speaking function
# ------------------------------------------------------------

def say(text: str, private: bool = False, force_offline: bool = False) -> None:
    """
    Use this everywhere in Nova.

    Normal:
        say("Hello Caleb. Nova is online.")

    Private:
        say("Your alarm is set.", private=True)

    Forced offline:
        say("Testing offline voice.", force_offline=True)
    """
    text = _safe_text(text)

    if private or force_offline:
        say_offline(text)
        return

    worked = say_online(text)

    if not worked:
        say_offline(text)


# ------------------------------------------------------------
# Compatibility names
# ------------------------------------------------------------
# These help if other Nova files already call speak() or nova_say().

def speak(text: str, private: bool = False) -> None:
    say(text, private=private)


def nova_say(text: str, private: bool = False) -> None:
    say(text, private=private)


# ------------------------------------------------------------
# Terminal test
# ------------------------------------------------------------

if __name__ == "__main__":
    import sys

    test_text = " ".join(sys.argv[1:]).strip()

    if not test_text:
        test_text = "Hello Caleb. Nova voice test successful."

    say(test_text)