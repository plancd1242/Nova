from __future__ import annotations

from dataclasses import dataclass

from nova.config import settings


@dataclass(frozen=True)
class VoltageReading:
    status: str
    volts: float | None = None

    @property
    def display(self) -> str:
        if self.volts is None:
            return "N/A" if self.status != "Disabled" else "Disabled"
        return f"{self.volts:.2f}V"


def read_voltage() -> VoltageReading:
    if not settings.voltage_enabled:
        return VoltageReading("Disabled")
    return VoltageReading("Unsupported")
