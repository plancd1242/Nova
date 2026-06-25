from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorValue:
    label: str
    value: str
    ok: bool = False


def wifi_status() -> SensorValue:
    try:
        from nova.wifi_status import read_wifi

        reading = read_wifi()
        return SensorValue("Wi-Fi", reading.display, reading.status == "Connected")
    except Exception:
        return SensorValue("Wi-Fi", "N/A", False)


def light_level() -> SensorValue:
    try:
        from nova.light_sensor import read_light

        reading = read_light()
        return SensorValue("Light", reading.display, reading.status == "Connected")
    except Exception:
        return SensorValue("Light", "N/A", False)


def voltage() -> SensorValue:
    try:
        from nova.voltage_sensor import read_voltage

        reading = read_voltage()
        return SensorValue("Volt", reading.display, reading.status == "Connected")
    except Exception:
        return SensorValue("Volt", "N/A", False)
