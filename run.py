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

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("supervisor")


def git_prefix() -> list[str]:
    command = ["git"]
    token = os.getenv("GITHUB_TOKEN")
    if token:
        basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        command += ["-c", f"http.extraheader=AUTHORIZATION: basic {basic}"]
    return command + ["-C", str(ROOT)]


def update_from_github() -> bool:
    if not (ROOT / ".git").exists():
        log.warning("No .git directory found; skipping GitHub update")
        return False

    git = git_prefix()
    previous = None

    try:
        previous = subprocess.check_output(
            git + ["rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()

        pull = subprocess.run(
            git + [
                "pull", "--ff-only", "origin",
                os.getenv("GITHUB_BRANCH", "main"),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if pull.stdout:
            log.info("Git output:\n%s", pull.stdout.strip())
        if pull.returncode != 0:
            log.error("Git pull failed; current version was left unchanged")
            return False

        check = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "main.py", "cogs", "run.py"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        install = None
        if check.returncode == 0:
            install = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=ROOT,
            )

        if check.returncode != 0 or install is None or install.returncode != 0:
            log.error("Update validation failed; restoring previous code")
            subprocess.run(git + ["reset", "--hard", previous], cwd=ROOT, check=False)
            return False

        log.info("GitHub update installed successfully")
        return True

    except Exception:
        log.exception("Update failed")
        if previous:
            subprocess.run(git + ["reset", "--hard", previous], cwd=ROOT, check=False)
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
