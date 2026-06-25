from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from nova.config import settings
from nova.storage import JsonStore


@dataclass(frozen=True)
class LockdownState:
    status: str
    active: bool


class LockdownManager:
    def __init__(self, store: JsonStore | None = None) -> None:
        self.store = store or JsonStore()

    def activate(self) -> str:
        if not settings.lockdown_enabled:
            return "Lockdown mode is disabled in settings."
        data = self.store.read("settings.json")
        data["lockdown_active"] = True
        data["lockdown_started_at"] = datetime.now().isoformat(timespec="seconds")
        self.store.write("settings.json", data)
        return "Lockdown mode is active."

    def deactivate(self) -> str:
        data = self.store.read("settings.json")
        data["lockdown_active"] = False
        self.store.write("settings.json", data)
        return "Lockdown mode is off."

    def state(self) -> LockdownState:
        if not settings.lockdown_enabled:
            return LockdownState("Disabled", False)
        active = bool(self.store.read("settings.json").get("lockdown_active", False))
        return LockdownState("Active" if active else "Ready", active)
