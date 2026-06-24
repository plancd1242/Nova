from __future__ import annotations

import re


def spell_word(command: str) -> str:
    text = command.strip().rstrip("?")
    text = re.sub(r"^(how do you spell|spell)\s+", "", text, flags=re.I).strip()
    if not text:
        return "Tell me which word to spell."
    word = text.split()[-1]
    letters = " ".join(word.upper())
    return f"{word} is spelled {letters}."

