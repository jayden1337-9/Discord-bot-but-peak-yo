"""Crash-resistant JSON persistence shared by game systems."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

# Compatibility hook for existing tests; backups now refresh on every save.
_BACKUPS_CREATED: set[Path] = set()


def atomic_json_save(data: dict[str, Any], path: Path) -> None:
    """Write JSON atomically and refresh a last-known-good recovery snapshot."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(f"{path.stem}.backup{path.suffix}")

    if path.exists():
        backup_temp = None
        try:
            # Refresh the recovery point on every save, not only at process
            # startup, so it never trails hours of successful gameplay.
            with path.open("r", encoding="utf-8") as current:
                json.load(current)
            fd, backup_temp = tempfile.mkstemp(
                dir=str(path.parent), prefix=f"{backup.stem}-", suffix=".tmp"
            )
            with os.fdopen(fd, "wb") as target, path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            os.replace(backup_temp, backup)
            backup_temp = None
        except (OSError, json.JSONDecodeError):
            # A bad current file must never overwrite a valid recovery copy.
            pass
        finally:
            if backup_temp and os.path.exists(backup_temp):
                os.unlink(backup_temp)

    fd, temporary_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f"{path.stem}-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        # Persist the directory entry where the platform supports directory fsync.
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
