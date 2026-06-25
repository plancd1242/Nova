from __future__ import annotations

from dataclasses import dataclass

from nova.backups import BackupManager


@dataclass(frozen=True)
class BackupStatus:
    status: str
    latest: str


def get_backup_status(manager: BackupManager | None = None) -> BackupStatus:
    manager = manager or BackupManager()
    files = manager.list_backup_files()
    if not files:
        return BackupStatus("Ready", "N/A")
    return BackupStatus("Ready", files[0].name)
