from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from nova.config import settings
from nova.storage import JsonStore


@dataclass(frozen=True)
class Notification:
    level: str
    title: str
    message: str
    created_at: str


class NotificationManager:
    def __init__(self, store: JsonStore | None = None) -> None:
        self.store = store or JsonStore()

    def notify(self, title: str, message: str, level: str = "info") -> str:
        if not settings.notification_enabled:
            return "Notifications are disabled."
        data = self.store.read("notifications.json")
        items = data.setdefault("notifications", [])
        items.append(
            {
                "level": level,
                "title": title,
                "message": message,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        data["notifications"] = items[-max(1, settings.notification_history_limit) :]
        self.store.write("notifications.json", data)
        return f"Notification saved: {title}."

    def history(self, limit: int = 5) -> str:
        items: list[dict[str, Any]] = self.store.read("notifications.json").get("notifications", [])
        if not items:
            return "No notifications yet."
        return "Notifications: " + "; ".join(item.get("title", "Untitled") for item in items[-limit:])

    def clear(self) -> str:
        self.store.write("notifications.json", {"notifications": []})
        return "Notifications cleared."
