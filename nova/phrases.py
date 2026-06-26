from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    category: str
    score: int


# The phrase database is intentionally generated from small, readable word banks.
# This keeps matching fast while giving Nova broad natural-language coverage.
POLITE_PREFIXES = [
    "",
    "please",
    "please nova",
    "hey nova",
    "hi nova",
    "hello nova",
    "nova",
    "buddy",
    "my friend",
    "can you",
    "could you",
    "would you",
    "will you",
    "would you please",
    "can you please",
    "could you please",
    "i need you to",
    "i want you to",
    "i would like you to",
    "help me",
    "help me please",
    "when you can",
    "if you can",
    "real quick",
    "for me",
]

REQUEST_VERBS = [
    "show",
    "start",
    "open",
    "run",
    "turn on",
    "use",
    "check",
    "tell me",
    "tell us",
    "give me",
    "pull up",
    "look at",
    "find",
    "read",
    "display",
    "update",
    "refresh",
    "explain",
    "help with",
]

GENERATION_PREFIXES = [
    "",
    "please",
    "hey nova",
    "nova",
    "can you",
    "could you",
    "would you",
    "can you please",
    "i need you to",
    "i want you to",
    "help me",
    "real quick",
]

GENERATION_ACTIONS = [
    "show",
    "start",
    "open",
    "run",
    "check",
    "tell me",
    "give me",
    "pull up",
    "display",
    "refresh",
    "help with",
]

GENERATION_TAILS = ["", " please", " now", " for me", " real quick"]

BACKUP_VERBS = ["backup", "back up", "save", "protect", "archive", "copy", "preserve"]
CREATE_WORDS = ["now", "today", "manually", "right now", "for me", "my data", "nova data", "everything", "the files"]
SHOW_WORDS = ["show", "list", "display", "tell me", "what are", "pull up", "open", "read", "view"]
STATUS_WORDS = ["status", "state", "health", "report", "condition", "summary", "details", "info"]
RESTORE_WORDS = ["restore", "recover", "bring back", "roll back", "load", "return to", "go back to"]
CLEAN_WORDS = ["clean", "cleanup", "delete old", "remove old", "prune", "clear old", "tidy"]
TIME_WORDS = ["time", "clock", "hour", "schedule", "when", "backup time"]


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
    "goodbye": ["bye", "goodbye", "see you later", "good night", "shut down", "exit", "quit"],
    "small_talk": ["how are you", "how is it going", "what are you doing", "are you awake", "are you online"],
    "thanks": ["thanks", "thank you", "thanks nova", "appreciate it", "good job"],
    "confirmation": ["yes", "yeah", "yep", "sure", "okay", "ok", "do it", "that is right"],
    "cancellation": ["no", "nope", "cancel", "never mind", "stop that", "forget it", "do not do that"],
    "help": ["help", "what can you do", "show commands", "how do i use nova", "what should i ask"],
    "error_recovery": ["try again", "that was wrong", "fix that", "i meant", "not what i asked"],
    "question": ["can i ask a question", "i have a question", "question", "what is", "why is", "how do"],
    "settings": ["settings", "preferences", "change settings", "set preference", "configure nova"],
    "account": ["create account", "switch account", "current account", "who am i", "list accounts"],
    "notification": ["show notifications", "clear notifications", "save notification", "notify me"],
    "sensor": ["sensor status", "check sensors", "temperature sensor", "light sensor", "voltage sensor"],
    "hardware": ["hardware status", "check hardware", "hardware report", "what is connected"],
    "diagnostic": ["test oled", "test backup screen", "test camera", "test motion sensor", "run diagnostics"],
    "time": ["what time is it", "tell me the time", "current time", "clock"],
    "date": ["what day is it", "what is the date", "today's date", "current date"],
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


FEATURE_WORDS: dict[str, list[str]] = {
    "joke": ["joke", "funny joke", "dad joke", "pun", "riddle", "something silly", "something funny", "laugh"],
    "dictionary": ["definition", "meaning", "word meaning", "vocabulary", "dictionary", "explanation", "term"],
    "math": ["math", "calculation", "problem", "equation", "answer", "sum", "percent", "fraction", "algebra"],
    "weather": ["weather", "forecast", "rain", "snow", "outside temperature", "conditions", "weather report"],
    "note": ["note", "reminder note", "idea", "shopping list", "study note", "thing to remember"],
    "privacy": ["privacy", "privacy mode", "private mode", "quiet privacy", "stop listening", "limited responses"],
    "sleep": ["sleep", "sleep mode", "nap", "rest mode", "quiet mode", "dim mode", "bedtime mode"],
    "lockdown": ["lockdown", "security", "security mode", "intruder alert", "room protection", "red alert"],
    "oled": ["oled", "screen", "display", "status screen", "oled display", "little screen", "dashboard"],
    "sensor": ["sensors", "sensor status", "temperature sensor", "humidity sensor", "light sensor", "voltage sensor", "climate sensor"],
    "hardware": ["hardware", "hardware status", "connected parts", "devices", "electronics", "modules", "sensors"],
    "notification": ["notifications", "alerts", "messages", "notification history", "notice", "reminder alerts"],
    "account": ["account", "profile", "user", "person", "current account", "family account", "voice profile"],
    "settings": ["settings", "preferences", "configuration", "options", "setup", "defaults"],
    "help": ["help", "commands", "command list", "what you can do", "instructions", "menu"],
    "diagnostic": ["test", "diagnostic", "self test", "system test", "hardware test", "smoke test"],
    "time": ["time", "clock", "current time", "hour", "what time"],
    "date": ["date", "day", "today", "calendar", "current date"],
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

        for category in self.phrases:
            if self._keyword_match(category, normalized):
                return MatchResult(category, 70)
        return None

    def count(self) -> int:
        return sum(len(items) for items in self.phrases.values())

    def _build(self) -> dict[str, set[str]]:
        phrases = {category: {normalize(item) for item in seeds} for category, seeds in PHRASE_SEEDS.items()}
        self._add_social_phrases(phrases)
        self._add_feature_request_phrases(phrases)
        self._add_backup_phrases(phrases)
        self._add_question_and_recovery_phrases(phrases)
        return phrases

    def _add_social_phrases(self, phrases: dict[str, set[str]]) -> None:
        greetings = [
            "hi",
            "hello",
            "hey",
            "yo",
            "howdy",
            "hiya",
            "sup",
            "what's up",
            "morning",
            "good morning",
            "good afternoon",
            "good evening",
            "good night",
            "greetings",
            "salutations",
            "hiya there",
            "hey there",
            "hello there",
        ]
        names = ["", " nova", " assistant", " buddy", " friend", " pal", " computer", " helper", " kiddo helper"]
        endings = [
            "",
            " please",
            " there",
            " are you awake",
            " can you hear me",
            " how are you",
            " you there",
            " are you online",
            " wake up",
            " let's go",
        ]
        for greeting in greetings:
            for name in names:
                for ending in endings:
                    phrases["greeting"].add(normalize(f"{greeting}{name}{ending}"))

        goodbye_starts = ["bye", "goodbye", "see ya", "see you", "later", "catch you later", "i am done", "that is all"]
        goodbye_ends = ["", " nova", " for now", " thanks", " good night", " talk later", " shut down"]
        for start in goodbye_starts:
            for end in goodbye_ends:
                phrases["goodbye"].add(normalize(f"{start}{end}"))

        small_talk_starts = ["how are you", "how is it going", "what are you doing", "are you okay", "are you ready"]
        small_talk_ends = ["", " today", " nova", " right now", " this morning", " tonight", " my friend"]
        for start in small_talk_starts:
            for end in small_talk_ends:
                phrases["small_talk"].add(normalize(f"{start}{end}"))

        for word in ["thanks", "thank you", "thanks a lot", "thank you very much", "appreciate it", "nice work", "good job"]:
            for name in ["", " nova", " buddy", " friend"]:
                phrases["thanks"].add(normalize(f"{word}{name}"))

        for word in ["yes", "yeah", "yep", "yup", "sure", "okay", "ok", "do it", "correct", "that is right", "sounds good"]:
            phrases["confirmation"].add(normalize(word))
        for word in ["no", "nope", "nah", "cancel", "never mind", "stop", "forget it", "not now", "do not do that"]:
            phrases["cancellation"].add(normalize(word))

    def _add_feature_request_phrases(self, phrases: dict[str, set[str]]) -> None:
        actions = GENERATION_ACTIONS + ["can we", "let's", "i need", "i want", "i would like"]
        for category, subjects in FEATURE_WORDS.items():
            for prefix in GENERATION_PREFIXES:
                for action in actions:
                    for subject in subjects:
                        for tail in GENERATION_TAILS:
                            phrases.setdefault(category, set()).add(normalize(f"{prefix} {action} {subject} {tail}"))

        account_actions = ["create", "make", "switch", "change", "show", "list", "open", "use", "select"]
        account_targets = ["account", "profile", "user account", "family account", "voice profile"]
        for prefix in POLITE_PREFIXES:
            for action in account_actions:
                for target in account_targets:
                    for name in ["", " for caleb", " for mom", " for dad", " named alex", " named sam", " to caleb"]:
                        phrases["account"].add(normalize(f"{prefix} {action} {target}{name}"))

        test_targets = [
            "oled",
            "backup screen",
            "sleep mode",
            "privacy mode",
            "lockdown mode",
            "notifications",
            "camera",
            "motion sensor",
            "ultrasonic sensor",
            "climate",
            "light sensor",
            "voltage sensor",
            "accounts",
            "voice login",
        ]
        for target in test_targets:
            for prefix in POLITE_PREFIXES:
                for verb in ["test", "check", "try", "run test for", "diagnose", "verify"]:
                    phrases["diagnostic"].add(normalize(f"{prefix} {verb} {target}"))

    def _add_backup_phrases(self, phrases: dict[str, set[str]]) -> None:
        backup_targets = [
            "backup",
            "back up",
            "backup file",
            "backup copy",
            "data backup",
            "nova backup",
            "safety copy",
            "archive",
            "saved copy",
        ]
        for prefix in POLITE_PREFIXES:
            for verb in ["make", "create", "start", "run", "do", "save", "prepare", "build", "generate"]:
                for target in backup_targets:
                    for tail in CREATE_WORDS:
                        phrases["backup_now"].add(normalize(f"{prefix} {verb} a {target} {tail}"))

            for show in SHOW_WORDS:
                for target in ["backups", "backup history", "backup list", "saved backups", "backup files", "backup records"]:
                    phrases["backup_list"].add(normalize(f"{prefix} {show} {target}"))

            for word in STATUS_WORDS:
                phrases["backup_status"].add(normalize(f"{prefix} backup {word}"))
                phrases["backup_status"].add(normalize(f"{prefix} what is the backup {word}"))
                phrases["backup_status"].add(normalize(f"{prefix} how are backups doing"))

            for restore in RESTORE_WORDS:
                for latest in ["latest", "newest", "most recent", "last"]:
                    phrases["backup_restore_latest"].add(normalize(f"{prefix} {restore} {latest} backup"))
                phrases["backup_restore"].add(normalize(f"{prefix} {restore} backup"))

            for clean in CLEAN_WORDS:
                phrases["backup_cleanup"].add(normalize(f"{prefix} {clean} backups"))
                phrases["backup_cleanup"].add(normalize(f"{prefix} {clean} backup files"))

            for word in TIME_WORDS:
                phrases["backup_set_time"].add(normalize(f"{prefix} set backup {word}"))
                phrases["backup_set_time"].add(normalize(f"{prefix} change backup {word}"))
                phrases["backup_set_time"].add(normalize(f"{prefix} change backup schedule"))

            for phrase in [
                "change backup cleanup days",
                "set backup cleanup days",
                "change backup retention",
                "keep backups for",
                "save backups for",
                "delete backups after",
            ]:
                phrases["backup_set_keep_days"].add(normalize(f"{prefix} {phrase}"))

    def _add_question_and_recovery_phrases(self, phrases: dict[str, set[str]]) -> None:
        question_words = ["what", "why", "how", "when", "where", "who", "which", "can", "could", "would", "is", "are"]
        topics = [
            "nova",
            "this",
            "that",
            "weather",
            "time",
            "date",
            "backup",
            "sensor",
            "account",
            "word",
            "math problem",
            "note",
        ]
        for word in question_words:
            for topic in topics:
                phrases["question"].add(normalize(f"{word} is {topic}"))
                phrases["question"].add(normalize(f"{word} about {topic}"))

        recovery_starts = ["try again", "that was wrong", "not that", "i meant", "fix that", "redo it", "say that again"]
        recovery_ends = ["", " please", " nova", " a different way", " slower", " more clearly", " with another answer"]
        for start in recovery_starts:
            for end in recovery_ends:
                phrases["error_recovery"].add(normalize(f"{start}{end}"))

    def _keyword_match(self, category: str, text: str) -> bool:
        words = set(text.split())
        if category == "backup_now":
            return has_backup(text) and any(word in words for word in ["now", "create", "make", "start", "run", "save"])
        if category == "backup_list":
            return has_backup(text) and any(word in words for word in ["show", "list", "history", "backups", "files"])
        if category == "backup_status":
            return has_backup(text) and any(word in words for word in ["status", "health", "report", "summary"])
        if category == "backup_restore_latest":
            return has_backup(text) and any(word in words for word in ["latest", "newest", "recent"]) and any(
                word in words for word in ["restore", "recover"]
            )
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

        keyword_map = {
            "goodbye": ["bye", "goodbye", "quit", "exit", "shutdown"],
            "small_talk": ["how are you", "are you awake", "are you online"],
            "thanks": ["thanks", "thank you", "appreciate"],
            "help": ["help", "commands", "what can you do"],
            "error_recovery": ["try again", "wrong", "i meant", "fix that"],
            "joke": ["joke", "laugh", "funny", "pun", "riddle"],
            "dictionary": ["define", "definition", "meaning", "dictionary"],
            "math": ["math", "calculate", "solve", "plus", "minus", "times", "percent"],
            "weather": ["weather", "forecast", "rain", "outside"],
            "time": ["time", "clock"],
            "date": ["date", "day"],
            "note": ["note", "remember", "write down"],
            "privacy": ["private", "privacy", "stop listening"],
            "sleep": ["sleep", "nap", "quiet mode"],
            "lockdown": ["lockdown", "security", "intruder", "red alert"],
            "oled": ["oled", "display", "screen"],
            "sensor": ["sensor", "temperature", "humidity", "voltage", "light"],
            "hardware": ["hardware", "connected", "device"],
            "notification": ["notification", "alert", "message"],
            "settings": ["setting", "settings", "preference", "configure"],
            "account": ["account", "profile", "who am i", "switch user"],
            "diagnostic": ["test", "diagnostic", "verify"],
        }
        if category == "greeting":
            return bool(words & {"hi", "hello", "hey", "yo", "howdy", "sup", "hiya", "greetings"})
        return any(keyword in text for keyword in keyword_map.get(category, []))


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
