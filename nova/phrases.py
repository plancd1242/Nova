from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MatchResult:
    category: str
    score: int


POLITE_PREFIXES = [
    "",
    "please",
    "hey nova",
    "nova",
    "can you",
    "could you",
    "would you",
    "will you",
    "i need you to",
    "i want you to",
    "help me",
    "when you can",
]

BACKUP_VERBS = ["backup", "back up", "save", "protect", "archive", "copy"]
CREATE_WORDS = ["now", "today", "manually", "right now", "for me", "my data", "nova data"]
SHOW_WORDS = ["show", "list", "display", "tell me", "what are", "pull up", "open"]
STATUS_WORDS = ["status", "state", "health", "report", "condition", "summary"]
RESTORE_WORDS = ["restore", "recover", "bring back", "roll back", "load"]
CLEAN_WORDS = ["clean", "cleanup", "delete old", "remove old", "prune", "clear old"]
TIME_WORDS = ["time", "clock", "hour", "schedule", "when"]

PHRASE_SEEDS: dict[str, list[str]] = {
    "greeting": [
        "hi",
        "hello",
        "hey",
        "hey nova",
        "hello nova",
        "yo",
        "sup",
        "what's up",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "howdy",
        "hiya",
        "greetings",
        "nice to see you",
        "are you there",
    ],
    "joke": ["tell me a joke", "make me laugh", "say something funny", "got any jokes", "joke time"],
    "dictionary": ["define", "definition", "what does", "what is the meaning of", "explain the word"],
    "math": ["math", "calculate", "solve", "what is", "plus", "minus", "times", "divided by", "percent"],
    "weather": ["weather", "forecast", "is it raining", "outside temperature", "how hot is it outside"],
    "note": ["note", "remember this", "write this down", "save a note", "make a note"],
    "privacy": ["go private", "privacy mode", "stop listening", "private time", "do not listen"],
    "sleep": ["sleep mode", "go to sleep", "take a nap", "quiet mode", "dim the screen"],
    "lockdown": ["lockdown", "security mode", "intruder mode", "protect the room", "red alert"],
    "oled": ["oled", "screen", "display", "show on screen", "refresh display"],
    "backup_now": [],
    "backup_list": [],
    "backup_status": [],
    "backup_restore_latest": [],
    "backup_restore": [],
    "backup_cleanup": [],
    "backup_set_time": [],
    "backup_set_keep_days": [],
}


class PhraseDatabase:
    def __init__(self) -> None:
        self.phrases = self._build()

    def match(self, text: str) -> MatchResult | None:
        normalized = normalize(text)
        if not normalized:
            return None

        for category in [
            "backup_restore_latest",
            "backup_set_keep_days",
            "backup_set_time",
            "backup_cleanup",
            "backup_status",
            "backup_list",
            "backup_now",
            "backup_restore",
        ]:
            if normalized in self.phrases[category] or self._keyword_match(category, normalized):
                return MatchResult(category, 100)

        for category, phrases in self.phrases.items():
            if normalized in phrases:
                return MatchResult(category, 90)

        for category in ["greeting", "joke", "dictionary", "weather", "note", "privacy", "sleep", "lockdown", "oled"]:
            if self._keyword_match(category, normalized):
                return MatchResult(category, 70)
        return None

    def count(self) -> int:
        return sum(len(items) for items in self.phrases.values())

    def _build(self) -> dict[str, set[str]]:
        phrases = {category: {normalize(item) for item in seeds} for category, seeds in PHRASE_SEEDS.items()}

        greetings = ["hi", "hello", "hey", "yo", "howdy", "hiya", "good morning", "good afternoon", "good evening"]
        names = ["", " nova", " assistant", " buddy", " friend"]
        endings = ["", " please", " there", " are you awake", " can you hear me", " how are you"]
        for greeting in greetings:
            for name in names:
                for ending in endings:
                    phrases["greeting"].add(normalize(f"{greeting}{name}{ending}"))

        backup_targets = ["backup", "back up", "backup file", "backup copy", "data backup", "nova backup", "safety copy"]
        for prefix in POLITE_PREFIXES:
            for verb in ["make", "create", "start", "run", "do", "save", "prepare"]:
                for target in backup_targets:
                    for tail in CREATE_WORDS:
                        phrases["backup_now"].add(normalize(f"{prefix} {verb} a {target} {tail}"))

            for show in SHOW_WORDS:
                for target in ["backups", "backup history", "backup list", "saved backups", "backup files"]:
                    phrases["backup_list"].add(normalize(f"{prefix} {show} {target}"))

            for word in STATUS_WORDS:
                phrases["backup_status"].add(normalize(f"{prefix} backup {word}"))
                phrases["backup_status"].add(normalize(f"{prefix} what is the backup {word}"))

            for restore in RESTORE_WORDS:
                phrases["backup_restore_latest"].add(normalize(f"{prefix} {restore} latest backup"))
                phrases["backup_restore_latest"].add(normalize(f"{prefix} {restore} newest backup"))
                phrases["backup_restore"].add(normalize(f"{prefix} {restore} backup"))

            for clean in CLEAN_WORDS:
                phrases["backup_cleanup"].add(normalize(f"{prefix} {clean} backups"))
                phrases["backup_cleanup"].add(normalize(f"{prefix} {clean} backup files"))

            for word in TIME_WORDS:
                phrases["backup_set_time"].add(normalize(f"{prefix} set backup {word}"))
                phrases["backup_set_time"].add(normalize(f"{prefix} change backup {word}"))
                phrases["backup_set_time"].add(normalize(f"{prefix} change backup schedule"))

            for phrase in ["change backup cleanup days", "set backup cleanup days", "change backup retention", "keep backups for"]:
                phrases["backup_set_keep_days"].add(normalize(f"{prefix} {phrase}"))

        subjects = {
            "joke": ["joke", "something funny", "dad joke", "pun", "make me laugh"],
            "dictionary": ["define", "meaning", "definition", "explain"],
            "weather": ["weather", "forecast", "rain", "outside", "temperature outside"],
            "note": ["note", "remember", "write down", "save this", "shopping list"],
            "privacy": ["privacy", "private", "stop listening", "quiet privacy"],
            "sleep": ["sleep", "sleep mode", "nap", "rest", "quiet mode"],
            "lockdown": ["lockdown", "security", "intruder", "alarm", "red alert"],
            "oled": ["oled", "screen", "display", "status screen", "refresh screen"],
        }
        verbs = ["show", "start", "open", "run", "turn on", "use", "check", "tell me", "please do"]
        for category, words in subjects.items():
            for prefix in POLITE_PREFIXES:
                for verb in verbs:
                    for word in words:
                        phrases[category].add(normalize(f"{prefix} {verb} {word}"))

        return phrases

    def _keyword_match(self, category: str, text: str) -> bool:
        words = set(text.split())
        if category == "backup_now":
            return has_backup(text) and any(word in words for word in ["now", "create", "make", "start", "run", "save"])
        if category == "backup_list":
            return has_backup(text) and any(word in words for word in ["show", "list", "history", "backups", "files"])
        if category == "backup_status":
            return has_backup(text) and any(word in words for word in ["status", "health", "report", "summary"])
        if category == "backup_restore_latest":
            return has_backup(text) and "latest" in words and any(word in words for word in ["restore", "recover"])
        if category == "backup_restore":
            return has_backup(text) and any(word in words for word in ["restore", "recover"])
        if category == "backup_cleanup":
            return has_backup(text) and any(word in text for word in ["clean", "cleanup", "delete old", "remove old", "prune"])
        if category == "backup_set_time":
            return has_backup(text) and (
                any(word in text for word in ["set time", "change time", "schedule"])
                or ("time" in words and any(word in words for word in ["set", "change", "move"]))
            )
        if category == "backup_set_keep_days":
            return has_backup(text) and any(word in text for word in ["cleanup days", "keep days", "retention", "keep backups"])
        if category == "greeting":
            return text in self.phrases["greeting"]
        if category == "joke":
            return any(word in text for word in ["joke", "laugh", "funny", "pun"])
        if category == "dictionary":
            return any(word in text for word in ["define", "definition", "meaning"])
        if category == "weather":
            return any(word in text for word in ["weather", "forecast", "rain", "outside"])
        if category == "note":
            return any(word in text for word in ["note", "remember", "write down"])
        if category == "privacy":
            return any(word in text for word in ["private", "privacy", "stop listening"])
        if category == "sleep":
            return any(word in text for word in ["sleep", "nap", "quiet mode"])
        if category == "lockdown":
            return any(word in text for word in ["lockdown", "security", "intruder", "red alert"])
        if category == "oled":
            return any(word in text for word in ["oled", "display", "screen"])
        return False


def normalize(text: str) -> str:
    text = text.lower().replace("nova's", "novas")
    text = re.sub(r"[^a-z0-9: ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has_backup(text: str) -> bool:
    return any(word in text for word in ["backup", "back up", "backups", "archive", "safety copy"])


def find_number(text: str) -> int | None:
    match = re.search(r"\b(\d+)\b", text)
    if not match:
        return None
    return int(match.group(1))


def phrase_count() -> int:
    return get_database().count()


_DATABASE: PhraseDatabase | None = None


def get_database() -> PhraseDatabase:
    global _DATABASE
    if _DATABASE is None:
        _DATABASE = PhraseDatabase()
    return _DATABASE
