from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import threading
from typing import Optional

from nova.config import settings


@dataclass(frozen=True)
class OledStatus:
    mode: str
    face: str
    title: str
    lines: tuple[str, ...]


STATUS_SCREENS: dict[str, OledStatus] = {
    "off": OledStatus("off", "  --", "Nova Offline", ("",)),
    "ready": OledStatus("ready", "  :)", "Ready", ("Awaiting command",)),
    "waiting": OledStatus("waiting", "  :)", "Ready", ("Awaiting command",)),
    "listening": OledStatus("listening", "  :o", "Listening", ("Type or speak",)),
    "thinking": OledStatus("thinking", "  :|", "Thinking", ("Working...",)),
    "speaking": OledStatus("speaking", "  :D", "Speaking", ("Answering",)),
    "done": OledStatus("done", "  :)", "Ready", ("Done",)),
    "backup": OledStatus("backup", " [ ]", "Backing Up", ("Saving data",)),
    "private": OledStatus("private", "  -_-", "Privacy Mode", ("Reduced activity",)),
    "lockdown": OledStatus("lockdown", "  !!", "LOCKDOWN MODE", ("Security active",)),
    "sleeping": OledStatus("sleeping", "  zz", "Sleeping", ("Quiet mode",)),
    "warning": OledStatus("warning", "  !!", "Warning", ("Check Nova",)),
}


class OledDisplay:
    def __init__(self) -> None:
        self.device: Optional[object] = None
        self.image_tools: Optional[tuple[object, object, object]] = None
        self.hardware_ready = False
        self.current_mode = "ready"
        self.current_extra_lines: tuple[str, ...] | None = None
        self._lock = threading.Lock()
        self._stop_refresh = threading.Event()
        self._refresh_thread: threading.Thread | None = None
        if settings.oled_enabled:
            self._try_hardware()

    def _try_hardware(self) -> None:
        try:
            import board  # type: ignore
            import busio  # type: ignore
            import adafruit_ssd1306  # type: ignore
            from PIL import Image, ImageDraw, ImageFont  # type: ignore

            i2c = busio.I2C(board.SCL, board.SDA)
            self.device = adafruit_ssd1306.SSD1306_I2C(
                settings.oled_width,
                settings.oled_height,
                i2c,
                addr=settings.oled_i2c_address,
            )
            self.image_tools = (Image, ImageDraw, ImageFont)
            self.hardware_ready = True
            self.clear()
        except Exception as exc:
            print(f"[OLED] hardware unavailable, using text fallback: {exc}")

    def clear(self) -> None:
        if not self.hardware_ready or self.device is None:
            print("[OLED] clear")
            return
        with self._lock:
            self.device.fill(0)
            self.device.show()

    def status(self, mode: str, extra_lines: list[str] | tuple[str, ...] | None = None) -> None:
        self.current_mode = mode
        self.current_extra_lines = tuple(extra_lines) if extra_lines else None
        self._draw(mode, self.current_extra_lines, print_fallback=True)

    def refresh(self) -> None:
        self._draw(self.current_mode, self.current_extra_lines, print_fallback=False)

    def start_auto_refresh(self, refresh_seconds: int | None = None) -> None:
        if not settings.oled_enabled or not self.hardware_ready:
            return
        if self._refresh_thread and self._refresh_thread.is_alive():
            return

        interval = max(1, refresh_seconds or settings.oled_refresh_seconds)
        self._stop_refresh.clear()
        self._refresh_thread = threading.Thread(
            target=self._refresh_loop,
            args=(interval,),
            daemon=True,
            name="nova-oled-refresh",
        )
        self._refresh_thread.start()

    def stop_auto_refresh(self) -> None:
        self._stop_refresh.set()
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._refresh_thread.join(timeout=1)
        self._refresh_thread = None

    def _refresh_loop(self, interval: int) -> None:
        while not self._stop_refresh.wait(interval):
            self.refresh()

    def _draw(
        self,
        mode: str,
        extra_lines: list[str] | tuple[str, ...] | None = None,
        print_fallback: bool = True,
    ) -> None:
        screen = STATUS_SCREENS.get(mode, STATUS_SCREENS["ready"])
        lines = self._build_lines(screen, extra_lines)

        if not self.hardware_ready or self.device is None or self.image_tools is None:
            if print_fallback:
                printable = " | ".join(line for line in (screen.title, *lines) if line)
                print(f"[OLED] {printable}")
            return

        Image, ImageDraw, ImageFont = self.image_tools
        with self._lock:
            image = Image.new("1", (settings.oled_width, settings.oled_height))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()

            draw.text((0, 0), screen.face, font=font, fill=255)
            draw.text((42, 0), datetime.now().strftime("%I:%M %p").lstrip("0"), font=font, fill=255)
            draw.line((0, 12, settings.oled_width - 1, 12), fill=255)
            draw.text((0, 16), screen.title[:21], font=font, fill=255)

            y = 29
            for line in lines[:4]:
                draw.text((0, y), str(line)[:21], font=font, fill=255)
                y += 9

            self.device.image(image)
            self.device.show()

    def _build_lines(
        self,
        screen: OledStatus,
        extra_lines: list[str] | tuple[str, ...] | None = None,
    ) -> tuple[str, ...]:
        lines = tuple(extra_lines) if extra_lines else screen.lines
        if screen.mode in {"ready", "waiting", "done", "thinking"}:
            try:
                from nova import climate

                lines = (*climate.oled_lines(), *lines)
            except Exception:
                lines = ("Temp: --.- F", "Humidity: -- %", *lines)
        return lines[:4]


_display: OledDisplay | None = None


def get_display() -> OledDisplay:
    global _display
    if _display is None:
        _display = OledDisplay()
    return _display


def status(mode: str, extra_lines: list[str] | tuple[str, ...] | None = None) -> None:
    get_display().status(mode, extra_lines)


def show(mode: str, extra_lines: list[str] | tuple[str, ...] | None = None) -> None:
    status(mode, extra_lines)


def set_mode(mode: str) -> None:
    status(mode)


def clear() -> None:
    get_display().clear()


def refresh() -> None:
    get_display().refresh()


def start_auto_refresh(refresh_seconds: int | None = None) -> None:
    get_display().start_auto_refresh(refresh_seconds)


def stop_auto_refresh() -> None:
    get_display().stop_auto_refresh()
