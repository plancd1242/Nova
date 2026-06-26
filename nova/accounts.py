from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nova.config import settings
from nova.storage import JsonStore


@dataclass(frozen=True)
class Account:
    name: str
    preferences: dict[str, Any]
    voice_profile: dict[str, Any] | None = None


class Accounts:
    def __init__(self, store: JsonStore | None = None):
        self.store = store or JsonStore()

    def current_user(self) -> str:
        return self.store.read("users.json").get("current_user", settings.default_user)

    def create_or_switch(self, name: str) -> str:
        name = self._clean_name(name)
        if not name:
            return "Tell me the account name."
        data = self.store.read("users.json")
        users = data.setdefault("users", {})
        if name not in users:
            users[name] = self._default_user()
        data["current_user"] = name
        self.store.write("users.json", data)
        return f"Okay. I switched to {name}."

    def create(self, name: str) -> str:
        name = self._clean_name(name)
        if not name:
            return "Tell me the account name."
        data = self.store.read("users.json")
        users = data.setdefault("users", {})
        if name in users:
            return f"{name} already has an account."
        users[name] = self._default_user()
        data["current_user"] = name
        self.store.write("users.json", data)
        return f"Account created for {name}. I switched to that account."

    def switch(self, name: str) -> str:
        name = self._clean_name(name)
        data = self.store.read("users.json")
        users = data.setdefault("users", {})
        if name not in users:
            return f"I could not find an account named {name}."
        data["current_user"] = name
        self.store.write("users.json", data)
        return f"Okay. I switched to {name}."

    def list_accounts(self) -> str:
        users = sorted(self.store.read("users.json").get("users", {}).keys())
        if not users:
            return "No accounts exist yet."
        return "Accounts: " + ", ".join(users)

    def current_account_report(self) -> str:
        return f"The current account is {self.current_user()}."

    def set_preference(self, key: str, value: Any, user: str | None = None) -> str:
        user = self._clean_name(user or self.current_user())
        data = self.store.read("users.json")
        users = data.setdefault("users", {})
        account = users.setdefault(user, self._default_user())
        account.setdefault("preferences", {})[key] = value
        self.store.write("users.json", data)
        return f"I saved {key} for {user}."

    def set_voice_profile(self, user: str, profile: dict[str, Any]) -> None:
        user = self._clean_name(user)
        data = self.store.read("users.json")
        users = data.setdefault("users", {})
        account = users.setdefault(user, self._default_user())
        account["voice_profile"] = profile
        self.store.write("users.json", data)

    def get_voice_profiles(self) -> dict[str, dict[str, Any]]:
        users = self.store.read("users.json").get("users", {})
        profiles: dict[str, dict[str, Any]] = {}
        for name, account in users.items():
            profile = account.get("voice_profile")
            if profile:
                profiles[name] = profile
        return profiles

    def _default_user(self) -> dict[str, Any]:
        return {"alarms": [], "preferences": {}, "notes": [], "voice_profile": None}

    def _clean_name(self, name: str) -> str:
        return " ".join(name.strip().title().split())
