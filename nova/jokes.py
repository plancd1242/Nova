from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from nova.config import settings
from nova.storage import JsonStore


LOCAL_JOKES = [
    {"id": "computer-glasses", "text": "Why did the computer get glasses? Because it wanted to improve its web sight."},
    {"id": "math-book-sad", "text": "Why was the math book sad? It had too many problems."},
    {"id": "fake-noodle", "text": "What do you call a fake noodle? An impasta."},
    {"id": "robot-vacation", "text": "Why did the robot go on vacation? It needed to recharge."},
    {"id": "palm-tree", "text": "What kind of tree fits in your hand? A palm tree."},
    {"id": "windows-open", "text": "Why did the computer get cold? Because it left its Windows open."},
    {"id": "parallel-lines", "text": "Why are parallel lines so calm? Because they never meet any drama."},
    {"id": "pi-party", "text": "Why did pi get invited to every party? Because it never ends."},
    {"id": "light-bulb", "text": "Why did the light bulb ace the test? It had a bright idea."},
    {"id": "keyboard-snack", "text": "Why did the keyboard bring a snack? It needed more space bars."},
]


@dataclass(frozen=True)
class JokeChoice:
    joke_id: str
    text: str


class JokeStack:
    def __init__(self, store: JsonStore | None = None, jokes: list[dict[str, str]] | None = None):
        self.store = store or JsonStore()
        self.jokes = jokes or LOCAL_JOKES

    def tell(self, user: str | None = None) -> str:
        user = self._clean_user(user or self._current_user())
        choice = self._choose_for_user(user)
        self._record_use(user, choice.joke_id)
        return choice.text

    def stats(self, user: str | None = None) -> dict[str, Any]:
        user = self._clean_user(user or self._current_user())
        data = self.store.read("joke_history.json")
        user_data = data.get("users", {}).get(user, {})
        return {
            "user": user,
            "last_joke_id": user_data.get("last_joke_id"),
            "seen_count": len(user_data.get("seen_joke_ids", [])),
            "usage_counts": user_data.get("usage_counts", {}),
        }

    def _current_user(self) -> str:
        users = self.store.read("users.json")
        return users.get("current_user") or settings.default_user

    def _choose_for_user(self, user: str) -> JokeChoice:
        data = self.store.read("joke_history.json")
        user_data = data.setdefault("users", {}).setdefault(user, self._empty_user_history())
        seen_ids = set(user_data.get("seen_joke_ids", []))
        last_joke_id = user_data.get("last_joke_id")

        unused = [joke for joke in self.jokes if joke["id"] not in seen_ids]
        candidates = unused or self.jokes
        if len(candidates) > 1:
            candidates = [joke for joke in candidates if joke["id"] != last_joke_id]

        joke = random.choice(candidates)
        return JokeChoice(joke_id=joke["id"], text=joke["text"])

    def _record_use(self, user: str, joke_id: str) -> None:
        data = self.store.read("joke_history.json")
        user_data = data.setdefault("users", {}).setdefault(user, self._empty_user_history())

        seen_ids = user_data.setdefault("seen_joke_ids", [])
        if joke_id not in seen_ids:
            seen_ids.append(joke_id)

        usage_counts = user_data.setdefault("usage_counts", {})
        usage_counts[joke_id] = int(usage_counts.get(joke_id, 0)) + 1
        user_data["last_joke_id"] = joke_id

        self.store.write("joke_history.json", data)

    def _empty_user_history(self) -> dict[str, Any]:
        return {"last_joke_id": None, "seen_joke_ids": [], "usage_counts": {}}

    def _clean_user(self, user: str) -> str:
        return user.strip().title() or settings.default_user


def get_joke(user: str | None = None) -> str:
    return JokeStack().tell(user)


def random_joke(user: str | None = None) -> str:
    return get_joke(user)


def tell_joke(user: str | None = None) -> str:
    return get_joke(user)
