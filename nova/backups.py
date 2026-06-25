from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

from nova.config import BACKUP_DIR, DATA_DIR, ROOT_DIR, settings
from nova.storage import JsonStore


@dataclass(frozen=True)
class BackupRecord:
    filename: str
    created_at: str
    reason: str
    size_bytes: int


class BackupManager:
    def __init__(
        self,
        store: JsonStore | None = None,
        data_dir: Path = DATA_DIR,
        backup_dir: Path = BACKUP_DIR,
    ) -> None:
        self.store = store or JsonStore()
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._sync_default_settings()

    def create_backup(self, reason: str = "manual") -> str:
        now = datetime.now()
        filename = self._filename(now)
        path = self.backup_dir / filename
        counter = 2
        while path.exists():
            path = self.backup_dir / f"{path.stem}_{counter}.zip"
            counter += 1

        manifest = {
            "created_at": now.isoformat(timespec="seconds"),
            "reason": reason,
            "nova_backup_version": 1,
            "sources": ["data"],
        }

        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as backup:
            backup.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            for source in self._source_files():
                arcname = self._archive_name(source)
                backup.write(source, arcname)

        self._record_backup(
            BackupRecord(
                filename=path.name,
                created_at=manifest["created_at"],
                reason=reason,
                size_bytes=path.stat().st_size,
            )
        )
        removed = self.cleanup_old_backups()
        suffix = f" I also cleaned up {removed} old backup{'s' if removed != 1 else ''}." if removed else ""
        return f"Backup created: {path.name}.{suffix}"

    def status(self) -> str:
        backup_files = self.list_backup_files()
        settings_data = self.settings()
        if backup_files:
            latest = backup_files[0]
            latest_text = f" Latest backup: {latest.name}."
        else:
            latest_text = " No backups yet."
        return (
            f"Backups are {'enabled' if settings_data['enabled'] else 'disabled'}."
            f" Daily time: {settings_data['time']}."
            f" Cleanup: {settings_data['keep_days']} days."
            f"{latest_text}"
        )

    def history(self, limit: int = 8) -> str:
        backup_files = self.list_backup_files()
        if not backup_files:
            return "No backups have been created yet."
        names = [path.name for path in backup_files[:limit]]
        return "Recent backups: " + "; ".join(names)

    def cleanup_old_backups(self, keep_days: int | None = None) -> int:
        keep_days = keep_days if keep_days is not None else int(self.settings()["keep_days"])
        cutoff = datetime.now() - timedelta(days=max(0, keep_days))
        removed = 0
        for path in self.list_backup_files(oldest_first=True):
            try:
                if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
        if removed:
            self._prune_history()
        return removed

    def restore_latest(self) -> str:
        backups = self.list_backup_files()
        if not backups:
            return "I could not find any backups to restore."
        return self.restore(backups[0].name)

    def restore(self, filename: str) -> str:
        backup_path = self._resolve_backup(filename)
        if backup_path is None:
            return "I could not find that backup."

        if not self._validate_backup(backup_path):
            return "That backup did not pass safety checks, so I did not restore it."

        safety_message = self.create_backup(reason="pre_restore")
        with zipfile.ZipFile(backup_path, "r") as archive:
            for member in archive.infolist():
                if not member.filename.startswith("data/") or member.is_dir():
                    continue
                target = self.data_dir / Path(member.filename).relative_to("data")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member, "r") as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)

        return f"Restored backup: {backup_path.name}. Safety backup made first. {safety_message}"

    def settings(self) -> dict[str, Any]:
        data = self.store.read("backup_settings.json")
        data.setdefault("enabled", settings.backup_enabled)
        data.setdefault("time", settings.backup_time)
        data.setdefault("keep_days", settings.backup_keep_days)
        return data

    def set_time(self, time_text: str) -> str:
        backup_time = self._parse_time(time_text)
        if backup_time is None:
            return "Tell me the backup time like 12:00 AM, midnight, or 23:30."
        data = self.settings()
        data["time"] = backup_time
        self.store.write("backup_settings.json", data)
        return f"Daily backups are scheduled for {backup_time}."

    def set_keep_days(self, days: int) -> str:
        days = max(1, int(days))
        data = self.settings()
        data["keep_days"] = days
        self.store.write("backup_settings.json", data)
        return f"I will keep backups for {days} days."

    def list_backup_files(self, oldest_first: bool = False) -> list[Path]:
        files = sorted(
            self.backup_dir.glob("backup_*.zip"),
            key=lambda path: path.stat().st_mtime,
            reverse=not oldest_first,
        )
        return files

    def _source_files(self) -> Iterable[Path]:
        if not self.data_dir.exists():
            return []
        return (path for path in self.data_dir.rglob("*") if path.is_file())

    def _filename(self, now: datetime) -> str:
        return f"backup_{now.strftime('%Y-%m-%d_%I-%M_%p')}.zip"

    def _archive_name(self, source: Path) -> str:
        return (Path("data") / source.relative_to(self.data_dir)).as_posix()

    def _sync_default_settings(self) -> None:
        data = self.settings()
        changed = False
        for key, value in {
            "enabled": settings.backup_enabled,
            "time": settings.backup_time,
            "keep_days": settings.backup_keep_days,
        }.items():
            if key not in data:
                data[key] = value
                changed = True
        if changed:
            self.store.write("backup_settings.json", data)

    def _record_backup(self, record: BackupRecord) -> None:
        data = self.store.read("backup_history.json")
        backups = data.setdefault("backups", [])
        backups.append(
            {
                "filename": record.filename,
                "created_at": record.created_at,
                "reason": record.reason,
                "size_bytes": record.size_bytes,
            }
        )
        self.store.write("backup_history.json", data)

    def _prune_history(self) -> None:
        existing = {path.name for path in self.list_backup_files()}
        data = self.store.read("backup_history.json")
        data["backups"] = [item for item in data.get("backups", []) if item.get("filename") in existing]
        self.store.write("backup_history.json", data)

    def _resolve_backup(self, filename: str) -> Optional[Path]:
        clean = Path(filename).name
        if not clean.endswith(".zip"):
            clean += ".zip"
        path = self.backup_dir / clean
        if path.exists() and path.is_file():
            return path
        matches = sorted(self.backup_dir.glob(f"*{Path(filename).stem}*.zip"))
        return matches[-1] if matches else None

    def _validate_backup(self, path: Path) -> bool:
        try:
            with zipfile.ZipFile(path, "r") as archive:
                names = archive.namelist()
                if "manifest.json" not in names:
                    return False
                for name in names:
                    member_path = Path(name)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        return False
                    if name != "manifest.json" and not name.startswith("data/"):
                        return False
            return True
        except (OSError, zipfile.BadZipFile):
            return False

    def _parse_time(self, text: str) -> Optional[str]:
        lower = text.lower().strip()
        if "midnight" in lower:
            return "00:00"
        if "noon" in lower:
            return "12:00"

        match_12 = re.search(r"\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*(a\.?m\.?|p\.?m\.?)\b", lower)
        if not match_12:
            match_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", lower)
            if match_24:
                return f"{int(match_24.group(1)):02d}:{match_24.group(2)}"
            return None
        hour = int(match_12.group(1))
        minute = int(match_12.group(2) or "0")
        meridiem = match_12.group(3).replace(".", "")
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"
