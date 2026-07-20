from __future__ import annotations

from dataclasses import dataclass
import queue
from typing import Any, Callable

from nova.config import settings


@dataclass(frozen=True)
class MicrophoneStatus:
    available: bool
    status: str
    device: str
    message: str


class Microphone:
    """USB microphone helper for local offline voice input.

    Nova does not store microphone recordings by default. Audio chunks are
    streamed directly to the recognizer and discarded.
    """

    def __init__(self) -> None:
        self.sample_rate = settings.voice_sample_rate
        self.device = settings.audio_input_device or None

    def is_available(self) -> bool:
        return self.status().available

    def status(self) -> MicrophoneStatus:
        if not settings.microphone_enabled:
            return MicrophoneStatus(False, "Disabled", self.device or "Default", "Microphone input is disabled.")
        try:
            import sounddevice as sd  # type: ignore

            devices = sd.query_devices()
            selected = self._selected_device(devices)
            if selected is None:
                return MicrophoneStatus(False, "Missing", self.device or "Default", "No input microphone was found.")
            return MicrophoneStatus(True, "Available", str(selected.get("name", self.device or "Default")), "Microphone is available.")
        except ImportError:
            return MicrophoneStatus(False, "Not Installed", self.device or "Default", "sounddevice is not installed.")
        except Exception as exc:
            return MicrophoneStatus(False, "Unavailable", self.device or "Default", f"Microphone check failed: {type(exc).__name__}.")

    def list_devices(self) -> str:
        try:
            import sounddevice as sd  # type: ignore

            rows: list[str] = []
            for index, device in enumerate(sd.query_devices()):
                inputs = int(device.get("max_input_channels", 0) or 0)
                if inputs > 0:
                    rows.append(f"{index}: {device.get('name', 'Unknown')} ({inputs} input channel{'s' if inputs != 1 else ''})")
            if not rows:
                return "No microphone input devices were found."
            return "Microphones: " + "; ".join(rows)
        except ImportError:
            return "sounddevice is not installed."
        except Exception as exc:
            return f"Could not list microphones: {type(exc).__name__}."

    def stream(self, on_audio: Callable[[bytes], None], stop_flag: Callable[[], bool]) -> None:
        import sounddevice as sd  # type: ignore

        audio_queue: queue.Queue[bytes] = queue.Queue()

        def callback(indata: bytes, frames: int, time_info: object, status: object) -> None:
            _ = frames, time_info, status
            audio_queue.put(bytes(indata))

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=4000,
            dtype="int16",
            channels=1,
            device=self._device_arg(),
            callback=callback,
        ):
            while not stop_flag():
                try:
                    on_audio(audio_queue.get(timeout=0.2))
                except queue.Empty:
                    continue

    def _device_arg(self) -> int | str | None:
        if not self.device:
            return None
        try:
            return int(self.device)
        except ValueError:
            return self.device

    def _selected_device(self, devices: Any) -> dict[str, Any] | None:
        if self.device:
            try:
                device = devices[int(self.device)]
                return device if int(device.get("max_input_channels", 0) or 0) > 0 else None
            except (ValueError, IndexError, TypeError):
                needle = self.device.lower()
                for device in devices:
                    if needle in str(device.get("name", "")).lower() and int(device.get("max_input_channels", 0) or 0) > 0:
                        return device
                return None
        for device in devices:
            if int(device.get("max_input_channels", 0) or 0) > 0:
                return device
        return None


def status() -> MicrophoneStatus:
    return Microphone().status()


def list_devices() -> str:
    return Microphone().list_devices()
