from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser

from nova.config import settings
from nova.storage import JsonStore


class Alarms:
    def __init__(self, store: JsonStore):
        self.store = store
        self.tz = ZoneInfo(settings.timezone)

    def _now(self) -> datetime:
        return datetime.now(self.tz)

    def set_from_text(self, text: str) -> str:
        raw = re.sub(r"^set an alarm for\s+", "", text, flags=re.I).strip()
        if not raw:
            return "Tell me a time for the alarm."
        try:
            default = self._now().replace(second=0, microsecond=0)
            when = parser.parse(raw, fuzzy=True, default=default)
            if when.tzinfo is None:
                when = when.replace(tzinfo=self.tz)
            if "tomorrow" in raw.lower() and when.date() == self._now().date():
                when = when + timedelta(days=1)
            if when <= self._now():
                when = when + timedelta(days=1)
        except Exception:
            return "I could not understand that alarm time."
        data = self.store.read("alarms.json")
        data.setdefault("alarms", []).append({"id": str(uuid.uuid4()), "time": when.isoformat()})
        self.store.write("alarms.json", data)
        return f"Okay. I set an alarm for {when.strftime('%I:%M %p').lstrip('0')}."

    def list(self) -> str:
        alarms = self.store.read("alarms.json").get("alarms", [])
        if not alarms:
            return "No alarms are set."
        parts = [datetime.fromisoformat(item["time"]).strftime("%A at %I:%M %p").replace(" 0", " ") for item in alarms]
        return "Alarms: " + "; ".join(parts) + "."

    def cancel(self) -> str:
        self.store.write("alarms.json", {"alarms": []})
        return "I canceled the alarms."

    def pop_due(self) -> list[dict]:
        now = self._now()
        data = self.store.read("alarms.json")
        remaining, due = [], []
        for alarm in data.get("alarms", []):
            if datetime.fromisoformat(alarm["time"]) <= now:
                due.append(alarm)
            else:
                remaining.append(alarm)
        if due:
            self.store.write("alarms.json", {"alarms": remaining})
        return due

