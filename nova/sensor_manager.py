from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorSnapshot:
    temperature: str
    humidity: str
    wifi: str
    voltage: str
    light: str


class SensorManager:
    def snapshot(self) -> SensorSnapshot:
        return SensorSnapshot(
            temperature=self._temperature(),
            humidity=self._humidity(),
            wifi=self._wifi(),
            voltage=self._voltage(),
            light=self._light(),
        )

    def status_report(self) -> str:
        snap = self.snapshot()
        return (
            f"Temperature: {snap.temperature}; Humidity: {snap.humidity}; "
            f"Wi-Fi: {snap.wifi}; Voltage: {snap.voltage}; Light: {snap.light}."
        )

    def _temperature(self) -> str:
        try:
            from nova import climate

            reading = climate.read_climate()
            if reading.ok and reading.temperature_f is not None:
                return f"{reading.temperature_f:.1f}F"
        except Exception:
            pass
        return "N/A"

    def _humidity(self) -> str:
        try:
            from nova import climate

            reading = climate.read_climate()
            if reading.ok and reading.humidity_percent is not None:
                return f"{reading.humidity_percent:.0f}%"
        except Exception:
            pass
        return "N/A"

    def _wifi(self) -> str:
        try:
            from nova.wifi_status import read_wifi

            return read_wifi().display
        except Exception:
            return "N/A"

    def _voltage(self) -> str:
        try:
            from nova.voltage_sensor import read_voltage

            reading = read_voltage()
            return reading.display if reading.status == "Connected" else "N/A"
        except Exception:
            return "N/A"

    def _light(self) -> str:
        try:
            from nova.light_sensor import read_light

            reading = read_light()
            return reading.display if reading.status == "Connected" else "N/A"
        except Exception:
            return "N/A"


_manager: SensorManager | None = None


def get_sensor_manager() -> SensorManager:
    global _manager
    if _manager is None:
        _manager = SensorManager()
    return _manager
