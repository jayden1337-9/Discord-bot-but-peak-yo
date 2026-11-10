"""Centralized environment configuration."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    token: str
    prefix: str
    owner_id: int | None
    data_dir: Path
    log_level: str
    github_branch: str

    @classmethod
    def from_env(cls) -> "Settings":
        raw_owner = os.getenv("BOT_OWNER_ID", "").strip()
        owner_id = int(raw_owner) if raw_owner.isdigit() else None
        prefix = os.getenv("COMMAND_PREFIX", ",").strip() or ","
        return cls(
            token=os.getenv("DISCORD_TOKEN", "").strip(),
            prefix=prefix,
            owner_id=owner_id,
            data_dir=Path(os.getenv("BOT_DATA_DIR", "/home/container/data")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            github_branch=os.getenv("GITHUB_BRANCH", "main").strip() or "main",
        )

    def require_token(self) -> str:
        if not self.token:
            raise RuntimeError("DISCORD_TOKEN environment variable is missing")
        return self.token
