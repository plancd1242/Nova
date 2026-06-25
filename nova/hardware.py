from __future__ import annotations

from dataclasses import dataclass

from nova.config import settings


@dataclass(frozen=True)
class HardwareStatus:
    name: str
    status: str


class HardwareManager:
    def status(self) -> list[HardwareStatus]:
        return [
            HardwareStatus("OLED", "Enabled" if settings.oled_enabled else "Disabled"),
            HardwareStatus("LED", "Enabled" if settings.led_enabled else "Disabled"),
            HardwareStatus("Climate", "Enabled" if settings.climate_enabled else "Disabled"),
            HardwareStatus("Light", "Enabled" if settings.light_enabled else "Disabled"),
            HardwareStatus("Voltage", "Enabled" if settings.voltage_enabled else "Disabled"),
            HardwareStatus("Lockdown motion", "Enabled" if settings.lockdown_motion_enabled else "Disabled"),
            HardwareStatus("Lockdown camera", "Enabled" if settings.lockdown_camera_enabled else "Disabled"),
        ]

    def report(self) -> str:
        return "Hardware: " + "; ".join(f"{item.name}: {item.status}" for item in self.status())
