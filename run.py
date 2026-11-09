"""Wispbyte entry point: restart the bot after crashes and controlled reloads."""

import base64
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESTART_FLAG = ROOT / ".restart_requested"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("supervisor")


def git_environment() -> tuple[dict[str, str], list[str]]:
    env = os.environ.copy()
    token = env.get("GITHUB_TOKEN")
    remote = env.get("GITHUB_REPOSITORY", "jayden1337-9/Discord-bot-but-peak-yo")
    branch = env.get("GITHUB_BRANCH", "main")

    command = ["git"]
    if token:
        basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        command += ["-c", f"http.extraheader=AUTHORIZATION: basic {basic}"]

    return env, command + ["-C", str(ROOT), "pull", "--ff-only", "origin", branch]


def update_from_github() -> bool:
    if not (ROOT / ".git").exists():
        log.warning("No .git directory found; skipping GitHub update")
        return False

    try:
        env, command = git_environment()
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if result.stdout:
            log.info("Git output:\n%s", result.stdout.strip())
        if result.returncode != 0:
            log.error("Git pull failed; keeping the currently installed version")
            return False

        check = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "main.py", "cogs", "run.py"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if check.returncode != 0:
            log.error("Updated code failed its syntax check; not restarting into it")
            return False

        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=ROOT,
        )
        if install.returncode != 0:
            log.error("Dependency installation failed")
            return False

        log.info("Update checks completed")
        return True
    except Exception:
        log.exception("Update failed")
        return False


def main() -> None:
    delay = 3
    max_delay = 60

    while True:
        RESTART_FLAG.unlink(missing_ok=True)
        log.info("Starting Discord bot")
        try:
            process = subprocess.Popen([sys.executable, str(ROOT / "main.py")], cwd=ROOT)
            code = process.wait()
        except KeyboardInterrupt:
            log.info("Supervisor stopped")
            return
        except Exception:
            log.exception("Could not start bot process")
            code = 1

        if RESTART_FLAG.exists():
            RESTART_FLAG.unlink(missing_ok=True)
            log.info("Controlled reload requested; pulling GitHub updates")
            update_from_github()
            delay = 3
            continue

        log.warning("Bot process exited with code %s; restarting in %s seconds", code, delay)
        time.sleep(delay)
        delay = min(delay * 2, max_delay)


if __name__ == "__main__":
    main()
