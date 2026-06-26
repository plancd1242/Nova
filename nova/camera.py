from __future__ import annotations

from dataclasses import dataclass

from nova.config import settings


@dataclass(frozen=True)
class CameraStatus:
    status: str
    message: str


def status() -> CameraStatus:
    if not settings.camera_enabled and not settings.lockdown_camera_enabled:
        return CameraStatus("Disabled", "Camera is disabled.")
    try:
        import picamera2  # type: ignore  # noqa: F401

        return CameraStatus("Available", "Camera library is installed.")
    except ImportError:
        return CameraStatus("Not Installed", "Install picamera2 on Raspberry Pi to use the camera.")
    except Exception as exc:
        return CameraStatus("Missing", f"Camera is unavailable: {exc}")


def test_camera() -> str:
    current = status()
    return f"Camera: {current.status}. {current.message}"
