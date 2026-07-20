from __future__ import annotations


class Diagnostics:
    def run(self, name: str) -> str:
        name = name.strip().lower()
        if name in {"oled", "oled status"}:
            return self.oled_status()
        if name in {"led", "led ring", "light ring"}:
            return self.led()
        if name in {"led pixel", "led first pixel", "first led"}:
            return self.led_first_pixel()
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
        if name in {"voice", "voice commands", "speech to text", "vosk"}:
            return self.voice_commands()
        if name in {"microphone", "mic"}:
            return self.microphone()
        if name in {"microphones", "list microphones", "audio devices"}:
            return self.microphones()
        if name in {"wake word", "wake-word"}:
            return self.wake_word()
        if name in {"listen once", "voice listen once"}:
            return self.listen_once()
        if name in {"accounts", "account system"}:
            return self.accounts()
        if name in {"router", "router control"}:
            return self.router()
        if name in {"router status", "wifi status", "wireless status"}:
            return self.router_status()
        if name in {"router inspect", "inspect router", "router page"}:
            return self.router_inspect()
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

    def led_first_pixel(self) -> str:
        try:
            from nova import led

            return led.test_first_pixel()
        except Exception as exc:
            return f"LED first-pixel test unavailable: {exc}"

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

    def voice_commands(self) -> str:
        from nova.speech_to_text import get_speech_to_text

        return get_speech_to_text().status()

    def microphone(self) -> str:
        from nova.microphone import status

        current = status()
        return f"Microphone: {current.status}. {current.message}"

    def microphones(self) -> str:
        from nova.microphone import list_devices

        return list_devices()

    def wake_word(self) -> str:
        from nova.wake_word import get_wake_word_detector

        current = get_wake_word_detector().status()
        return f"Wake word: {current.status}. {current.message}"

    def listen_once(self) -> str:
        from nova.speech_to_text import get_speech_to_text

        result = get_speech_to_text().listen_once()
        if not result.ok:
            return result.message
        return f'I heard: "{result.text}".'

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

    def router(self) -> str:
        from nova.config import settings

        if not settings.router_control_enabled:
            return "Router control is disabled."
        if not settings.router_url:
            return "Router control is missing a router URL."
        if not settings.router_local_password:
            return "Router control is missing the local password."
        try:
            import playwright.sync_api  # type: ignore

            _ = playwright
        except Exception:
            return "Playwright is unavailable, so router control has been disabled."
        return "Router control is configured. Use test router status or inspect router for safe live checks."

    def router_status(self) -> str:
        from nova.router_control import get_router_control

        return get_router_control().status().message

    def router_inspect(self) -> str:
        from nova.router_control import get_router_control

        return get_router_control().inspect().message
