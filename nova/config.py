from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from nova.config_helpers import env_bool, env_float, env_int

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SOUNDS_DIR = ROOT_DIR / "sounds"
BACKUP_DIR = ROOT_DIR / "backups"

load_dotenv(ROOT_DIR / ".env.local")
load_dotenv(ROOT_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return env_bool(name, default)


def _int(name: str, default: int) -> int:
    return env_int(name, default)


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def _int_first(default: int, *names: str) -> int:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip() and "put_" not in value:
            try:
                return int(value)
            except ValueError:
                continue
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
    led_pin: int = _int_first(18, "NOVA_GPIO_LED_RING_PIN", "NOVA_LED_PIN")
    led_brightness: int = _int("NOVA_LED_BRIGHTNESS", 80)
    led_enabled: bool = _bool("NOVA_LED_ENABLED", False)
    volume_enabled: bool = _bool("NOVA_VOLUME_ENABLED", True)
    volume_hardware_enabled: bool = _bool("NOVA_VOLUME_HARDWARE_ENABLED", False)
    volume_default: int = _int("NOVA_VOLUME_DEFAULT", 60)
    volume_min: int = _int("NOVA_VOLUME_MIN", 0)
    volume_max: int = _int("NOVA_VOLUME_MAX", 100)
    volume_rotary_clk_pin: str = _env_first("NOVA_GPIO_ROTARY_CLK_PIN", "NOVA_VOLUME_ROTARY_CLK_PIN", default="D5")
    volume_rotary_dt_pin: str = _env_first("NOVA_GPIO_ROTARY_DT_PIN", "NOVA_VOLUME_ROTARY_DT_PIN", default="D6")
    volume_rotary_sw_pin: str = _env_first("NOVA_GPIO_ROTARY_SW_PIN", "NOVA_ROTARY_SW_PIN", "NOVA_VOLUME_ROTARY_SW_PIN")
    volume_rotary_mute_enabled: bool = _bool("NOVA_ROTARY_MUTE_ENABLED", True)
    volume_rotary_step: float = env_float("NOVA_VOLUME_ROTARY_STEP", 2.5)
    volume_rotary_reverse: bool = _bool("NOVA_VOLUME_ROTARY_REVERSE", False)
    oled_enabled: bool = _bool("NOVA_OLED_ENABLED", False)
    oled_width: int = _int("NOVA_OLED_WIDTH", 128)
    oled_height: int = _int("NOVA_OLED_HEIGHT", 64)
    oled_i2c_address: int = _int_first(0x3C, "NOVA_GPIO_OLED_I2C_ADDRESS", "NOVA_OLED_I2C_ADDRESS")
    oled_refresh_seconds: int = _int("NOVA_OLED_REFRESH_SECONDS", 5)
    climate_enabled: bool = _bool("NOVA_CLIMATE_ENABLED", False)
    climate_sensor_type: str = os.getenv("NOVA_CLIMATE_SENSOR_TYPE", "DHT22")
    climate_pin: str = _env_first("NOVA_GPIO_DHT22_PIN", "NOVA_CLIMATE_PIN", default="D17")
    light_enabled: bool = _bool("NOVA_LIGHT_ENABLED", False)
    light_i2c_address: int = _int_first(0x23, "NOVA_GPIO_BH1750_I2C_ADDRESS", "NOVA_LIGHT_I2C_ADDRESS")
    voltage_enabled: bool = _bool("NOVA_VOLTAGE_ENABLED", False)
    voltage_channel: int = _int("NOVA_VOLTAGE_CHANNEL", 0)
    voltage_scale: float = env_float("NOVA_VOLTAGE_SCALE", 5.0)
    lockdown_enabled: bool = _bool("NOVA_LOCKDOWN_ENABLED", True)
    lockdown_motion_enabled: bool = _bool("NOVA_LOCKDOWN_MOTION_ENABLED", False)
    lockdown_camera_enabled: bool = _bool("NOVA_LOCKDOWN_CAMERA_ENABLED", False)
    lockdown_alert_sound: str = os.getenv("NOVA_LOCKDOWN_ALERT_SOUND", "")
    camera_enabled: bool = _bool("NOVA_CAMERA_ENABLED", False)
    motion_enabled: bool = _bool("NOVA_MOTION_ENABLED", False)
    motion_pin: str = _env_first("NOVA_GPIO_PIR_PIN", "NOVA_MOTION_PIN", default="D23")
    ultrasonic_enabled: bool = _bool("NOVA_ULTRASONIC_ENABLED", False)
    ultrasonic_trigger_pin: str = _env_first("NOVA_GPIO_ULTRASONIC_TRIGGER_PIN", "NOVA_ULTRASONIC_TRIGGER_PIN", default="D24")
    ultrasonic_echo_pin: str = _env_first("NOVA_GPIO_ULTRASONIC_ECHO_PIN", "NOVA_ULTRASONIC_ECHO_PIN", default="D25")
    sleep_enabled: bool = _bool("NOVA_SLEEP_ENABLED", True)
    sleep_oled_dim: bool = _bool("NOVA_SLEEP_OLED_DIM", True)
    notification_enabled: bool = _bool("NOVA_NOTIFICATIONS_ENABLED", True)
    notification_history_limit: int = _int("NOVA_NOTIFICATION_HISTORY_LIMIT", 50)
    account_enabled: bool = _bool("NOVA_ACCOUNTS_ENABLED", True)
    microphone_enabled: bool = _bool("NOVA_MICROPHONE_ENABLED", False)
    voice_login_enabled: bool = _bool("NOVA_VOICE_LOGIN_ENABLED", False)
    voice_profile_dir: str = os.getenv("NOVA_VOICE_PROFILE_DIR", "data/voice_profiles")
    voice_confidence_threshold: float = env_float("NOVA_VOICE_CONFIDENCE_THRESHOLD", 0.82)
    backup_enabled: bool = _bool("NOVA_BACKUP_ENABLED", True)
    backup_time: str = os.getenv("NOVA_BACKUP_TIME", "00:00")
    backup_keep_days: int = _int("NOVA_BACKUP_KEEP_DAYS", 30)
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_search_engine_id: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    spotify_redirect_uri: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/callback")


settings = Settings()
