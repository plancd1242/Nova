from __future__ import annotations

from dataclasses import dataclass
import threading
import time

from nova.config import settings
from nova.storage import JsonStore


@dataclass(frozen=True)
class VolumeState:
    level: int
    saved_level: int
    muted: bool
    status: str
    hardware: str
    mute_button: str
    minimum: int
    maximum: int

    @property
    def percent(self) -> int:
        span = max(1, self.maximum - self.minimum)
        return max(0, min(100, int(((self.level - self.minimum) / span) * 100)))

    @property
    def bar_percent(self) -> int:
        span = max(1, self.maximum - self.minimum)
        shown_level = self.saved_level if self.muted else self.level
        return max(0, min(100, int(((shown_level - self.minimum) / span) * 100)))

    @property
    def display(self) -> str:
        return "Muted" if self.muted else f"{self.percent}%"


class VolumeManager:
    def __init__(self, store: JsonStore | None = None) -> None:
        self.store = store or JsonStore()
        self._stop_monitor = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._ensure_settings()

    def state(self) -> VolumeState:
        data = self.store.read("settings.json")
        level = self._clamp(int(data.get("volume_level", settings.volume_default)))
        saved_level = self._clamp(int(data.get("volume_saved_level", level or settings.volume_default)))
        muted = bool(data.get("volume_muted", False))
        return VolumeState(
            level=level,
            saved_level=saved_level,
            muted=muted,
            status="Enabled" if settings.volume_enabled else "Disabled",
            hardware=self.hardware_status(),
            mute_button=self.mute_button_status(),
            minimum=settings.volume_min,
            maximum=settings.volume_max,
        )

    def set_level(self, level: int) -> str:
        if not settings.volume_enabled:
            return "Volume control is disabled."
        level = self._clamp(level)
        data = self.store.read("settings.json")
        data["volume_level"] = level
        data["volume_saved_level"] = level
        data["volume_muted"] = False
        self.store.write("settings.json", data)
        return f"Volume set to {self.state().display}."

    def adjust(self, delta: int) -> str:
        return self.set_level(self.state().level + delta)

    def mute(self) -> str:
        data = self.store.read("settings.json")
        current = self._clamp(int(data.get("volume_level", settings.volume_default)))
        if current > settings.volume_min:
            data["volume_saved_level"] = current
        data["volume_muted"] = True
        self.store.write("settings.json", data)
        return "Volume muted."

    def unmute(self) -> str:
        data = self.store.read("settings.json")
        level = self._clamp(int(data.get("volume_saved_level", settings.volume_default)))
        if level <= settings.volume_min:
            level = self._clamp(settings.volume_default)
        data["volume_level"] = level
        data["volume_muted"] = False
        self.store.write("settings.json", data)
        return f"Volume unmuted at {self.state().display}."

    def toggle_mute_from_button(self) -> str:
        if not settings.volume_rotary_mute_enabled:
            return "Rotary mute button is disabled."
        if not settings.volume_rotary_sw_pin:
            return "Rotary mute button is not configured."
        return self.toggle_mute()

    def toggle_mute(self) -> str:
        if self.state().muted:
            return self.unmute()
        return self.mute()

    def hardware_status(self) -> str:
        if not settings.volume_hardware_enabled:
            return "Not Installed"
        try:
            import board  # type: ignore
            import digitalio  # type: ignore

            getattr(board, settings.volume_rotary_clk_pin)
            getattr(board, settings.volume_rotary_dt_pin)
            _ = digitalio
            return "Configured"
        except ImportError:
            return "Not Installed"
        except Exception:
            return "Missing"

    def mute_button_status(self) -> str:
        if not settings.volume_rotary_mute_enabled:
            return "Disabled"
        if not settings.volume_rotary_sw_pin:
            return "Not Configured"
        if not settings.volume_hardware_enabled:
            return "Not Installed"
        try:
            import board  # type: ignore
            import digitalio  # type: ignore

            getattr(board, settings.volume_rotary_sw_pin)
            _ = digitalio
            return "Configured"
        except ImportError:
            return "Not Installed"
        except Exception:
            return "Missing"

    def start_hardware_monitor(self) -> str:
        if not settings.volume_hardware_enabled:
            return "Volume hardware is disabled."
        if not settings.volume_rotary_mute_enabled:
            return "Rotary mute button is disabled."
        if not settings.volume_rotary_sw_pin:
            return "Rotary mute button is not configured."
        if self._monitor_thread and self._monitor_thread.is_alive():
            return "Rotary mute button monitor is already running."

        try:
            import board  # type: ignore
            import digitalio  # type: ignore

            pin = getattr(board, settings.volume_rotary_sw_pin)
            button = digitalio.DigitalInOut(pin)
            button.direction = digitalio.Direction.INPUT
            try:
                button.pull = digitalio.Pull.UP
            except Exception:
                pass
        except ImportError:
            return "Rotary mute button monitor is not installed."
        except Exception:
            return "Rotary mute button is missing."

        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(
            target=self._button_loop,
            args=(button,),
            daemon=True,
            name="nova-volume-button",
        )
        self._monitor_thread.start()
        return "Rotary mute button monitor started."

    def stop_hardware_monitor(self) -> None:
        self._stop_monitor.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)
        self._monitor_thread = None

    def _button_loop(self, button: object) -> None:
        was_pressed = False
        while not self._stop_monitor.wait(0.03):
            try:
                pressed = not bool(button.value)
                if pressed and not was_pressed:
                    self.toggle_mute()
                    self._refresh_oled()
                was_pressed = pressed
                if pressed:
                    time.sleep(0.18)
            except Exception:
                break

    def _refresh_oled(self) -> None:
        try:
            from nova import oled

            oled.refresh()
        except Exception:
            pass

    def test(self) -> str:
        state = self.state()
        return (
            f"Volume: {state.display}; bar: {state.bar_percent}%; "
            f"hardware: {state.hardware}; mute button: {state.mute_button}; range: {state.minimum}-{state.maximum}."
        )

    def _ensure_settings(self) -> None:
        data = self.store.read("settings.json")
        changed = False
        if "volume_level" not in data:
            data["volume_level"] = self._clamp(settings.volume_default)
            changed = True
        if "volume_muted" not in data:
            data["volume_muted"] = False
            changed = True
        if "volume_saved_level" not in data:
            data["volume_saved_level"] = self._clamp(int(data.get("volume_level", settings.volume_default)))
            changed = True
        if changed:
            self.store.write("settings.json", data)

    def _clamp(self, value: int) -> int:
        low = min(settings.volume_min, settings.volume_max)
        high = max(settings.volume_min, settings.volume_max)
        return max(low, min(high, int(value)))


_manager: VolumeManager | None = None


def get_volume_manager() -> VolumeManager:
    global _manager
    if _manager is None:
        _manager = VolumeManager()
    return _manager
