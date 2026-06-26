from __future__ import annotations

from datetime import datetime

from nova.accounts import Accounts
from nova.storage import JsonStore


class Notes:
    def __init__(self, store: JsonStore):
        self.store = store

    def add(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "Tell me what note to save."
        user = Accounts(self.store).current_user()
        data = self.store.read("notes.json")
        data.setdefault("notes", []).append(
            {"text": text, "user": user, "created_at": datetime.now().isoformat(timespec="seconds")}
        )
        self.store.write("notes.json", data)
        return "Okay, I remembered that."

    def list_notes(self) -> str:
        user = Accounts(self.store).current_user()
        notes = [note for note in self.store.read("notes.json").get("notes", []) if note.get("user", user) == user]
        if not notes:
            return "You do not have any notes yet."
        return "Your notes are: " + "; ".join(note["text"] for note in notes)

    def delete_all(self) -> str:
        self.store.write("notes.json", {"notes": []})
        return "I deleted your notes."


def save_note(command: str) -> str:
    text = command
    for prefix in ["remember this", "save note", "make a note", "note"]:
        text = text.replace(prefix, "", 1).strip(" :")
    return Notes(JsonStore()).add(text)


def add_note(command: str) -> str:
    return save_note(command)


def list_notes() -> str:
    return Notes(JsonStore()).list_notes()
