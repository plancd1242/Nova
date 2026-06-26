from __future__ import annotations

from datetime import datetime
from typing import Any


class StatusProvider:
    def snapshot(self) -> dict[str, Any]:
        sensors = self._sensors()
        hardware = self._hardware()
        backup = self._backup()
        mode = self._mode()
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "nova": {
                "name": "Nova",
                "mode": mode,
                "face": self._face(mode),
                "online": True,
            },
            "time": datetime.now().strftime("%I:%M %p").lstrip("0"),
            "sensors": sensors,
            "hardware": hardware,
            "backup": backup,
            "battery": {"status": "Future", "level": "N/A"},
            "camera": self._camera(),
            "motion": self._motion(),
            "ultrasonic": self._ultrasonic(),
            "led": self._led(mode),
            "volume": self._volume(),
            "oled": self._oled(mode, sensors),
            "lockdown": self._lockdown(),
            "accounts": self._accounts(),
            "notifications": self._notifications(),
            "settings": self._settings(),
        }

    def _sensors(self) -> dict[str, str]:
        try:
            from nova.sensor_manager import get_sensor_manager

            snap = get_sensor_manager().snapshot()
            return {
                "temperature": snap.temperature,
                "humidity": snap.humidity,
                "wifi": snap.wifi,
                "voltage": snap.voltage,
                "light": snap.light,
            }
        except Exception:
            return {"temperature": "N/A", "humidity": "N/A", "wifi": "N/A", "voltage": "N/A", "light": "N/A"}

    def _hardware(self) -> list[dict[str, str]]:
        try:
            from nova.hardware import HardwareManager

            return [{"name": item.name, "status": item.status} for item in HardwareManager().status()]
        except Exception:
            return []

    def _backup(self) -> dict[str, Any]:
        try:
            from nova.backups import BackupManager

            manager = BackupManager()
            files = manager.list_backup_files()
            settings = manager.settings()
            return {
                "status": "Ready",
                "latest": files[0].name if files else "N/A",
                "next": settings.get("time", "00:00"),
                "history": [path.name for path in files[:10]],
                "keep_days": settings.get("keep_days", 30),
            }
        except Exception:
            return {"status": "N/A", "latest": "N/A", "next": "N/A", "history": [], "keep_days": "N/A"}

    def _mode(self) -> str:
        try:
            from nova.lockdown import LockdownManager
            from nova.sleep import SleepManager

            if LockdownManager().state().active:
                return "Lockdown"
            if SleepManager().state().active:
                return "Sleep"
        except Exception:
            pass
        return "Ready"

    def _camera(self) -> dict[str, str]:
        try:
            from nova.camera import status

            current = status()
            return {"status": current.status, "message": current.message, "stream": "/api/camera/stream"}
        except Exception:
            return {"status": "N/A", "message": "Camera Offline", "stream": ""}

    def _motion(self) -> dict[str, Any]:
        try:
            from nova.motion import status

            current = status()
            return {"status": current.status, "detected": current.detected}
        except Exception:
            return {"status": "N/A", "detected": None}

    def _ultrasonic(self) -> dict[str, Any]:
        try:
            from nova.ultrasonic import status

            current = status()
            return {"status": current.status, "distance_cm": current.distance_cm}
        except Exception:
            return {"status": "N/A", "distance_cm": None}

    def _led(self, mode: str) -> dict[str, str]:
        colors = {
            "Ready": "🟢 Ready",
            "Listening": "🔵 Listening",
            "Thinking": "🌈 Thinking",
            "Speaking": "🟣 Speaking",
            "Backup": "⚪ Backup",
            "Privacy": "🟠 Privacy",
            "Lockdown": "🔴 Lockdown",
            "Sleep": "😴 Sleep",
        }
        return {"status": colors.get(mode, "🟢 Ready")}

    def _volume(self) -> dict[str, str | int | bool]:
        try:
            from nova.volume import get_volume_manager

            state = get_volume_manager().state()
            return {
                "level": state.level,
                "saved_level": state.saved_level,
                "percent": state.percent,
                "bar_percent": state.bar_percent,
                "muted": state.muted,
                "display": state.display,
                "hardware": state.hardware,
                "mute_button": state.mute_button,
                "status": state.status,
            }
        except Exception:
            return {"level": 0, "percent": 0, "muted": True, "display": "N/A", "hardware": "N/A", "status": "N/A"}

    def _oled(self, mode: str, sensors: dict[str, str]) -> dict[str, str]:
        return {
            "face": self._face(mode),
            "mode": mode,
            "time": datetime.now().strftime("%I:%M %p").lstrip("0"),
            "temperature": sensors["temperature"],
            "humidity": sensors["humidity"],
            "wifi": sensors["wifi"],
            "voltage": sensors["voltage"],
        }

    def _lockdown(self) -> dict[str, Any]:
        try:
            from nova.lockdown import LockdownManager

            state = LockdownManager().state()
            return {"status": state.status, "active": state.active, "alerts": []}
        except Exception:
            return {"status": "N/A", "active": False, "alerts": []}

    def _accounts(self) -> dict[str, Any]:
        try:
            from nova.accounts import Accounts

            accounts = Accounts()
            data = accounts.store.read("users.json")
            return {
                "current": accounts.current_user(),
                "users": [{"name": name, "avatar": self._avatar(name)} for name in sorted(data.get("users", {}).keys())],
            }
        except Exception:
            return {"current": "N/A", "users": []}

    def _notifications(self) -> list[dict[str, str]]:
        try:
            from nova.storage import JsonStore

            return JsonStore().read("notifications.json").get("notifications", [])[-10:]
        except Exception:
            return []

    def _settings(self) -> dict[str, Any]:
        return {
            "voice": "Configured",
            "oled_brightness": "Future",
            "led_brightness": "Future",
            "backup_schedule": self._backup().get("next", "N/A"),
            "privacy_mode": "Available",
            "sleep_mode": "Available",
            "notifications": "Available",
        }

    def _face(self, mode: str) -> str:
        return {"Lockdown": "!!", "Sleep": "zz", "Privacy": "-_-", "Backup": "[v]"}.get(mode, ":)")

    def _avatar(self, name: str) -> str:
        return (name[:1] or "N").upper()
