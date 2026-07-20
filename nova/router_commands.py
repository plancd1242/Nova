from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouterCommand:
    action: str
    guest_key: str | None = None
    enabled: bool | None = None
    confirmed: bool = False


def parse_router_command(text: str) -> RouterCommand | None:
    lower = _clean(text)
    if not _looks_router_related(lower):
        return None

    if _speed_test(lower):
        return RouterCommand("speed_test")
    if _inspection(lower):
        return RouterCommand("inspect")
    if _status(lower):
        return RouterCommand("status")
    if _smart_connect_status(lower):
        return RouterCommand("status")
    if _ofdma_status(lower):
        return RouterCommand("status")

    guest_key = _guest_key(lower)
    if guest_key:
        if _turn_on(lower):
            return RouterCommand("guest", guest_key=guest_key, enabled=True)
        if _turn_off(lower):
            return RouterCommand("guest", guest_key=guest_key, enabled=False)
        return RouterCommand("status")

    if _confirmed_wifi_off(lower):
        return RouterCommand("main_wifi_off", confirmed=True)
    if _main_wifi_off(lower):
        return RouterCommand("main_wifi_off", confirmed=_confirmed_wifi_off(lower))
    if _main_wifi_on(lower):
        return RouterCommand("main_wifi_on")

    return None


def _looks_router_related(text: str) -> bool:
    words = [
        "wi-fi",
        "wifi",
        "wireless",
        "guest network",
        "guest wi-fi",
        "guest wifi",
        "router",
        "smart connect",
        "ofdma",
        "speed test",
        "internet speed",
        "download speed",
        "network speed",
    ]
    return any(word in text for word in words)


def _speed_test(text: str) -> bool:
    return any(
        phrase in text
        for phrase in [
            "do a speed test",
            "run a speed test",
            "speed test",
            "test the internet speed",
            "check our internet speed",
            "how fast is the wi-fi",
            "how fast is the wifi",
            "check the network speed",
            "what is our download speed",
            "download speed",
        ]
    )


def _inspection(text: str) -> bool:
    return any(phrase in text for phrase in ["inspect router", "inspect router page", "discover router controls"])


def _status(text: str) -> bool:
    return any(
        phrase in text
        for phrase in [
            "is wi-fi on",
            "is wifi on",
            "is wi-fi off",
            "is wifi off",
            "check the wi-fi status",
            "check the wifi status",
            "which wireless bands are on",
            "which guest wi-fi networks are enabled",
            "which guest wifi networks are enabled",
            "check guest network",
            "router status",
            "wireless status",
        ]
    )


def _smart_connect_status(text: str) -> bool:
    return "smart connect" in text and any(word in text for word in ["on", "off", "enabled", "status", "check", "is"])


def _ofdma_status(text: str) -> bool:
    return "ofdma" in text and any(word in text for word in ["on", "off", "enabled", "status", "check", "is"])


def _turn_on(text: str) -> bool:
    return any(word in text for word in ["turn on", "enable", "restore", "back on", "start"])


def _turn_off(text: str) -> bool:
    return any(word in text for word in ["turn off", "disable", "shut down", "switch off", "stop"])


def _main_wifi_off(text: str) -> bool:
    return _turn_off(text) and any(
        phrase in text
        for phrase in [
            "the wi-fi",
            "the wifi",
            "all wireless bands",
            "main wi-fi",
            "main wifi",
            "normal wi-fi",
            "normal wifi",
            "wireless networks",
        ]
    )


def _main_wifi_on(text: str) -> bool:
    return _turn_on(text) and any(
        phrase in text
        for phrase in [
            "the wi-fi",
            "the wifi",
            "wireless networks",
            "main wi-fi",
            "main wifi",
            "normal wi-fi",
            "normal wifi",
        ]
    )


def _confirmed_wifi_off(text: str) -> bool:
    return any(phrase in text for phrase in ["confirm wi-fi off", "confirm wifi off", "yes turn off wi-fi", "yes turn off wifi"])


def _guest_key(text: str) -> str | None:
    if "guest" not in text:
        return None
    if any(phrase in text for phrase in ["network one", "network 1", "first guest", "2.4 gigahertz guest", "2.4 ghz guest", "2.4ghz guest", "2.4g guest"]):
        return "guest_24"
    if any(
        phrase in text
        for phrase in [
            "network two",
            "network 2",
            "second guest",
            "first 5 gigahertz guest",
            "5 gigahertz dash one",
            "5 ghz dash one",
            "5g-1 guest",
            "5ghz-1 guest",
            "5 ghz-1 guest",
        ]
    ):
        return "guest_5g1"
    if any(
        phrase in text
        for phrase in [
            "network three",
            "network 3",
            "third guest",
            "second 5 gigahertz guest",
            "5 gigahertz dash two",
            "5 ghz dash two",
            "5g-2 guest",
            "5ghz-2 guest",
            "5 ghz-2 guest",
        ]
    ):
        return "guest_5g2"
    return None


def _clean(text: str) -> str:
    return " ".join(text.lower().replace("hey nova", "").replace(",", " ").replace("?", " ").split())
