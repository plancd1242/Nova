from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from nova.config import settings


@dataclass(frozen=True)
class ClimateReading:
    temperature_c: Optional[float]
    humidity_percent: Optional[float]
    ok: bool
    message: str = ""

    @property
    def temperature_f(self) -> Optional[float]:
        if self.temperature_c is None:
            return None
        return (self.temperature_c * 9 / 5) + 32

    def oled_lines(self) -> tuple[str, str]:
        if not self.ok or self.temperature_f is None or self.humidity_percent is None:
            return ("Temp: N/A", "Humidity: N/A")
        return (
            f"Temp: {self.temperature_f:.1f} F",
            f"Humidity: {self.humidity_percent:.0f} %",
        )


class DhtClimateSensor:
    def __init__(self) -> None:
        self.device: Optional[object] = None
        self.hardware_ready = False
        self.last_reading: Optional[ClimateReading] = None
        self.last_read_at: Optional[datetime] = None
        if settings.climate_enabled:
            self._try_hardware()

    def _try_hardware(self) -> None:
        try:
            import adafruit_dht  # type: ignore
            import board  # type: ignore

            pin = getattr(board, settings.climate_pin)
            sensor_name = settings.climate_sensor_type.strip().upper()
            sensor_class = adafruit_dht.DHT11 if sensor_name == "DHT11" else adafruit_dht.DHT22
            self.device = sensor_class(pin)
            self.hardware_ready = True
        except Exception as exc:
            print(f"[CLIMATE] hardware unavailable, using unavailable reading: {exc}")

    def read(self, allow_cached: bool = True) -> ClimateReading:
        if allow_cached and self.last_reading and self.last_read_at:
            if datetime.now() - self.last_read_at < timedelta(seconds=2):
                return self.last_reading

        if not self.hardware_ready or self.device is None:
            return ClimateReading(None, None, False, "Climate sensor unavailable")

        try:
            temperature_c = self.device.temperature
            humidity = self.device.humidity
            if temperature_c is None or humidity is None:
                raise RuntimeError("Sensor returned an empty reading")
            reading = ClimateReading(float(temperature_c), float(humidity), True)
        except RuntimeError as exc:
            reading = ClimateReading(None, None, False, str(exc))

        self.last_reading = reading
        self.last_read_at = datetime.now()
        return reading


_sensor: DhtClimateSensor | None = None


def get_sensor() -> DhtClimateSensor:
    global _sensor
    if _sensor is None:
        _sensor = DhtClimateSensor()
    return _sensor


def read_climate() -> ClimateReading:
    return get_sensor().read()


def oled_lines() -> tuple[str, str]:
    return read_climate().oled_lines()


def climate_report() -> str:
    reading = read_climate()
    if not reading.ok or reading.temperature_f is None or reading.humidity_percent is None:
        return "The temperature and humidity sensor is not available right now."
    return f"It is {reading.temperature_f:.1f} degrees Fahrenheit with {reading.humidity_percent:.0f} percent humidity."
