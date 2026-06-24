from __future__ import annotations

from datetime import datetime

from nova.storage import JsonStore


class Notes:
    def __init__(self, store: JsonStore):
        self.store = store

    def add(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "Tell me what note to save."
        data = self.store.read("notes.json")
        data.setdefault("notes", []).append({"text": text, "created_at": datetime.now().isoformat(timespec="seconds")})
        self.store.write("notes.json", data)
        return "Okay, I remembered that."

    def list_notes(self) -> str:
        notes = self.store.read("notes.json").get("notes", [])
        if not notes:
            return "You do not have any notes yet."
        return "Your notes are: " + "; ".join(note["text"] for note in notes)

    def delete_all(self) -> str:
        self.store.write("notes.json", {"notes": []})
        return "I deleted your notes."

