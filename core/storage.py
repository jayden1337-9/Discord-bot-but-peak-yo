"""Crash-resistant JSON persistence shared by game systems."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

_BACKUPS_CREATED: set[Path] = set()


def atomic_json_save(data: dict[str, Any], path: Path) -> None:
    """Write JSON atomically and retain one last-known-good backup per process."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(f"{path.stem}.backup{path.suffix}")

    if path not in _BACKUPS_CREATED:
        if path.exists():
            try:
                # Only preserve a readable JSON file as the recovery snapshot.
                with path.open("r", encoding="utf-8") as current:
                    json.load(current)
                shutil.copy2(path, backup)
            except (OSError, json.JSONDecodeError):
                pass
        _BACKUPS_CREATED.add(path)

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
