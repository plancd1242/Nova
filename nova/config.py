from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SOUNDS_DIR = ROOT_DIR / "sounds"

load_dotenv(ROOT_DIR / ".env.local")
load_dotenv(ROOT_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    nova_name: str = os.getenv("NOVA_NAME", "Nova")
    default_user: str = os.getenv("NOVA_DEFAULT_USER", "Caleb")
    city: str = os.getenv("NOVA_CITY", "Metamora")
    state: str = os.getenv("NOVA_STATE", "Michigan")
    country: str = os.getenv("NOVA_COUNTRY", "US")
    timezone: str = os.getenv("NOVA_TIMEZONE", "America/Detroit")
    espeak_speed: int = _int("NOVA_ESPEAK_SPEED", 140)
    espeak_pitch: int = _int("NOVA_ESPEAK_PITCH", 32)
    led_count: int = _int("NOVA_LED_COUNT", 12)
    led_pin: int = _int("NOVA_LED_PIN", 18)
    led_brightness: int = _int("NOVA_LED_BRIGHTNESS", 80)
    led_enabled: bool = _bool("NOVA_LED_ENABLED", False)
    oled_enabled: bool = _bool("NOVA_OLED_ENABLED", False)
    oled_width: int = _int("NOVA_OLED_WIDTH", 128)
    oled_height: int = _int("NOVA_OLED_HEIGHT", 64)
    oled_i2c_address: int = _int("NOVA_OLED_I2C_ADDRESS", 0x3C)
    oled_refresh_seconds: int = _int("NOVA_OLED_REFRESH_SECONDS", 5)
    climate_enabled: bool = _bool("NOVA_CLIMATE_ENABLED", False)
    climate_sensor_type: str = os.getenv("NOVA_CLIMATE_SENSOR_TYPE", "DHT22")
    climate_pin: str = os.getenv("NOVA_CLIMATE_PIN", "D4")
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_search_engine_id: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    spotify_redirect_uri: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/callback")


settings = Settings()
