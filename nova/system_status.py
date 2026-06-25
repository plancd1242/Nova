from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemStatus:
    summary: str


class SystemStatusManager:
    def report(self) -> SystemStatus:
        parts: list[str] = []
        try:
            from nova.backup_status import get_backup_status

            backup = get_backup_status()
            parts.append(f"Backup: {backup.status}, latest {backup.latest}")
        except Exception:
            parts.append("Backup: N/A")

        try:
            from nova.hardware import HardwareManager

            parts.append(HardwareManager().report())
        except Exception:
            parts.append("Hardware: N/A")

        try:
            from nova.sensor_manager import get_sensor_manager

            parts.append("Sensors: " + get_sensor_manager().status_report())
        except Exception:
            parts.append("Sensors: N/A")

        try:
            from nova.oled_status import status_summary

            oled = status_summary()
            parts.append(f"OLED: {'Connected' if oled.available else 'Fallback'}, mode {oled.mode}")
        except Exception:
            parts.append("OLED: N/A")

        try:
            from nova.lockdown import LockdownManager
            from nova.sleep import SleepManager

            parts.append(f"Lockdown: {LockdownManager().state().status}")
            parts.append(f"Sleep: {SleepManager().state().status}")
        except Exception:
            parts.append("Modes: N/A")

        return SystemStatus(" | ".join(parts))
