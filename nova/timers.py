from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from nova.config import settings
from nova.storage import JsonStore


class Timers:
    def __init__(self, store: JsonStore):
        self.store = store
        self.tz = ZoneInfo(settings.timezone)

    def _now(self) -> datetime:
        return datetime.now(self.tz)

    def _active(self) -> list[dict]:
        now = self._now()
        data = self.store.read("timers.json")
        timers = []
        for timer in data.get("timers", []):
            if datetime.fromisoformat(timer["ends_at"]) > now:
                timers.append(timer)
        if len(timers) != len(data.get("timers", [])):
            self.store.write("timers.json", {"timers": timers})
        return timers

    def create_from_text(self, text: str) -> str:
        match = re.search(r"(\d+)\s*(second|seconds|minute|minutes|hour|hours)", text, re.I)
        if not match:
            return "Tell me a timer like set a timer for 10 minutes."
        amount = int(match.group(1))
        unit = match.group(2).lower()
        seconds = amount
        if unit.startswith("minute"):
            seconds = amount * 60
        elif unit.startswith("hour"):
            seconds = amount * 3600
        ends_at = self._now() + timedelta(seconds=seconds)
        data = self.store.read("timers.json")
        data.setdefault("timers", []).append({"id": str(uuid.uuid4()), "label": f"{amount} {unit}", "ends_at": ends_at.isoformat()})
        self.store.write("timers.json", data)
        return f"Okay. I set a timer for {amount} {unit}."

    def list(self) -> str:
        timers = self._active()
        if not timers:
            return "No timers are running."
        now = self._now()
        parts = []
        for timer in timers:
            left = datetime.fromisoformat(timer["ends_at"]) - now
            seconds = max(0, int(left.total_seconds()))
            minutes, sec = divmod(seconds, 60)
            parts.append(f"{timer['label']} has {minutes} minutes and {sec} seconds left")
        return "Timers: " + "; ".join(parts) + "."

    def cancel(self) -> str:
        self.store.write("timers.json", {"timers": []})
        return "I canceled your timers."

    def pop_due(self) -> list[dict]:
        now = self._now()
        data = self.store.read("timers.json")
        remaining, due = [], []
        for timer in data.get("timers", []):
            if datetime.fromisoformat(timer["ends_at"]) <= now:
                due.append(timer)
            else:
                remaining.append(timer)
        if due:
            self.store.write("timers.json", {"timers": remaining})
        return due

