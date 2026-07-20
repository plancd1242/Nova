from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nova.router_commands import parse_router_command
from nova.router_status import RouterStateStore
from nova.storage import JsonStore


class RouterCommandTests(unittest.TestCase):
    def test_main_wifi_off_requires_confirmation_flag(self) -> None:
        command = parse_router_command("Hey Nova, turn off the Wi-Fi.")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "main_wifi_off")
        self.assertFalse(command.confirmed)

    def test_main_wifi_off_confirmation(self) -> None:
        command = parse_router_command("Confirm Wi-Fi off.")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "main_wifi_off")
        self.assertTrue(command.confirmed)

    def test_guest_network_mapping(self) -> None:
        cases = {
            "Turn on guest network one.": ("guest_24", True),
            "Disable the 5 gigahertz dash one guest network.": ("guest_5g1", False),
            "Enable 5G-2 guest Wi-Fi.": ("guest_5g2", True),
        }
        for phrase, expected in cases.items():
            with self.subTest(phrase=phrase):
                command = parse_router_command(phrase)
                self.assertIsNotNone(command)
                self.assertEqual(command.action, "guest")
                self.assertEqual((command.guest_key, command.enabled), expected)

    def test_speed_test_command(self) -> None:
        command = parse_router_command("What is our download speed?")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "speed_test")


class RouterStateTests(unittest.TestCase):
    def test_state_does_not_store_password(self) -> None:
        with TemporaryDirectory() as tmp:
            store = JsonStore(Path(tmp))
            router_state = RouterStateStore(store)
            router_state.save_radios({"main_24": True}, "unit_test")
            router_state.save_speed_test({"download_mbps": "100", "upload_mbps": "20", "ping_ms": "10"})
            text = (Path(tmp) / "router_state.json").read_text(encoding="utf-8").lower()
            self.assertNotIn("password", text)
            self.assertNotIn("cookie", text)
            self.assertNotIn("token", text)


if __name__ == "__main__":
    unittest.main()
