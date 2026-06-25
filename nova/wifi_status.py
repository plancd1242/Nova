from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class WifiReading:
    status: str
    signal: str
    percent: int | None = None

    @property
    def display(self) -> str:
        return self.signal if self.signal != "N/A" else "N/A"


def read_wifi() -> WifiReading:
    try:
        if shutil.which("iwconfig"):
            result = subprocess.run(
                ["iwconfig"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1,
            )
            quality = _extract_quality(result.stdout)
            if quality is not None:
                return WifiReading("Connected", _signal_label(quality), quality)
            if "ESSID:off/any" in result.stdout:
                return WifiReading("Offline", "No connection", 0)

        if shutil.which("nmcli"):
            result = subprocess.run(
                ["nmcli", "-t", "-f", "ACTIVE,SIGNAL", "dev", "wifi"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1,
            )
            for line in result.stdout.splitlines():
                active, _, signal = line.partition(":")
                if active == "yes":
                    percent = int(signal)
                    return WifiReading("Connected", _signal_label(percent), percent)
            return WifiReading("Offline", "No connection", 0)
    except Exception:
        pass
    return WifiReading("Unsupported", "N/A", None)


def _extract_quality(text: str) -> int | None:
    match = re.search(r"Quality=(\d+)/(\d+)", text)
    if not match:
        return None
    return int((int(match.group(1)) / max(1, int(match.group(2)))) * 100)


def _signal_label(percent: int) -> str:
    if percent <= 0:
        return "No connection"
    if percent < 35:
        return "Weak"
    if percent < 70:
        return "Medium"
    return "Strong"
