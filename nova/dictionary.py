from __future__ import annotations

import re

import requests


def define(command: str) -> str:
    word = re.sub(r"^(define|what does|what is the definition of)\s+", "", command.strip().rstrip("?"), flags=re.I)
    word = word.replace(" mean", "").strip()
    if not word:
        return "Tell me which word to define."
    try:
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=5)
        if response.status_code != 200:
            return f"I could not find a definition for {word}."
        data = response.json()
        definition = data[0]["meanings"][0]["definitions"][0]["definition"]
        return f"{word} means {definition}"
    except Exception:
        return "Dictionary lookup needs internet. I could not reach it right now."

