from __future__ import annotations


class Diagnostics:
    def run(self, name: str) -> str:
        name = name.strip().lower()
        if name in {"oled", "oled status"}:
            return self.oled_status()
        if name in {"led", "led ring", "light ring"}:
            return self.led()
        if name == "backup screen":
            return self.backup_screen()
        if name == "sleep mode":
            return self.sleep_mode()
        if name == "privacy mode":
            return self.privacy_mode()
        if name == "lockdown mode":
            return self.lockdown_mode()
        if name == "notifications":
            return self.notifications()
        if name == "camera":
            return self.camera()
        if name in {"motion sensor", "pir", "pir motion"}:
            return self.motion()
        if name in {"ultrasonic sensor", "ultrasonic"}:
            return self.ultrasonic()
        if name == "climate":
            return self.climate()
        if name == "light sensor":
            return self.light()
        if name == "voltage sensor":
            return self.voltage()
        if name in {"volume", "volume dial", "volume control"}:
            return self.volume()
        if name in {"volume button", "rotary button", "rotary mute", "sw button"}:
            return self.volume_button()
        if name == "volume mute":
            return self.volume_mute()
        if name == "voice login":
            return self.voice_login()
        if name in {"accounts", "account system"}:
            return self.accounts()
        return "Unknown diagnostic test."

    def oled_status(self) -> str:
        try:
            from nova.oled_status import status_summary

            summary = status_summary()
            return f"OLED: {'Connected' if summary.available else 'Fallback'}; mode {summary.mode}."
        except Exception as exc:
            return f"OLED: N/A. {exc}"

    def backup_screen(self) -> str:
        try:
            from nova import oled

            oled.status("backup", ("Diagnostic",))
            oled.status("backup_complete", ("Backup Complete",))
            return "Backup OLED screen test complete."
        except Exception as exc:
            return f"Backup screen test unavailable: {exc}"

    def led(self) -> str:
        try:
            from nova import led

            return led.test_led()
        except Exception as exc:
            return f"LED ring test unavailable: {exc}"

    def sleep_mode(self) -> str:
        from nova.sleep import SleepManager

        manager = SleepManager()
        message = manager.activate()
        manager.deactivate()
        return f"Sleep mode test OK. {message}"

    def privacy_mode(self) -> str:
        from nova.privacy import PrivacyManager
        from nova.storage import JsonStore

        manager = PrivacyManager(JsonStore())
        manager.set_for_minutes(1)
        manager.clear()
        return "Privacy mode test OK."

    def lockdown_mode(self) -> str:
        from nova.lockdown import LockdownManager

        manager = LockdownManager()
        message = manager.activate()
        manager.deactivate()
        return f"Lockdown mode test OK. {message}"

    def notifications(self) -> str:
        from nova.notifications import NotificationManager

        manager = NotificationManager()
        message = manager.notify("Diagnostic", "Notification test", level="test")
        history = manager.history()
        return f"{message} {history}"

    def camera(self) -> str:
        from nova.camera import test_camera

        return test_camera()

    def motion(self) -> str:
        from nova.motion import test_motion

        return test_motion()

    def ultrasonic(self) -> str:
        from nova.ultrasonic import test_ultrasonic

        return test_ultrasonic()

    def climate(self) -> str:
        try:
            from nova import climate

            return climate.climate_report()
        except Exception as exc:
            return f"Climate: N/A. {exc}"

    def light(self) -> str:
        from nova.light_sensor import read_light

        reading = read_light()
        return f"Light sensor: {reading.status}; {reading.display}."

    def voltage(self) -> str:
        from nova.voltage_sensor import read_voltage

        reading = read_voltage()
        return f"Voltage sensor: {reading.status}; {reading.display}."

    def volume(self) -> str:
        from nova.volume import get_volume_manager

        manager = get_volume_manager()
        before = manager.state().level
        up = manager.adjust(1)
        manager.set_level(before)
        return f"Volume control test OK. {manager.test()} Change check: {up}"

    def volume_mute(self) -> str:
        from nova.volume import get_volume_manager

        manager = get_volume_manager()
        before = manager.state().level
        muted = manager.mute()
        zero = manager.state()
        manager.set_level(before)
        return f"Mute test OK. {muted} Muted display: {zero.display}."

    def volume_button(self) -> str:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from nova.storage import JsonStore
        from nova.volume import VolumeManager

        with TemporaryDirectory() as tmp:
            manager = VolumeManager(JsonStore(Path(tmp)))
            manager.set_level(42)
            first = manager.toggle_mute()
            muted = manager.state()
            second = manager.toggle_mute()
            restored = manager.state()
        if not muted.muted or restored.level != 42 or restored.muted:
            return "Rotary button mute test failed."
        return f"Rotary button mute test OK. {first} {second} Restored {restored.display}."

    def voice_login(self) -> str:
        from nova.voice_profiles import VoiceProfileManager

        manager = VoiceProfileManager()
        return manager.status()

    def accounts(self) -> str:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from nova.accounts import Accounts
        from nova.storage import JsonStore

        with TemporaryDirectory() as tmp:
            store = JsonStore(Path(tmp))
            accounts = Accounts(store)
            created = accounts.create("Diagnostic")
            switched = accounts.switch("Diagnostic")
            current = accounts.current_user()
        return f"Account system test OK. {created} {switched} Current: {current}."
