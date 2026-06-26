from __future__ import annotations

from dataclasses import dataclass

from nova.config import settings


@dataclass(frozen=True)
class UltrasonicStatus:
    status: str
    distance_cm: float | None = None


def status() -> UltrasonicStatus:
    if not settings.ultrasonic_enabled:
        return UltrasonicStatus("Disabled")
    try:
        import board  # type: ignore
        import adafruit_hcsr04  # type: ignore

        trigger = getattr(board, settings.ultrasonic_trigger_pin)
        echo = getattr(board, settings.ultrasonic_echo_pin)
        sonar = adafruit_hcsr04.HCSR04(trigger_pin=trigger, echo_pin=echo)
        return UltrasonicStatus("Connected", float(sonar.distance))
    except ImportError:
        return UltrasonicStatus("Not Installed")
    except Exception:
        return UltrasonicStatus("Missing")


def test_ultrasonic() -> str:
    current = status()
    if current.distance_cm is None:
        return f"Ultrasonic sensor: {current.status}."
    return f"Ultrasonic sensor: {current.status}. Distance: {current.distance_cm:.1f} cm."
