from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
import socket
import subprocess
import time
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from nova.config import DATA_DIR, settings
from nova.router_status import DEFAULT_RADIOS, GUEST_RADIOS, GUEST_TO_MAIN, MAIN_RADIOS, RouterStateStore
from nova.storage import JsonStore


LABELS = {
    "smart_connect": "Smart Connect:",
    "ofdma": "OFDMA:",
    "main_24": "2.4Ghz:",
    "main_5g1": "5GHz-1:",
    "main_5g2": "5GHz-2:",
    "guest_24": "2.4GHz:",
    "guest_5g1": "5GHz-1:",
    "guest_5g2": "5GHz-2:",
}

SAFE_ERROR = {
    "disabled": "Router control is disabled.",
    "not_configured": "Router control is not configured.",
    "playwright": "Playwright is unavailable, so router control has been disabled.",
    "unreachable": "I couldn't reach the router. No changes were made.",
    "login": "I couldn't verify the router login.",
    "page_changed": "The router page appears to have changed.",
    "verify": "I couldn't confirm that the setting changed.",
    "timeout": "The router operation timed out. No success was reported.",
}


@dataclass(frozen=True)
class RouterResult:
    ok: bool
    message: str
    radios: dict[str, bool | None] | None = None
    speed_test: dict[str, Any] | None = None


class RouterControl:
    def __init__(self, store: JsonStore | None = None) -> None:
        self.store = store or JsonStore()
        self.state = RouterStateStore(self.store)
        self.timeout_ms = max(5, settings.router_timeout_seconds) * 1000

    def status(self) -> RouterResult:
        ready = self._preflight(change=False)
        if not ready.ok:
            return ready
        try:
            with self._session() as session:
                radios = session.read_all_radios()
                self.state.save_radios(radios, "status")
                self._log("status", "success", final_state=radios)
                return RouterResult(True, "Router status: " + self.state.snapshot().summary(), radios)
        except RouterControlError as exc:
            return self._failure("status", exc)

    def inspect(self) -> RouterResult:
        ready = self._preflight(change=False)
        if not ready.ok:
            return ready
        try:
            with self._session() as session:
                info = session.inspect_safe_structure()
                self._log("inspect", "success", page=info.get("page"), final_state=info)
                return RouterResult(True, "Router inspection complete. Found: " + "; ".join(info.get("found", [])))
        except RouterControlError as exc:
            return self._failure("inspect", exc)

    def turn_main_wifi_off(self, confirmed: bool = False) -> RouterResult:
        ready = self._preflight(change=True)
        if not ready.ok:
            return ready
        if settings.router_require_off_confirmation and not confirmed:
            return RouterResult(
                False,
                "Turning off Wi-Fi will disconnect wireless devices. Say: Confirm Wi-Fi off.",
            )
        if settings.router_require_ethernet and not self._ethernet_likely():
            return RouterResult(False, "I do not have enough evidence that Nova is on Ethernet. No changes were made.")

        try:
            with self._session() as session:
                radios = session.read_all_radios()
                self.state.save_radios(radios, "pre_wifi_off_status")
                if all(radios.get(key) is False for key in MAIN_RADIOS):
                    return RouterResult(True, "Wi-Fi is already off, so I didn't change anything.", radios)
                self.state.save_previous_main_state(radios)

                desired = {"smart_connect": False, "main_24": False, "main_5g1": False, "main_5g2": False}
                final = session.apply_radios(desired)
                if not all(final.get(key) is False for key in MAIN_RADIOS):
                    raise RouterControlError("verify", SAFE_ERROR["verify"])
                self.state.save_radios(final, "main_wifi_off")
                self._notify("Router Wi-Fi", "Main Wi-Fi radios were turned off.")
                return RouterResult(True, "Main Wi-Fi is off. I verified all three wireless radios are disabled.", final)
        except RouterControlError as exc:
            return self._failure("main_wifi_off", exc)

    def restore_main_wifi(self) -> RouterResult:
        ready = self._preflight(change=True)
        if not ready.ok:
            return ready
        try:
            with self._session() as session:
                current = session.read_all_radios()
                if any(current.get(key) is True for key in MAIN_RADIOS):
                    return RouterResult(True, "Wi-Fi is already on, so I didn't change anything.", current)
                desired = self.state.previous_main_state()
                final = session.apply_radios(desired)
                if not any(final.get(key) is True for key in MAIN_RADIOS):
                    raise RouterControlError("verify", SAFE_ERROR["verify"])
                self.state.save_radios(final, "main_wifi_restore")
                self._notify("Router Wi-Fi", "Main Wi-Fi radios were restored.")
                return RouterResult(True, "Wi-Fi is back on. I restored the saved main-radio settings.", final)
        except RouterControlError as exc:
            return self._failure("main_wifi_restore", exc)

    def set_guest(self, guest_key: str, enabled: bool) -> RouterResult:
        ready = self._preflight(change=True)
        if not ready.ok:
            return ready
        if guest_key not in GUEST_RADIOS:
            return RouterResult(False, "I do not know that guest network.")
        try:
            with self._session() as session:
                radios = session.read_all_radios()
                current = radios.get(guest_key)
                guest_name = self._guest_number_name(guest_key)
                if current is enabled:
                    return RouterResult(True, f"{guest_name} is already {'on' if enabled else 'off'}.", radios)

                desired = {guest_key: enabled}
                main_key = GUEST_TO_MAIN[guest_key]
                main_was_off = radios.get(main_key) is False
                if enabled and main_was_off:
                    desired[main_key] = True

                final = session.apply_radios(desired)
                if final.get(guest_key) is not enabled:
                    raise RouterControlError("verify", SAFE_ERROR["verify"])
                if enabled and final.get(main_key) is not True:
                    raise RouterControlError("verify", SAFE_ERROR["verify"])
                self.state.save_radios(final, f"{guest_key}_{'on' if enabled else 'off'}")

                if enabled and main_was_off:
                    message = f"The {MAIN_RADIOS[main_key]} radio was off, so I turned it on and enabled {guest_name}."
                else:
                    message = f"{guest_name} is now {'on' if enabled else 'off'}."
                self._notify("Router guest Wi-Fi", message)
                return RouterResult(True, message, final)
        except RouterControlError as exc:
            return self._failure(f"{guest_key}_{enabled}", exc)

    def speed_test(self) -> RouterResult:
        ready = self._preflight(change=False)
        if not ready.ok:
            return ready
        try:
            with self._session() as session:
                result = session.run_speed_test()
                self.state.save_speed_test(result)
                message = (
                    "The speed test is complete. "
                    f"Your download speed is {result.get('download_mbps')} megabits per second, "
                    f"your upload speed is {result.get('upload_mbps')} megabits per second, "
                    f"and your ping is {result.get('ping_ms')} milliseconds."
                )
                self._notify("Router speed test", "Speed test completed.")
                return RouterResult(True, message, speed_test=result)
        except RouterControlError as exc:
            return self._failure("speed_test", exc)

    def _preflight(self, change: bool) -> RouterResult:
        if not settings.router_control_enabled:
            return RouterResult(False, SAFE_ERROR["disabled"])
        if settings.router_automation_engine.strip().lower() != "playwright":
            return RouterResult(False, "Router control currently supports Playwright only.")
        if not settings.router_url or not settings.router_local_password:
            return RouterResult(False, SAFE_ERROR["not_configured"])
        if not self._playwright_available():
            return RouterResult(False, SAFE_ERROR["playwright"])
        if not self._router_reachable():
            self._log("preflight", "failure", error_category="unreachable", reachable=False, requested_new_state={"change": change})
            return RouterResult(False, SAFE_ERROR["unreachable"])
        return RouterResult(True, "Router control is ready.")

    def _session(self) -> "RouterSession":
        return RouterSession(self.timeout_ms, self._log)

    def _playwright_available(self) -> bool:
        try:
            import playwright.sync_api  # type: ignore

            return True
        except Exception:
            return False

    def _router_reachable(self) -> bool:
        try:
            request = Request(settings.router_url, method="GET", headers={"User-Agent": "Nova local router check"})
            with urlopen(request, timeout=min(5, settings.router_timeout_seconds)) as response:
                return response.status < 500
        except Exception:
            host = urlparse(settings.router_url).hostname
            if not host:
                return False
            try:
                with socket.create_connection((host, 80), timeout=3):
                    return True
            except Exception:
                return False

    def _ethernet_likely(self) -> bool:
        if not settings.router_require_ethernet:
            return True
        host = urlparse(settings.router_url).hostname or "192.168.0.1"
        commands = [
            ["ip", "route", "get", host],
            ["route", "-n", "get", host],
        ]
        for command in commands:
            try:
                result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=2)
                text = (result.stdout + result.stderr).lower()
                if any(name in text for name in (" eth", "enp", "eno", "end", "ethernet")):
                    return True
                if any(name in text for name in (" wlan", "wifi", "wi-fi")):
                    return False
            except Exception:
                continue
        return True

    def _failure(self, operation: str, exc: "RouterControlError") -> RouterResult:
        self._log(operation, "failure", error_category=exc.category)
        return RouterResult(False, exc.safe_message)

    def _log(
        self,
        operation: str,
        status: str,
        *,
        reachable: bool | None = None,
        page: str | None = None,
        previous_state: dict[str, Any] | None = None,
        requested_new_state: dict[str, Any] | None = None,
        final_state: dict[str, Any] | None = None,
        error_category: str | None = None,
    ) -> None:
        data = self.store.read("router_diagnostics.json")
        events = data.setdefault("events", [])
        events.append(
            {
                "operation": operation,
                "status": status,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "reachable": reachable,
                "page": page,
                "previous_state": previous_state,
                "requested_new_state": requested_new_state,
                "final_state": final_state,
                "error_category": error_category,
            }
        )
        data["events"] = events[-100:]
        self.store.write("router_diagnostics.json", data)

    def _notify(self, title: str, message: str) -> None:
        try:
            from nova.notifications import NotificationManager

            NotificationManager(self.store).notify(title, message, level="router")
        except Exception:
            pass

    def _guest_number_name(self, guest_key: str) -> str:
        return {"guest_24": "guest network 1", "guest_5g1": "guest network 2", "guest_5g2": "guest network 3"}[guest_key]


class RouterSession:
    def __init__(self, timeout_ms: int, logger: Any) -> None:
        self.timeout_ms = timeout_ms
        self._log = logger
        self.playwright = None
        self.browser = None
        self.page = None

    def __enter__(self) -> "RouterSession":
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright

            self.PlaywrightTimeoutError = PlaywrightTimeoutError
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=settings.router_headless)
            context = self.browser.new_context(ignore_https_errors=True)
            self.page = context.new_page()
            self.page.set_default_timeout(self.timeout_ms)
            self._login()
            return self
        except RouterControlError:
            self.close()
            raise
        except Exception as exc:
            self.close()
            raise RouterControlError("playwright", f"{SAFE_ERROR['playwright']} {type(exc).__name__}") from exc

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self) -> None:
        for item in (self.browser, self.playwright):
            try:
                if item is not None:
                    item.close() if hasattr(item, "close") else item.stop()
            except Exception:
                pass

    def _login(self) -> None:
        page = self._page()
        try:
            page.goto(settings.router_url, wait_until="domcontentloaded")
            page.get_by_text("Local Password:", exact=False).wait_for()
            password_field = self._password_field()
            password_field.fill(settings.router_local_password)
            self._click_text("LOG IN")
            page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
            self._wait_for_any_text(["Network Map", "Wireless", "Advanced", "Internet", "Game Center"])
            self._log("login", "success", reachable=True, page="dashboard")
        except Exception as exc:
            raise RouterControlError("login", SAFE_ERROR["login"]) from exc

    def inspect_safe_structure(self) -> dict[str, Any]:
        page = self._page()
        found: list[str] = []
        for text in ["Network Map", "Game Center", "Internet", "Wireless", "Advanced", "Guest Network", "SAVE"]:
            try:
                if page.get_by_text(text, exact=False).count() > 0:
                    found.append(text)
            except Exception:
                pass
        return {"page": "inspection", "found": found}

    def read_all_radios(self) -> dict[str, bool | None]:
        self._open_wireless_page()
        radios = {}
        for key in ("smart_connect", "ofdma", "main_24", "main_5g1", "main_5g2"):
            radios[key] = self._read_toggle(LABELS[key])
        self._open_guest_network_page()
        for key in ("guest_24", "guest_5g1", "guest_5g2"):
            radios[key] = self._read_toggle(LABELS[key])
        self._log("read_radios", "success", page="Wireless", final_state=radios)
        return radios

    def apply_radios(self, desired: dict[str, bool]) -> dict[str, bool | None]:
        previous = self.read_all_radios()
        main_changes = {key: value for key, value in desired.items() if key in {"smart_connect", "ofdma", *MAIN_RADIOS}}
        guest_changes = {key: value for key, value in desired.items() if key in GUEST_RADIOS}

        if main_changes:
            self._open_wireless_page()
            for key, value in main_changes.items():
                self._set_toggle(LABELS[key], value)
            self._save()

        if guest_changes:
            self._open_guest_network_page()
            for key, value in guest_changes.items():
                self._set_toggle(LABELS[key], value)
            self._save()

        time.sleep(1)
        final = self.read_all_radios()
        self._log("apply_radios", "success", page="Wireless", previous_state=previous, requested_new_state=desired, final_state=final)
        for key, value in desired.items():
            if final.get(key) is not value:
                raise RouterControlError("verify", SAFE_ERROR["verify"])
        return final

    def run_speed_test(self) -> dict[str, Any]:
        page = self._page()
        try:
            self._click_text("Network Map")
            page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
            self._wait_for_any_text(["Speed Test", "Download", "Upload", "Ping"])
        except Exception as exc:
            self._debug_screenshot("speed_test_not_found")
            raise RouterControlError("page_changed", "I couldn't find the router's speed-test feature. The router page may have changed.") from exc

        if self._text_visible("running") or self._text_visible("testing"):
            start_note = "already_running"
        else:
            start_note = "opened"

        deadline = time.time() + max(settings.router_timeout_seconds, 30)
        result: dict[str, Any] | None = None
        while time.time() < deadline:
            text = self._safe_body_text()
            result = self._parse_speed_result(text)
            if result:
                self._log("speed_test", "success", page="Network Map", requested_new_state={"mode": start_note}, final_state=result)
                return result
            time.sleep(2)
        raise RouterControlError("timeout", "The speed test could not be completed. No router settings were changed.")

    def _open_wireless_page(self) -> None:
        try:
            self._click_text("Wireless")
            self._wait_for_any_text(["Smart Connect:", "2.4Ghz:", "5GHz-1:", "Wireless Settings"])
        except Exception as exc:
            self._debug_screenshot("wireless_page_changed")
            raise RouterControlError("page_changed", "The Wireless page appears to have changed.") from exc

    def _open_guest_network_page(self) -> None:
        page = self._page()
        try:
            if page.get_by_text("Guest Network", exact=False).count() > 0:
                self._click_text("Guest Network")
            else:
                self._click_text("Wireless Settings")
                self._click_text("Guest Network")
            self._wait_for_any_text(["Guest Network", "2.4GHz:", "5GHz-1:", "5GHz-2:"])
        except Exception as exc:
            self._debug_screenshot("guest_page_changed")
            raise RouterControlError("page_changed", "The Guest Network page appears to have changed.") from exc

    def _read_toggle(self, label: str) -> bool | None:
        value = self._page().evaluate(
            """
            (label) => {
              const norm = s => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
              const wanted = norm(label);
              const nodes = Array.from(document.querySelectorAll('body *')).filter(el => norm(el.innerText || el.textContent) === wanted);
              const root = nodes[0]?.closest('tr, li, .row, .form-group, .setting, div') || nodes[0]?.parentElement;
              if (!root) return null;
              const controls = Array.from(root.querySelectorAll('input, button, [role="switch"], [aria-checked], .switch, .toggle'));
              for (const el of controls) {
                if (el.type === 'checkbox') return !!el.checked;
                const aria = el.getAttribute('aria-checked');
                if (aria === 'true') return true;
                if (aria === 'false') return false;
                const cls = (el.className || '').toString().toLowerCase();
                if (cls.includes('on') || cls.includes('enable')) return true;
                if (cls.includes('off') || cls.includes('disable')) return false;
              }
              return null;
            }
            """,
            label,
        )
        if value is None:
            self._debug_screenshot("toggle_not_found")
            raise RouterControlError("page_changed", f"I couldn't find the {label} toggle.")
        return bool(value)

    def _set_toggle(self, label: str, enabled: bool) -> None:
        current = self._read_toggle(label)
        if current is enabled:
            return
        clicked = self._page().evaluate(
            """
            ([label, enabled]) => {
              const norm = s => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
              const wanted = norm(label);
              const nodes = Array.from(document.querySelectorAll('body *')).filter(el => norm(el.innerText || el.textContent) === wanted);
              const root = nodes[0]?.closest('tr, li, .row, .form-group, .setting, div') || nodes[0]?.parentElement;
              if (!root) return false;
              const controls = Array.from(root.querySelectorAll('input, button, [role="switch"], [aria-checked], .switch, .toggle'));
              const control = controls[0];
              if (!control) return false;
              control.click();
              return true;
            }
            """,
            [label, enabled],
        )
        if not clicked:
            self._debug_screenshot("toggle_change_failed")
            raise RouterControlError("page_changed", f"I couldn't change the {label} toggle.")
        time.sleep(0.3)

    def _save(self) -> None:
        try:
            self._click_text("SAVE")
            self._confirm_dialog_if_present()
            self._page().wait_for_load_state("networkidle", timeout=min(self.timeout_ms, 10000))
        except Exception as exc:
            raise RouterControlError("verify", "Save or Apply failed. No success was reported.") from exc

    def _confirm_dialog_if_present(self) -> None:
        page = self._page()
        try:
            if page.get_by_text("The wireless function is off", exact=False).count() > 0:
                for text in ("OK", "Ok", "Confirm", "Yes"):
                    try:
                        self._click_text(text)
                        return
                    except Exception:
                        pass
        except Exception:
            pass

    def _password_field(self) -> Any:
        page = self._page()
        candidates = [
            page.locator("input[type='password']").first,
            page.get_by_label("Local Password:", exact=False),
            page.locator("input").first,
        ]
        for candidate in candidates:
            try:
                candidate.wait_for(timeout=3000)
                return candidate
            except Exception:
                continue
        raise RouterControlError("login", SAFE_ERROR["login"])

    def _click_text(self, text: str) -> None:
        locator = self._page().get_by_text(text, exact=False).first
        locator.wait_for()
        locator.click()

    def _wait_for_any_text(self, values: list[str]) -> None:
        deadline = time.time() + settings.router_timeout_seconds
        while time.time() < deadline:
            for value in values:
                try:
                    if self._page().get_by_text(value, exact=False).count() > 0:
                        return
                except Exception:
                    pass
            time.sleep(0.25)
        raise RouterControlError("page_changed", SAFE_ERROR["page_changed"])

    def _text_visible(self, value: str) -> bool:
        try:
            return self._page().get_by_text(value, exact=False).count() > 0
        except Exception:
            return False

    def _safe_body_text(self) -> str:
        try:
            return self._page().locator("body").inner_text(timeout=2000)
        except Exception:
            return ""

    def _parse_speed_result(self, text: str) -> dict[str, Any] | None:
        lower = text.lower()
        if not all(word in lower for word in ("download", "upload")):
            return None
        download = _number_near(text, "download")
        upload = _number_near(text, "upload")
        ping = _number_near(text, "ping") or _number_near(text, "latency")
        if download is None or upload is None:
            return None
        return {"download_mbps": download, "upload_mbps": upload, "ping_ms": ping or "N/A"}

    def _page(self) -> Any:
        if self.page is None:
            raise RouterControlError("playwright", SAFE_ERROR["playwright"])
        return self.page

    def _debug_screenshot(self, label: str) -> None:
        if not settings.router_debug_screenshots or self.page is None:
            return
        try:
            target_dir = DATA_DIR / "router_screenshots"
            target_dir.mkdir(parents=True, exist_ok=True)
            safe_label = re.sub(r"[^a-zA-Z0-9_-]+", "_", label)[:40]
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_label}.png"
            self.page.screenshot(path=str(target_dir / filename), full_page=False)
        except Exception:
            pass


class RouterControlError(Exception):
    def __init__(self, category: str, safe_message: str) -> None:
        super().__init__(safe_message)
        self.category = category
        self.safe_message = safe_message


def _number_near(text: str, label: str) -> str | None:
    pattern = re.compile(rf"{re.escape(label)}[^0-9]{{0,80}}([0-9]+(?:\\.[0-9]+)?)", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1)


def get_router_control() -> RouterControl:
    return RouterControl()
