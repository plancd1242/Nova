from __future__ import annotations

from nova.storage import JsonStore


class Accounts:
    def __init__(self, store: JsonStore):
        self.store = store

    def current_user(self) -> str:
        return self.store.read("users.json").get("current_user", "Caleb")

    def create_or_switch(self, name: str) -> str:
        name = name.strip().title()
        data = self.store.read("users.json")
        users = data.setdefault("users", {})
        if name not in users:
            users[name] = {"alarms": [], "preferences": {}}
        data["current_user"] = name
        self.store.write("users.json", data)
        return f"Okay. I switched to {name}."

