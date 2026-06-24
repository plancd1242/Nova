from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser

from nova.config import settings
from nova.storage import JsonStore


class PrivacyManager:
    def __init__(self, store: JsonStore):
        self.store = store
        self.tz = ZoneInfo(settings.timezone)

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def until(self) -> datetime | None:
        raw = self.store.read("settings.json").get("privacy_until")
        if not raw:
            return None
        try:
            value = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if value <= self.now():
            self.clear()
            return None
        return value

    def is_private(self) -> bool:
        return self.until() is not None

    def set_for_minutes(self, minutes: int) -> datetime:
        until = self.now() + timedelta(minutes=minutes)
        data = self.store.read("settings.json")
        data["privacy_until"] = until.isoformat()
        self.store.write("settings.json", data)
        return until

    def set_until_text(self, text: str) -> datetime:
        target = parser.parse(text, fuzzy=True, default=self.now().replace(second=0, microsecond=0))
        if target.tzinfo is None:
            target = target.replace(tzinfo=self.tz)
        if target <= self.now():
            target = target + timedelta(days=1)
        data = self.store.read("settings.json")
        data["privacy_until"] = target.isoformat()
        self.store.write("settings.json", data)
        return target

    def clear(self) -> None:
        data = self.store.read("settings.json")
        data["privacy_until"] = None
        self.store.write("settings.json", data)

