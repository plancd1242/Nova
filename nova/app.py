from __future__ import annotations

import datetime as _dt
import os
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Callable, Optional


# ============================================================
# Nova App 🧠
# Main brain file for Nova
# This file should be saved as:
# nova/app.py
# ============================================================


@dataclass
class NovaState:
    running: bool = True
    private_until: Optional[_dt.datetime] = None
    last_command: str = ""


class NovaApp:
    def __init__(self) -> None:
        self.state = NovaState()
        self.name = "Nova"
        self.backup_scheduler: object | None = None

        self._load_env_file(".env.local")
        self._load_env_file(".env")

        from nova.backups import BackupManager
        from nova.accounts import Accounts
        from nova.diagnostics import Diagnostics
        from nova.hardware import HardwareManager
        from nova.lockdown import LockdownManager
        from nova.notifications import NotificationManager
        from nova.phrases import get_database
        from nova.sensor_manager import get_sensor_manager
        from nova.sleep import SleepManager
        from nova.system_status import SystemStatusManager
        from nova.voice_profiles import VoiceProfileManager

        self.accounts = Accounts()
        self.backups = BackupManager()
        self.diagnostics = Diagnostics()
        self.hardware = HardwareManager()
        self.lockdown = LockdownManager()
        self.notifications = NotificationManager()
        self.phrases = get_database()
        self.sensor_manager = get_sensor_manager()
        self.sleep = SleepManager()
        self.system_status = SystemStatusManager()
        self.voice_profiles = VoiceProfileManager(self.accounts)

    # ------------------------------------------------------------
    # Basic helpers
    # ------------------------------------------------------------


    def _load_env_file(self, path: str) -> None:
        """
        Super simple .env loader.
        This lets Nova read .env.local without needing python-dotenv.
        """
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    if not line or line.startswith("#") or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if key and key not in os.environ:
                        os.environ[key] = value
        except Exception:
            pass

    def say(self, text: str) -> None:
        """
        Nova talks here.
        First tries eSpeak NG.
        If eSpeak is not installed, it prints instead.
        """
        text = str(text)
        print(f"\nNova: {text}\n")

        try:
            subprocess.run(
                ["espeak-ng", "-s", "140", "-p", "32", text],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Mac or missing eSpeak fallback
            pass

    def led(self, mode: str) -> None:
        """
        Safe LED function.
        It will not crash if the LED ring is not plugged in yet.
        """
        print(f"[LED mode: {mode}]")

        try:
            from nova import led as led_module

            for function_name in ["set_mode", "show", "status", "led_status"]:
                func = getattr(led_module, function_name, None)
                if callable(func):
                    func(mode)
                    return
        except Exception:
            return

    def oled(self, mode: str, extra_lines: list[str] | tuple[str, ...] | None = None) -> None:
        """
        Safe OLED function.
        It will not crash if the OLED screen or display libraries are missing.
        """
        try:
            from nova import oled as oled_module

            for function_name in ["show", "status", "set_mode"]:
                func = getattr(oled_module, function_name, None)
                if callable(func):
                    if function_name == "set_mode":
                        func(mode)
                    else:
                        func(mode, extra_lines)
                    return
        except Exception:
            return

    def status_display(self, mode: str, extra_lines: list[str] | tuple[str, ...] | None = None) -> None:
        self.led(mode)
        self.oled(mode, extra_lines)

    def start_oled_refresh(self) -> None:
        try:
            from nova import oled as oled_module

            start_auto_refresh = getattr(oled_module, "start_auto_refresh", None)
            if callable(start_auto_refresh):
                start_auto_refresh()
        except Exception:
            return

    def stop_oled_refresh(self) -> None:
        try:
            from nova import oled as oled_module

            stop_auto_refresh = getattr(oled_module, "stop_auto_refresh", None)
            if callable(stop_auto_refresh):
                stop_auto_refresh()
        except Exception:
            return

    def shutdown_oled(self) -> None:
        try:
            from nova import oled as oled_module

            shutdown = getattr(oled_module, "shutdown", None)
            if callable(shutdown):
                shutdown()
        except Exception:
            return

    def start_volume_monitor(self) -> None:
        try:
            from nova.volume import get_volume_manager

            result = get_volume_manager().start_hardware_monitor()
            if "started" in result.lower():
                print(f"[VOLUME] {result}")
        except Exception as exc:
            print(f"[VOLUME] monitor unavailable: {exc}")

    def stop_volume_monitor(self) -> None:
        try:
            from nova.volume import get_volume_manager

            get_volume_manager().stop_hardware_monitor()
        except Exception:
            return

    def start_backup_scheduler(self) -> None:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            backup_settings = self.backups.settings()
            if not backup_settings.get("enabled", True):
                return
            hour, minute = self._parse_hhmm(str(backup_settings.get("time", "00:00")))
            scheduler = BackgroundScheduler(timezone=os.getenv("NOVA_TIMEZONE", "America/Detroit"))
            scheduler.add_job(
                self._scheduled_backup,
                "cron",
                hour=hour,
                minute=minute,
                id="nova_daily_backup",
                replace_existing=True,
            )
            scheduler.start()
            self.backup_scheduler = scheduler
        except Exception as exc:
            print(f"[BACKUP] scheduler unavailable: {exc}")

    def stop_backup_scheduler(self) -> None:
        scheduler = self.backup_scheduler
        if scheduler is None:
            return
        shutdown = getattr(scheduler, "shutdown", None)
        if callable(shutdown):
            try:
                shutdown(wait=False)
            except Exception:
                pass
        self.backup_scheduler = None

    def _scheduled_backup(self) -> None:
        try:
            self.status_display("backup", ("Automatic backup",))
            print(f"[BACKUP] {self.backups.create_backup(reason='scheduled')}")
        except Exception as exc:
            print(f"[BACKUP] scheduled backup failed: {exc}")
        finally:
            if not self.is_private():
                self.status_display("ready")

    # ------------------------------------------------------------
    # System check
    # ------------------------------------------------------------

    def system_check(self) -> str:
        checks = []

        checks.append("Nova system check:")
        checks.append(f"Python version: {sys.version.split()[0]}")

        # Check files
        important_files = [
            "main.py",
            "requirements.txt",
            ".env.local",
            ".env.example",
        ]

        for file_name in important_files:
            if os.path.exists(file_name):
                checks.append(f"Found {file_name}")
            else:
                checks.append(f"Missing {file_name}")

        # Check folders
        important_folders = ["nova", "data", "sounds"]

        for folder_name in important_folders:
            if os.path.isdir(folder_name):
                checks.append(f"Found {folder_name} folder")
            else:
                checks.append(f"Missing {folder_name} folder")

        # Check API keys
        if os.getenv("OPENWEATHER_API_KEY"):
            checks.append("OpenWeather API key found")
        else:
            checks.append("OpenWeather API key not found")

        if os.getenv("SPOTIFY_CLIENT_ID"):
            checks.append("Spotify Client ID found")
        else:
            checks.append("Spotify Client ID not found")

        if os.getenv("SPOTIFY_CLIENT_SECRET"):
            checks.append("Spotify Client Secret found")
        else:
            checks.append("Spotify Client Secret not found")

        if os.getenv("NOVA_OLED_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}:
            checks.append("OLED enabled: SSD1306 I2C display configured")
        else:
            checks.append("OLED disabled: text fallback ready")

        if os.getenv("NOVA_CLIMATE_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}:
            checks.append("Climate sensor enabled: DHT sensor configured")
        else:
            checks.append("Climate sensor disabled: unavailable fallback ready")

        checks.append(f"Backup: {self.backups.status()}")
        checks.append(self.hardware.report())
        checks.append(f"Sensors: {self.sensor_manager.status_report()}")
        checks.append(f"Phrase database: {self.phrases.count()} generated phrases")

        return "\n".join(checks)

    # ------------------------------------------------------------
    # Private mode
    # ------------------------------------------------------------

    def is_private(self) -> bool:
        if self.state.private_until is None:
            return False

        now = _dt.datetime.now()

        if now >= self.state.private_until:
            self.state.private_until = None
            self.status_display("ready")
            return False

        return True

    def go_private(self, minutes: int = 30) -> str:
        self.state.private_until = _dt.datetime.now() + _dt.timedelta(minutes=minutes)
        self.status_display("private", (f"{minutes} minutes",))
        return f"Okay. I will go private for {minutes} minutes."

    def private_time_left(self) -> str:
        if not self.is_private():
            return "I am not in private mode right now."

        left = self.state.private_until - _dt.datetime.now()
        minutes = max(1, int(left.total_seconds() // 60))
        return f"I am private for about {minutes} more minutes."

    # ------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------

    def handle_command(self, command: str) -> str:
        command = command.strip()
        lower = command.lower()
        self.state.last_command = command

        if not command:
            return "Please type a command."

        # Quit
        if lower in ["quit", "exit", "stop nova", "bye"]:
            self.state.running = False
            self.status_display("off")
            return "Okay. Nova is shutting down."

        # Wake word typed mode
        if lower in ["hey nova", "nova"]:
            self.status_display("listening")
            return "Uh-huh?"

        if lower.startswith("test "):
            self.status_display("thinking")
            try:
                return self._test_command(command)
            finally:
                if not self.is_private():
                    self.status_display("done")

        # Private mode
        if lower in ["who am i", "current account", "who is logged in", "which account"]:
            return self.accounts.current_account_report()

        if lower.startswith("switch account") or lower.startswith("change account"):
            return self._account_command(command)

        if lower.startswith("create account") or lower.startswith("make account"):
            return self._account_command(command)

        if lower in ["list accounts", "show accounts"]:
            return self.accounts.list_accounts()

        if "private time left" in lower:
            return self.private_time_left()

        if "go private" in lower or "privacy mode" in lower:
            minutes = self._find_minutes(lower)
            if minutes is None:
                minutes = 30
            return self.go_private(minutes)

        if "wake up" in lower or "stop private" in lower:
            self.state.private_until = None
            self.sleep.deactivate()
            self.lockdown.deactivate()
            self.status_display("ready")
            return "Okay. I am listening again."

        if self.is_private():
            return "I am in private mode right now."

        # Normal commands
        self.status_display("thinking")
        route = self.phrases.match(lower)
        keep_display_mode = False

        try:
            if route and route.category.startswith("backup_"):
                keep_display_mode = route.category in {"backup_now", "backup_restore_latest"}
                return self._backup_command(route.category, command)

            if route and route.category == "sleep":
                keep_display_mode = True
                return self._sleep_command()

            if route and route.category == "lockdown":
                keep_display_mode = True
                return self._lockdown_command()

            if "oled status" in lower or "display status" in lower:
                return self.diagnostics.oled_status()

            if route and route.category == "oled":
                return self._oled_command(command)

            if "hardware status" in lower or "hardware report" in lower:
                return self.hardware.report()

            if "sensor status" in lower or "sensor report" in lower:
                return self.sensor_manager.status_report()

            if "system status" in lower or "system report" in lower:
                return self.system_status.report().summary

            if "notification" in lower or "notifications" in lower:
                return self._notification_command(command)

            router_answer = self._router_command(command)
            if router_answer is not None:
                return router_answer

            if "voice login" in lower or "voice profile" in lower:
                return self._voice_profile_command(command)

            if self._looks_like_volume(lower):
                return self._volume_command(command)

            if (route and route.category == "greeting") or self._matches(lower, ["hello", "hi nova", "hi"]):
                return random.choice(
                    [
                        "Hello Caleb.",
                        "Hi. Nova is online.",
                        "Hello. I am Nova.",
                    ]
                )

            if "time" in lower:
                return self._time_command()

            if "date" in lower or "day is it" in lower:
                return self._date_command()

            if self._looks_like_climate(lower):
                return self._climate_command()

            if (route and route.category == "joke") or "joke" in lower:
                return self._joke_command()

            if "spell" in lower or "how do you spell" in lower:
                return self._spell_command(command)

            if (route and route.category == "dictionary") or "define" in lower or "what does" in lower or "definition" in lower:
                return self._definition_command(command)

            if (route and route.category == "weather") or "weather" in lower or "temperature" in lower or "rain" in lower:
                return self._weather_command(command)

            if "spotify" in lower or "music" in lower or lower.startswith("play "):
                return self._spotify_command(command)

            if "quiz" in lower:
                return self._quiz_command()

            if "note" in lower or "remember this" in lower:
                return self._note_command(command)

            if self._looks_like_math(lower):
                return self._math_command(command)

            if lower.startswith("search ") or lower.startswith("look up "):
                return self._web_search_command(command)

            return "I do not know that command yet."

        finally:
            if not keep_display_mode and not self.is_private():
                self.status_display("done")

    # ------------------------------------------------------------
    # Small command tools
    # ------------------------------------------------------------

    def _matches(self, text: str, options: list[str]) -> bool:
        return any(option in text for option in options)

    def _find_minutes(self, text: str) -> Optional[int]:
        match = re.search(r"(\d+)\s*(minute|minutes|min)", text)
        if match:
            return int(match.group(1))
        return None

    def _parse_hhmm(self, value: str) -> tuple[int, int]:
        match = re.match(r"^([01]?\d|2[0-3]):([0-5]\d)$", value.strip())
        if not match:
            return (0, 0)
        return (int(match.group(1)), int(match.group(2)))

    def _looks_like_climate(self, text: str) -> bool:
        if any(word in text for word in ["weather", "forecast", "outside", "rain"]):
            return False
        return any(
            phrase in text
            for phrase in [
                "humidity",
                "room temperature",
                "inside temperature",
                "indoor temperature",
                "temperature sensor",
                "climate",
            ]
        ) or text in {"temperature", "temp"}

    def _looks_like_volume(self, text: str) -> bool:
        return any(word in text for word in ["volume", "mute", "unmute", "louder", "quieter", "turn it up", "turn it down"])

    def _time_command(self) -> str:
        now = _dt.datetime.now()
        return f"It is {now.strftime('%I:%M %p').lstrip('0')}."

    def _date_command(self) -> str:
        now = _dt.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    def _account_command(self, command: str) -> str:
        lower = command.lower()
        name = command
        for phrase in ["create account", "make account", "switch account", "change account", "for", "to", "named"]:
            name = re.sub(rf"\b{re.escape(phrase)}\b", "", name, flags=re.IGNORECASE).strip()
        if not name:
            if lower.startswith(("create", "make")):
                return "What name should I use for the new account?"
            return "Which account should I switch to?"
        if lower.startswith(("create", "make")):
            return self.accounts.create(name)
        return self.accounts.switch(name)

    def _test_command(self, command: str) -> str:
        test_name = re.sub(r"^test\s+", "", command, flags=re.IGNORECASE).strip()
        if test_name == "backup status":
            return self.backups.status()
        if test_name == "system status":
            return self.system_status.report().summary
        if test_name == "hardware status":
            return self.hardware.report()
        if test_name == "sensor status":
            return self.sensor_manager.status_report()
        return self.diagnostics.run(test_name)

    def _backup_command(self, category: str, command: str) -> str:
        try:
            from nova.phrases import find_number

            if category == "backup_now":
                self.status_display("backup", ("Manual backup",))
                result = self.backups.create_backup(reason="manual")
                self.status_display("backup_complete", ("Backup Complete",))
                return result
            if category == "backup_list":
                return self.backups.history()
            if category == "backup_status":
                return self.backups.status()
            if category == "backup_restore_latest":
                self.status_display("backup", ("Restoring latest",))
                result = self.backups.restore_latest()
                self.status_display("backup_complete", ("Backup Complete",))
                return result
            if category == "backup_restore":
                self.status_display("backup", ("Restore requested",))
                return "Tell me which backup filename to restore, or say restore latest backup."
            if category == "backup_cleanup":
                removed = self.backups.cleanup_old_backups()
                return f"Backup cleanup complete. Removed {removed} old backup{'s' if removed != 1 else ''}."
            if category == "backup_set_time":
                result = self.backups.set_time(command)
                self.stop_backup_scheduler()
                self.start_backup_scheduler()
                return result
            if category == "backup_set_keep_days":
                days = find_number(command)
                if days is None:
                    return "Tell me how many days of backups to keep."
                return self.backups.set_keep_days(days)
        except Exception as exc:
            return f"Backup manager could not complete that: {exc}"
        return "I heard a backup command, but I do not know that backup action yet."

    def _climate_command(self) -> str:
        try:
            from nova import climate

            return climate.climate_report()
        except Exception:
            return "The temperature and humidity sensor is not connected yet."

    def _sleep_command(self) -> str:
        message = self.sleep.activate()
        self.status_display("sleeping", ("Quiet operation",))
        return message

    def _lockdown_command(self) -> str:
        message = self.lockdown.activate()
        self.status_display("lockdown", ("Security active",))
        return message

    def _notification_command(self, command: str) -> str:
        lower = command.lower()
        if "clear" in lower:
            return self.notifications.clear()
        if "show" in lower or "list" in lower or "history" in lower:
            return self.notifications.history()
        return self.notifications.notify("Nova note", command, level="info")

    def _router_command(self, command: str) -> str | None:
        try:
            from nova.router_commands import parse_router_command
            from nova.router_control import get_router_control

            parsed = parse_router_command(command)
            if parsed is None:
                return None

            router = get_router_control()
            if parsed.action == "status":
                return router.status().message
            if parsed.action == "inspect":
                return router.inspect().message
            if parsed.action == "main_wifi_off":
                return router.turn_main_wifi_off(confirmed=parsed.confirmed).message
            if parsed.action == "main_wifi_on":
                return router.restore_main_wifi().message
            if parsed.action == "guest" and parsed.guest_key and parsed.enabled is not None:
                return router.set_guest(parsed.guest_key, parsed.enabled).message
            if parsed.action == "speed_test":
                return router.speed_test().message
            return "I heard a router command, but I do not know that router action yet."
        except Exception as exc:
            return f"Router control is unavailable: {type(exc).__name__}."

    def _volume_command(self, command: str) -> str:
        try:
            from nova.volume import get_volume_manager

            manager = get_volume_manager()
            lower = command.lower()
            match = re.search(r"\b(\d{1,3})\b", lower)
            if "mute" in lower and "unmute" not in lower:
                result = manager.mute()
            elif "unmute" in lower:
                result = manager.unmute()
            elif "button" in lower or "press" in lower or "toggle" in lower:
                result = manager.toggle_mute_from_button()
            elif match:
                result = manager.set_level(int(match.group(1)))
            elif "up" in lower or "louder" in lower or "increase" in lower:
                result = manager.adjust(5)
            elif "down" in lower or "quieter" in lower or "decrease" in lower:
                result = manager.adjust(-5)
            else:
                state = manager.state()
                result = f"Volume is {state.display}. Hardware: {state.hardware}."
            self.oled("ready")
            return result
        except Exception as exc:
            return f"Volume control is unavailable: {exc}"

    def _voice_profile_command(self, command: str) -> str:
        lower = command.lower()
        if "status" in lower or "available" in lower:
            return self.voice_profiles.status()
        if "train" in lower or "create" in lower or "setup" in lower:
            user = self.accounts.current_user()
            return self.voice_profiles.create_profile_from_phrase(user, "Hi Nova")
        if "who" in lower or "identify" in lower:
            result = self.voice_profiles.identify_from_phrase("Hi Nova")
            if result.status == "Matched" and result.user:
                return f"I think {result.user} is speaking."
            if result.status == "Unavailable":
                return self.voice_profiles.status()
            return "I am not sure who is speaking."
        return self.voice_profiles.status()

    def _oled_command(self, command: str) -> str:
        lower = command.lower()
        if "refresh" in lower or "update" in lower:
            try:
                from nova import oled

                oled.refresh()
                return "I refreshed the OLED display."
            except Exception:
                return "The OLED display is not available right now."
        return "The OLED display is connected to Nova status, time, temperature, and humidity."

    def _joke_command(self) -> str:
        try:
            from nova import jokes

            for function_name in ["get_joke", "random_joke", "tell_joke"]:
                func = getattr(jokes, function_name, None)
                if callable(func):
                    return str(func())
        except Exception:
            pass

        jokes = [
            "Why did the computer get cold? Because it left its Windows open.",
            "Why did the robot go on vacation? It needed to recharge.",
            "Why was the math book sad? It had too many problems.",
        ]
        return random.choice(jokes)

    def _spell_command(self, command: str) -> str:
        text = command.lower()
        text = text.replace("hey nova", "")
        text = text.replace("how do you spell", "")
        text = text.replace("spell", "")
        word = text.strip(" ?.!,")

        if not word:
            return "What word should I spell?"

        try:
            from nova import spelling

            func = getattr(spelling, "spell_word", None)
            if callable(func):
                return str(func(word))
        except Exception:
            pass

        letters = " ".join(list(word.upper()))
        return f"{word} is spelled {letters}."

    def _definition_command(self, command: str) -> str:
        text = command.lower()
        text = text.replace("hey nova", "")
        text = text.replace("what does", "")
        text = text.replace("define", "")
        text = text.replace("definition of", "")
        text = text.replace("mean", "")
        word = text.strip(" ?.!,")

        if not word:
            return "What word should I define?"

        try:
            from nova import dictionary

            for function_name in ["define_word", "define"]:
                func = getattr(dictionary, function_name, None)
                if callable(func):
                    return str(func(word))
        except Exception:
            pass

        return f"Definition mode is not fully connected yet. The word was {word}."

    def _weather_command(self, command: str) -> str:
        try:
            from nova import weather

            for function_name in ["get_weather", "weather_report", "current_weather"]:
                func = getattr(weather, function_name, None)
                if callable(func):
                    return str(func(command))
        except Exception:
            pass

        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return "Weather is not set up yet. Add your OpenWeather API key to .env.local."

        return "Weather mode found an API key, but the weather module is not connected yet."

    def _spotify_command(self, command: str) -> str:
        try:
            from nova import spotify_controller

            for function_name in ["handle_spotify_command", "spotify_command", "handle_command"]:
                func = getattr(spotify_controller, function_name, None)
                if callable(func):
                    return str(func(command))
        except Exception:
            pass

        if not os.getenv("SPOTIFY_CLIENT_ID"):
            return "Spotify is not set up yet. Add your Spotify Client ID and Client Secret to .env.local."

        return "Spotify keys are found, but Spotify control is not connected yet."

    def _quiz_command(self) -> str:
        try:
            from nova import quiz

            for function_name in ["start_quiz", "quiz_mode", "run_quiz"]:
                func = getattr(quiz, function_name, None)
                if callable(func):
                    return str(func())
        except Exception:
            pass

        return "Quiz mode is not connected yet, but I like the idea."

    def _note_command(self, command: str) -> str:
        try:
            from nova import notes

            for function_name in ["save_note", "add_note", "remember"]:
                func = getattr(notes, function_name, None)
                if callable(func):
                    return str(func(command))
        except Exception:
            pass

        os.makedirs("data", exist_ok=True)
        with open("data/notes.txt", "a", encoding="utf-8") as f:
            f.write(command + "\n")

        return "Okay. I saved that note."

    def _web_search_command(self, command: str) -> str:
        query = command.lower()
        query = query.replace("hey nova", "")
        query = query.replace("search", "")
        query = query.replace("look up", "")
        query = query.strip(" ?.!,")

        if not query:
            return "What should I search?"

        try:
            from nova import web_search

            for function_name in ["search_web", "google_search", "web_search"]:
                func = getattr(web_search, function_name, None)
                if callable(func):
                    return str(func(query))
        except Exception:
            pass

        return "Web search is not connected yet."

    # ------------------------------------------------------------
    # Math
    # ------------------------------------------------------------

    def _looks_like_math(self, text: str) -> bool:
        math_words = [
            "plus",
            "minus",
            "times",
            "divided",
            "multiply",
            "square root",
            "sqrt",
            "percent",
            "solve",
            "factor",
            "simplify",
            "+",
            "-",
            "*",
            "/",
            "=",
        ]
        return any(word in text for word in math_words)

    def _math_command(self, command: str) -> str:
        try:
            from nova import math_tools

            for function_name in ["calculate", "do_math", "solve_math", "handle_math"]:
                func = getattr(math_tools, function_name, None)
                if callable(func):
                    return str(func(command))
        except Exception:
            pass

        try:
            import sympy as sp

            expression = command.lower()
            expression = expression.replace("hey nova", "")
            expression = expression.replace("what is", "")
            expression = expression.replace("calculate", "")
            expression = expression.replace("plus", "+")
            expression = expression.replace("minus", "-")
            expression = expression.replace("times", "*")
            expression = expression.replace("multiplied by", "*")
            expression = expression.replace("divided by", "/")
            expression = expression.replace("square root of", "sqrt")
            expression = expression.strip(" ?.!,")

            answer = sp.sympify(expression)
            return f"The answer is {answer}."

        except Exception:
            return "I could not solve that math problem yet."

    # ------------------------------------------------------------
    # Main typed mode
    # ------------------------------------------------------------

    def run_typed(self) -> None:
        self.status_display("ready")
        self.start_oled_refresh()
        self.start_volume_monitor()
        self.start_backup_scheduler()
        self.say("Nova is online. Type a command.")

        try:
            while self.state.running:
                try:
                    command = input("You: ").strip()
                except KeyboardInterrupt:
                    print()
                    self.say("Nova is shutting down.")
                    break

                answer = self.handle_command(command)
                self.say(answer)

            self.status_display("off")
        finally:
            self.stop_oled_refresh()
            self.stop_volume_monitor()
            self.stop_backup_scheduler()
            self.shutdown_oled()
