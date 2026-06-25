from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nova.config import DATA_DIR, settings


DEFAULT_FILES: dict[str, Any] = {
    "settings.json": {"privacy_until": None, "lockdown_active": False, "sleep_active": False},
    "users.json": {
        "current_user": settings.default_user,
        "users": {settings.default_user: {"alarms": [], "preferences": {}}},
    },
    "joke_history.json": {"users": {}},
    "backup_settings.json": {"enabled": True, "time": "00:00", "keep_days": 30},
    "backup_history.json": {"backups": []},
    "notifications.json": {"notifications": []},
    "alarms.json": {"alarms": []},
    "timers.json": {"timers": []},
    "notes.json": {"notes": []},
}


class JsonStore:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ensure_files()

    def ensure_files(self) -> None:
        for filename, default in DEFAULT_FILES.items():
            path = self.data_dir / filename
            if not path.exists():
                self.write(filename, default)

    def read(self, filename: str) -> Any:
        path = self.data_dir / filename
        if not path.exists():
            self.ensure_files()
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            default = DEFAULT_FILES.get(filename, {})
            self.write(filename, default)
            return default

    def write(self, filename: str, data: Any) -> None:
        path = self.data_dir / filename
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
