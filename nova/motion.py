from __future__ import annotations

from dataclasses import dataclass

from nova.config import settings


@dataclass(frozen=True)
class MotionStatus:
    status: str
    detected: bool | None = None


def status() -> MotionStatus:
    if not settings.motion_enabled and not settings.lockdown_motion_enabled:
        return MotionStatus("Disabled")
    try:
        import board  # type: ignore
        import digitalio  # type: ignore

        pin = getattr(board, settings.motion_pin)
        pir = digitalio.DigitalInOut(pin)
        pir.direction = digitalio.Direction.INPUT
        return MotionStatus("Connected", bool(pir.value))
    except ImportError:
        return MotionStatus("Not Installed")
    except Exception:
        return MotionStatus("Missing")


def test_motion() -> str:
    current = status()
    if current.detected is None:
        return f"Motion sensor: {current.status}."
    return f"Motion sensor: {current.status}. Motion detected: {current.detected}."
