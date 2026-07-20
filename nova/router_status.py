from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from nova.config import settings
from nova.storage import JsonStore


MAIN_RADIOS = {
    "main_24": "2.4 GHz",
    "main_5g1": "5 GHz-1",
    "main_5g2": "5 GHz-2",
}

GUEST_RADIOS = {
    "guest_24": "2.4 GHz guest network",
    "guest_5g1": "5 GHz-1 guest network",
    "guest_5g2": "5 GHz-2 guest network",
}

GUEST_TO_MAIN = {
    "guest_24": "main_24",
    "guest_5g1": "main_5g1",
    "guest_5g2": "main_5g2",
}

DEFAULT_RADIOS = {
    "smart_connect": settings.router_default_smart_connect,
    "ofdma": settings.router_default_ofdma,
    "main_24": settings.router_default_main_24,
    "main_5g1": settings.router_default_main_5g1,
    "main_5g2": settings.router_default_main_5g2,
    "guest_24": False,
    "guest_5g1": False,
    "guest_5g2": False,
}


@dataclass(frozen=True)
class RouterSnapshot:
    radios: dict[str, bool | None]
    last_verified: str | None
    speed_test: dict[str, Any] | None

    def main_wifi_on(self) -> bool:
        return any(self.radios.get(key) is True for key in MAIN_RADIOS)

    def main_wifi_off(self) -> bool:
        return all(self.radios.get(key) is False for key in MAIN_RADIOS)

    def summary(self) -> str:
        parts = [
            f"Main 2.4 GHz: {_state(self.radios.get('main_24'))}",
            f"Main 5 GHz-1: {_state(self.radios.get('main_5g1'))}",
            f"Main 5 GHz-2: {_state(self.radios.get('main_5g2'))}",
            f"Guest 2.4 GHz: {_state(self.radios.get('guest_24'))}",
            f"Guest 5 GHz-1: {_state(self.radios.get('guest_5g1'))}",
            f"Guest 5 GHz-2: {_state(self.radios.get('guest_5g2'))}",
            f"Smart Connect: {_state(self.radios.get('smart_connect'))}",
            f"OFDMA: {_state(self.radios.get('ofdma'))}",
        ]
        if self.speed_test:
            download = self.speed_test.get("download_mbps", "N/A")
            upload = self.speed_test.get("upload_mbps", "N/A")
            ping = self.speed_test.get("ping_ms", "N/A")
            parts.append(f"Latest speed test: {download} down, {upload} up, {ping} ping")
        return "; ".join(parts)


class RouterStateStore:
    def __init__(self, store: JsonStore | None = None) -> None:
        self.store = store or JsonStore()

    def snapshot(self) -> RouterSnapshot:
        data = self.store.read("router_state.json")
        radios = dict(DEFAULT_RADIOS)
        radios.update(data.get("radios") or {})
        return RouterSnapshot(
            radios={key: _coerce_bool(value) for key, value in radios.items()},
            last_verified=data.get("last_verified"),
            speed_test=data.get("speed_test"),
        )

    def save_radios(self, radios: dict[str, bool | None], operation: str) -> None:
        data = self.store.read("router_state.json")
        current = dict(data.get("radios") or {})
        current.update({key: value for key, value in radios.items() if value is not None})
        data["radios"] = current
        data["last_verified"] = datetime.now().isoformat(timespec="seconds")
        data["last_operation"] = operation
        self.store.write("router_state.json", data)

    def save_previous_main_state(self, radios: dict[str, bool | None]) -> None:
        data = self.store.read("router_state.json")
        data["previous_main_wifi_state"] = {
            key: radios.get(key)
            for key in ("smart_connect", "ofdma", "main_24", "main_5g1", "main_5g2")
            if radios.get(key) is not None
        }
        self.store.write("router_state.json", data)

    def previous_main_state(self) -> dict[str, bool]:
        data = self.store.read("router_state.json")
        saved = data.get("previous_main_wifi_state") or {}
        defaults = {key: DEFAULT_RADIOS[key] for key in ("smart_connect", "ofdma", "main_24", "main_5g1", "main_5g2")}
        defaults.update({key: bool(value) for key, value in saved.items() if value is not None})
        return defaults

    def save_speed_test(self, result: dict[str, Any]) -> None:
        data = self.store.read("router_state.json")
        safe_result = {
            "download_mbps": result.get("download_mbps"),
            "upload_mbps": result.get("upload_mbps"),
            "ping_ms": result.get("ping_ms"),
            "verified_at": datetime.now().isoformat(timespec="seconds"),
        }
        data["speed_test"] = safe_result
        data["last_operation"] = "speed_test"
        self.store.write("router_state.json", data)


def status_summary() -> str:
    if not settings.router_control_enabled:
        return "Router control is disabled."
    return RouterStateStore().snapshot().summary()


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on", "enabled"}:
            return True
        if lowered in {"0", "false", "no", "off", "disabled"}:
            return False
    return None


def _state(value: bool | None) -> str:
    if value is True:
        return "On"
    if value is False:
        return "Off"
    return "N/A"
