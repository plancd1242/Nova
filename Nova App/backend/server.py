from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auth import AuthManager
from providers import StatusProvider

AUTH = AuthManager()
PROVIDER = StatusProvider()
NOVA_APP = None


def get_nova_app():
    global NOVA_APP
    if NOVA_APP is None:
        from nova.app import NovaApp

        NOVA_APP = NovaApp()
    return NOVA_APP


class NovaHandler(BaseHTTPRequestHandler):
    server_version = "NovaPWA/1.0"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/session":
            self._json({"authenticated": self._authenticated()})
            return
        if path == "/api/status":
            if not self._require_auth():
                return
            self._json(PROVIDER.snapshot())
            return
        if path == "/api/events":
            if not self._require_auth():
                return
            self._events()
            return
        if path == "/api/camera/stream":
            if not self._require_auth():
                return
            self._camera_stream()
            return
        self._static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        payload = self._read_json()
        if path == "/api/login":
            token = AUTH.login(str(payload.get("password", "")))
            if not token:
                self._json({"ok": False, "error": "Invalid password"}, HTTPStatus.UNAUTHORIZED)
                return
            self._json({"ok": True}, headers={"Set-Cookie": AUTH.cookie_header(token)})
            return
        if path == "/api/logout":
            AUTH.logout(self._session_token())
            self._json({"ok": True}, headers={"Set-Cookie": AUTH.clear_cookie_header()})
            return
        if not self._require_auth():
            return
        if path == "/api/command":
            command = str(payload.get("command", "")).strip()
            if not command:
                self._json({"ok": False, "response": "Type a command."}, HTTPStatus.BAD_REQUEST)
                return
            response = get_nova_app().handle_command(command)
            self._json({"ok": True, "response": response, "status": PROVIDER.snapshot()})
            return
        if path == "/api/backup/manual":
            response = get_nova_app().backups.create_backup(reason="pwa_manual")
            self._json({"ok": True, "response": response, "status": PROVIDER.snapshot()})
            return
        if path == "/api/settings":
            self._json({"ok": True, "response": "Settings endpoint is ready for future persistence.", "status": PROVIDER.snapshot()})
            return
        self._json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:
        print(f"[Nova App] {self.address_string()} {format % args}")

    def _events(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        while True:
            try:
                data = json.dumps(PROVIDER.snapshot())
                self.wfile.write(f"event: status\ndata: {data}\n\n".encode("utf-8"))
                self.wfile.flush()
                time.sleep(2)
            except (BrokenPipeError, ConnectionResetError):
                break

    def _camera_stream(self) -> None:
        self._json({"ok": False, "message": "Camera Offline"}, HTTPStatus.SERVICE_UNAVAILABLE)

    def _static(self, path: str) -> None:
        if path in {"/", ""}:
            path = "/index.html"
        target = (FRONTEND / path.lstrip("/")).resolve()
        if not str(target).startswith(str(FRONTEND.resolve())) or not target.exists() or not target.is_file():
            target = FRONTEND / "index.html"
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache" if target.name == "index.html" else "public, max-age=3600")
        self.end_headers()
        self.wfile.write(target.read_bytes())

    def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _session_token(self) -> str | None:
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            name, _, value = part.strip().partition("=")
            if name == AUTH.cookie_name:
                return value
        return None

    def _authenticated(self) -> bool:
        return AUTH.is_valid(self._session_token())

    def _require_auth(self) -> bool:
        if self._authenticated():
            return True
        self._json({"ok": False, "error": "Authentication required"}, HTTPStatus.UNAUTHORIZED)
        return False


def main() -> None:
    host = os.getenv("NOVA_APP_HOST", "127.0.0.1")
    port = int(os.getenv("NOVA_APP_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), NovaHandler)
    print(f"Nova App running at http://{host}:{port}")
    if AUTH.using_default_password:
        print("WARNING: using default local password. Set NOVA_APP_PASSWORD before Cloudflare deployment.")
    else:
        print("Password is configured from NOVA_APP_PASSWORD.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nNova App stopped.")


if __name__ == "__main__":
    main()
