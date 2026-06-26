from __future__ import annotations

import hmac
import os
import secrets
import time
from dataclasses import dataclass


@dataclass
class Session:
    token: str
    created_at: float


class AuthManager:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.password = os.getenv("NOVA_APP_PASSWORD", "nova")
        self.using_default_password = "NOVA_APP_PASSWORD" not in os.environ
        self.cookie_name = "nova_session"

    def login(self, password: str) -> str | None:
        if not hmac.compare_digest(password, self.password):
            return None
        token = secrets.token_urlsafe(32)
        self.sessions[token] = Session(token=token, created_at=time.time())
        return token

    def logout(self, token: str | None) -> None:
        if token:
            self.sessions.pop(token, None)

    def is_valid(self, token: str | None) -> bool:
        return bool(token and token in self.sessions)

    def cookie_header(self, token: str) -> str:
        return f"{self.cookie_name}={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400"

    def clear_cookie_header(self) -> str:
        return f"{self.cookie_name}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"
