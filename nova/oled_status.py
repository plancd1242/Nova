from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OledStatusSummary:
    mode: str
    available: bool


def status_summary() -> OledStatusSummary:
    try:
        from nova import oled

        display = oled.get_display()
        return OledStatusSummary(display.current_mode, display.hardware_ready)
    except Exception:
        return OledStatusSummary("N/A", False)
