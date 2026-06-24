from __future__ import annotations

import time
from typing import Optional

from nova.config import settings


class LedRing:
    def __init__(self) -> None:
        self.pixel_strip: Optional[object] = None
        self.hardware_ready = False
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
            print(f"[LED] hardware unavailable, using text fallback: {exc}")

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
            "waiting": (2, 2, 6, "very dim waiting"),
            "listening": (20, 80, 255, "blue listening"),
            "thinking": (60, 0, 120, "blue purple thinking"),
            "done": (0, 180, 50, "green done"),
            "private": (160, 0, 0, "red private"),
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

