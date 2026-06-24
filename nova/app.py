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

        self._load_env_file(".env.local")
        self._load_env_file(".env")

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

        # Private mode
        if "private time left" in lower:
            return self.private_time_left()

        if "go private" in lower or "privacy mode" in lower:
            minutes = self._find_minutes(lower)
            if minutes is None:
                minutes = 30
            return self.go_private(minutes)

        if "wake up" in lower or "stop private" in lower:
            self.state.private_until = None
            self.status_display("ready")
            return "Okay. I am listening again."

        if self.is_private():
            return "I am in private mode right now."

        # Normal commands
        self.status_display("thinking")

        try:
            if self._matches(lower, ["hello", "hi nova", "hi"]):
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

            if "joke" in lower:
                return self._joke_command()

            if "spell" in lower or "how do you spell" in lower:
                return self._spell_command(command)

            if "define" in lower or "what does" in lower or "definition" in lower:
                return self._definition_command(command)

            if "weather" in lower or "temperature" in lower or "rain" in lower:
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
            if not self.is_private():
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

    def _time_command(self) -> str:
        now = _dt.datetime.now()
        return f"It is {now.strftime('%I:%M %p').lstrip('0')}."

    def _date_command(self) -> str:
        now = _dt.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    def _climate_command(self) -> str:
        try:
            from nova import climate

            return climate.climate_report()
        except Exception:
            return "The temperature and humidity sensor is not connected yet."

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
        self.say("Nova is online. Type a command.")

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
