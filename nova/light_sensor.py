from __future__ import annotations

from dataclasses import dataclass

from nova.config import settings


@dataclass(frozen=True)
class LightReading:
    status: str
    lux: float | None = None

    @property
    def display(self) -> str:
        if self.lux is None:
            return "N/A" if self.status != "Disabled" else "Disabled"
        return f"{self.lux:.0f} lx"


def read_light() -> LightReading:
    if not settings.light_enabled:
        return LightReading("Disabled")
    try:
        import board  # type: ignore
        import busio  # type: ignore
        import adafruit_bh1750  # type: ignore

        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_bh1750.BH1750(i2c, address=settings.light_i2c_address)
        return LightReading("Connected", float(sensor.lux))
    except ImportError:
        return LightReading("Not Installed")
    except Exception:
        return LightReading("Missing")
