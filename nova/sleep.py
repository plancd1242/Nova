from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from nova.config import settings
from nova.storage import JsonStore


@dataclass(frozen=True)
class SleepState:
    status: str
    active: bool


class SleepManager:
    def __init__(self, store: JsonStore | None = None) -> None:
        self.store = store or JsonStore()

    def activate(self) -> str:
        if not settings.sleep_enabled:
            return "Sleep mode is disabled in settings."
        data = self.store.read("settings.json")
        data["sleep_active"] = True
        data["sleep_started_at"] = datetime.now().isoformat(timespec="seconds")
        self.store.write("settings.json", data)
        return "Sleep mode is active."

    def deactivate(self) -> str:
        data = self.store.read("settings.json")
        data["sleep_active"] = False
        self.store.write("settings.json", data)
        return "Sleep mode is off."

    def state(self) -> SleepState:
        if not settings.sleep_enabled:
            return SleepState("Disabled", False)
        active = bool(self.store.read("settings.json").get("sleep_active", False))
        return SleepState("Active" if active else "Ready", active)
