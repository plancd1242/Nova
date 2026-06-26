from __future__ import annotations

import time
from typing import Optional

from nova.config import settings


class LedRing:
    def __init__(self) -> None:
        self.pixel_strip: Optional[object] = None
        self.hardware_ready = False
        self.last_error = ""
        if settings.led_enabled:
            self._try_hardware()

    def _try_hardware(self) -> None:
        try:
            from rpi_ws281x import Color, PixelStrip  # type: ignore

            strip = PixelStrip(
                settings.led_count,
                settings.led_pin,
                brightness=max(0, min(255, settings.led_brightness)),
            )
            strip.begin()
            self.pixel_strip = (strip, Color)
            self.hardware_ready = True
        except Exception as exc:
            self.last_error = str(exc)
            print(f"[LED] hardware unavailable, using text fallback: {self._friendly_error()}")

    def _color_all(self, red: int, green: int, blue: int) -> None:
        if not self.hardware_ready or not self.pixel_strip:
            return
        strip, Color = self.pixel_strip
        for i in range(settings.led_count):
            strip.setPixelColor(i, Color(red, green, blue))
        strip.show()

    def status(self, name: str) -> None:
        colors = {
            "off": (0, 0, 0, "off"),
            "ready": (0, 180, 50, "green ready"),
            "waiting": (2, 2, 6, "very dim waiting"),
            "listening": (20, 80, 255, "blue listening"),
            "thinking": (60, 0, 120, "blue purple thinking"),
            "speaking": (120, 0, 180, "purple speaking"),
            "backup": (180, 180, 180, "white backup"),
            "backup_complete": (0, 180, 50, "green backup complete"),
            "done": (0, 180, 50, "green done"),
            "private": (255, 80, 0, "orange private"),
            "privacy": (255, 80, 0, "orange privacy"),
            "sleeping": (4, 4, 12, "dim sleep"),
            "sleep": (4, 4, 12, "dim sleep"),
            "lockdown": (255, 0, 0, "red lockdown"),
            "warning": (255, 120, 0, "yellow orange warning"),
            "calm": (25, 20, 80, "soft blue purple calm"),
            "party": (120, 0, 180, "rainbow party"),
        }
        red, green, blue, label = colors.get(name, colors["waiting"])
        if self.hardware_ready:
            self._color_all(red, green, blue)
        else:
            print(f"[LED] {label}")

    def flash_done(self) -> None:
        self.status("done")
        time.sleep(0.15)
        self.status("waiting")

    def flash_warning(self, times: int = 4) -> None:
        for _ in range(times):
            self.status("warning")
            time.sleep(0.2)
            self.status("off")
            time.sleep(0.2)
        self.status("waiting")

    def party(self) -> None:
        if not self.hardware_ready:
            print("[LED] rainbow fun colors")
            return
        palette = [(255, 0, 0), (255, 100, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (120, 0, 255)]
        for red, green, blue in palette:
            self._color_all(red, green, blue)
            time.sleep(0.2)
        self.status("waiting")

    def off(self) -> None:
        self.status("off")

    def _friendly_error(self) -> str:
        if "mailbox" in self.last_error.lower() or "operation not permitted" in self.last_error.lower():
            return (
                f"{self.last_error}. WS281x LEDs on GPIO{settings.led_pin} need elevated GPIO/mailbox access. "
                "Run Nova with the virtualenv Python under sudo, for example: sudo .venv/bin/python main.py"
            )
        if "no module named" in self.last_error.lower() or "import" in self.last_error.lower():
            return f"{self.last_error}. Install the LED package in the Python environment running Nova: pip install rpi_ws281x"
        return self.last_error or "unknown LED hardware error"


_ring: LedRing | None = None


def get_ring() -> LedRing:
    global _ring
    if _ring is None:
        _ring = LedRing()
    return _ring


def status(name: str) -> None:
    get_ring().status(name)


def show(name: str) -> None:
    status(name)


def set_mode(name: str) -> None:
    status(name)


def led_status(name: str) -> None:
    status(name)


def off() -> None:
    get_ring().off()


def test_led() -> str:
    ring = get_ring()
    if not settings.led_enabled:
        return "LED ring is disabled in configuration."
    if not ring.hardware_ready:
        detail = ring._friendly_error()
        return (
            "LED ring hardware is not ready. "
            f"{detail} Check GPIO pin, DIN/DOUT direction, LED power, and common ground."
        )
    ring.status("ready")
    return f"LED ring is ready on GPIO{settings.led_pin} with {settings.led_count} LEDs."
