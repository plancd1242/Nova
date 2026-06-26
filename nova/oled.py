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
    "backup_complete": OledStatus("backup_complete", "  :)", "Backup Complete", ("Saved",)),
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
        self._animation_frame = 0
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

            self._draw_screen(draw, font, screen, lines)

            self.device.image(image)
            self.device.show()

    def _draw_screen(self, draw: object, font: object, screen: OledStatus, lines: tuple[str, ...]) -> None:
        if screen.mode == "lockdown":
            self._draw_lockdown(draw, font)
        elif screen.mode == "sleeping":
            self._draw_sleep(draw, font)
        elif screen.mode == "private":
            self._draw_privacy(draw, font)
        elif screen.mode == "backup":
            self._draw_backup(draw, font, complete=False)
        elif screen.mode == "backup_complete":
            self._draw_backup(draw, font, complete=True)
        else:
            self._draw_dashboard(draw, font, screen, lines)

    def _draw_dashboard(self, draw: object, font: object, screen: OledStatus, lines: tuple[str, ...]) -> None:
        metrics = self._metrics()
        self._draw_face(draw, x=3, y=1, mood=screen.mode)
        draw.text((24, 1), datetime.now().strftime("%I:%M %p").lstrip("0"), font=font, fill=255)
        self._draw_wifi_icon(draw, 111, 2, metrics["wifi"])
        draw.line((0, 12, settings.oled_width - 1, 12), fill=255)

        draw.text((0, 15), f"T:{metrics['temp']}", font=font, fill=255)
        draw.text((68, 15), f"H:{metrics['humidity']}", font=font, fill=255)
        draw.text((0, 27), f"WiFi:{metrics['wifi']}", font=font, fill=255)
        draw.text((68, 27), f"V:{metrics['voltage']}", font=font, fill=255)
        draw.text((0, 39), f"Light:{metrics['light']}", font=font, fill=255)

        if lines:
            detail = str(lines[0])
            if detail and "N/A" not in detail and not detail.startswith(("Temp:", "Humidity:")):
                draw.text((68, 39), detail[:10], font=font, fill=255)

        draw.line((0, 52, settings.oled_width - 1, 52), fill=255)
        draw.text((0, 54), f"Mode:{self._mode_label(screen.mode)}"[:12], font=font, fill=255)
        self._draw_volume_indicator(draw, 70, 54)

    def _draw_backup(self, draw: object, font: object, complete: bool) -> None:
        self._draw_face(draw, x=4, y=2, mood="backup_complete" if complete else "backup")
        draw.text((30, 3), "Backup Complete" if complete else "Backing Up", font=font, fill=255)
        draw.line((0, 14, settings.oled_width - 1, 14), fill=255)
        if complete:
            draw.rectangle((50, 24, 78, 44), outline=255)
            draw.line((56, 34, 64, 41), fill=255)
            draw.line((64, 41, 74, 27), fill=255)
            draw.text((20, 52), "Backup Complete", font=font, fill=255)
            return

        frame_y = 20 + (self._animation_frame % 4) * 4
        self._animation_frame += 1
        draw.rectangle((48, 42, 80, 50), outline=255)
        draw.line((64, frame_y, 64, frame_y + 16), fill=255)
        draw.line((58, frame_y + 10, 64, frame_y + 16), fill=255)
        draw.line((70, frame_y + 10, 64, frame_y + 16), fill=255)
        draw.text((20, 53), "Saving Nova data", font=font, fill=255)

    def _draw_lockdown(self, draw: object, font: object) -> None:
        draw.rectangle((0, 0, settings.oled_width - 1, settings.oled_height - 1), outline=255)
        draw.rectangle((8, 22, 28, 42), outline=255)
        draw.arc((10, 8, 26, 28), 180, 360, fill=255)
        draw.polygon([(44, 42), (62, 10), (80, 42)], outline=255)
        draw.text((58, 23), "!", font=font, fill=255)
        draw.rectangle((92, 20, 118, 40), outline=255)
        draw.rectangle((98, 15, 111, 20), outline=255)
        draw.text((18, 51), "LOCKDOWN MODE", font=font, fill=255)

    def _draw_sleep(self, draw: object, font: object) -> None:
        self._draw_face(draw, x=6, y=5, mood="sleeping")
        draw.text((38, 8), "Zzz", font=font, fill=255)
        draw.text((18, 30), "Sleep Mode", font=font, fill=255)
        draw.text((12, 46), "Quiet operation", font=font, fill=255)

    def _draw_privacy(self, draw: object, font: object) -> None:
        self._draw_face(draw, x=4, y=3, mood="private")
        draw.rectangle((47, 23, 80, 48), outline=255)
        draw.arc((53, 10, 74, 34), 180, 360, fill=255)
        draw.text((30, 53), "Privacy Mode", font=font, fill=255)

    def _draw_face(self, draw: object, x: int, y: int, mood: str) -> None:
        draw.ellipse((x, y, x + 16, y + 10), outline=255)
        if mood == "sleeping":
            draw.line((x + 4, y + 4, x + 7, y + 4), fill=255)
            draw.line((x + 10, y + 4, x + 13, y + 4), fill=255)
            draw.arc((x + 5, y + 5, x + 12, y + 9), 0, 180, fill=255)
        elif mood in {"thinking", "private"}:
            draw.point((x + 5, y + 4), fill=255)
            draw.point((x + 11, y + 4), fill=255)
            draw.line((x + 6, y + 8, x + 11, y + 8), fill=255)
        elif mood == "lockdown":
            draw.text((x + 5, y + 1), "!", fill=255)
        else:
            draw.point((x + 5, y + 4), fill=255)
            draw.point((x + 11, y + 4), fill=255)
            draw.arc((x + 5, y + 4, x + 12, y + 9), 0, 180, fill=255)

    def _draw_wifi_icon(self, draw: object, x: int, y: int, status: str) -> None:
        bars = {"Weak": 1, "Medium": 2, "Strong": 3}.get(status, 0)
        for index in range(3):
            height = 3 + index * 3
            left = x + index * 5
            top = y + 10 - height
            if index < bars:
                draw.rectangle((left, top, left + 3, y + 10), fill=255)
            else:
                draw.rectangle((left, top, left + 3, y + 10), outline=255)

    def _draw_volume_indicator(self, draw: object, x: int, y: int) -> None:
        try:
            from nova.volume import get_volume_manager

            volume = get_volume_manager().state()
            percent = volume.bar_percent
        except Exception:
            percent = 0
            volume = None

        speaker_x = x
        draw.rectangle((speaker_x, y + 3, speaker_x + 3, y + 8), outline=255)
        draw.polygon([(speaker_x + 4, y + 3), (speaker_x + 9, y), (speaker_x + 9, y + 11), (speaker_x + 4, y + 8)], outline=255)
        if volume is not None and volume.muted:
            draw.line((speaker_x + 11, y + 2, speaker_x + 17, y + 9), fill=255)
            draw.line((speaker_x + 17, y + 2, speaker_x + 11, y + 9), fill=255)

        bar_x = x + 22
        bar_y = y + 3
        bar_w = 35
        draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + 7), outline=255)
        fill_w = int((bar_w - 2) * max(0, min(100, percent)) / 100)
        if fill_w > 0:
            draw.rectangle((bar_x + 1, bar_y + 1, bar_x + fill_w, bar_y + 6), fill=255)

    def _metrics(self) -> dict[str, str]:
        temp = "N/A"
        humidity = "N/A"
        try:
            from nova import climate

            reading = climate.read_climate()
            if reading.ok and reading.temperature_f is not None and reading.humidity_percent is not None:
                temp = f"{reading.temperature_f:.1f}F"
                humidity = f"{reading.humidity_percent:.0f}%"
        except Exception:
            pass

        try:
            from nova.sensor_manager import get_sensor_manager

            snapshot = get_sensor_manager().snapshot()
            wifi = snapshot.wifi
            voltage = snapshot.voltage
            light = snapshot.light
        except Exception:
            wifi = "N/A"
            voltage = "N/A"
            light = "N/A"
        return {"temp": temp, "humidity": humidity, "wifi": wifi, "voltage": voltage, "light": light}

    def _mode_label(self, mode: str) -> str:
        labels = {
            "off": "Offline",
            "ready": "Ready",
            "waiting": "Ready",
            "listening": "Listening",
            "thinking": "Thinking",
            "speaking": "Speaking",
            "done": "Ready",
            "backup": "Backup",
            "backup_complete": "Backup Complete",
            "private": "Privacy",
            "lockdown": "Lockdown",
            "sleeping": "Sleep",
            "warning": "Warning",
        }
        return labels.get(mode, mode.title())

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
                lines = ("Temp: N/A", "Humidity: N/A", *lines)
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
