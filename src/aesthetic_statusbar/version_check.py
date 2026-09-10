"""Background check for a newer release on GitHub.

The status line must never block on the network, so the render path only ever
reads a JSON cache. When that cache is missing or older than TTL_SECONDS, a
detached child process refreshes it for the next render.
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from . import __version__

CACHE_FILE = Path.home() / ".cache" / "aesthetic-statusbar" / "version_check.json"
PYPROJECT_URL = (
    "https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/pyproject.toml"
)
UPDATE_URL = "https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/update.sh"
CURL_INSTALL_DIR = Path.home() / ".claude" / "aesthetic-statusbar"
TTL_SECONDS = 24 * 60 * 60
FETCH_TIMEOUT = 5

_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)


def parse_version(text: str) -> tuple:
    parts = []
    for chunk in text.split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def is_newer(remote: str, local: str) -> bool:
    try:
        return parse_version(remote) > parse_version(local)
    except Exception:
        return False


def read_cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_cache(data: dict) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


def fetch_latest() -> str:
    req = urllib.request.Request(
        PYPROJECT_URL, headers={"User-Agent": f"aesthetic-statusbar/{__version__}"}
    )
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
        body = resp.read().decode("utf-8", "replace")
    match = _VERSION_RE.search(body)
    if not match:
        raise ValueError("no version field in remote pyproject.toml")
    return match.group(1)


def refresh() -> None:
    """Fetch the latest version and store it. Runs in the detached child."""
    try:
        latest = fetch_latest()
    except Exception:
        # Keep the old value, just push the next attempt one TTL away so a
        # machine that is offline does not spawn a child on every render.
        cached = read_cache()
        write_cache({"latest": cached.get("latest"), "checked_at": time.time()})
        return
    write_cache({"latest": latest, "checked_at": time.time()})


def detach_kwargs(os_name: str = None) -> dict:
    """Popen arguments that cut the child loose from this process."""
    if (os_name or os.name) == "nt":
        # start_new_session is POSIX-only; on Windows the child has to be
        # detached from the console explicitly, or it stays attached to it and
        # flashes a window on every refresh.
        return {
            "creationflags": getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        }
    return {"start_new_session": True}


def spawn_refresh() -> None:
    package_root = str(Path(__file__).resolve().parent.parent)
    env = dict(os.environ)
    env["PYTHONPATH"] = (
        package_root + os.pathsep + env["PYTHONPATH"]
        if env.get("PYTHONPATH")
        else package_root
    )
    try:
        subprocess.Popen(
            [sys.executable, "-m", "aesthetic_statusbar.version_check"],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **detach_kwargs(),
        )
    except Exception:
        pass


def git_checkout(start: Path) -> Path:
    """The repo root above `start`, or None when this is not a checkout."""
    for parent in [start] + list(start.parents):
        if (parent / ".git").exists() and (parent / "pyproject.toml").exists():
            return parent
    return None


def update_command() -> str:
    """The command that actually updates *this* install.

    A curl install has no console script on PATH, so pointing its user at
    `aesthetic-statusbar` would send them to a command that does not exist.
    """
    try:
        here = Path(__file__).resolve()
        install_dir = CURL_INSTALL_DIR.resolve()
        # Path.is_relative_to lands in 3.9; this package still claims 3.8.
        inside_curl = install_dir == here or install_dir in here.parents

        if not inside_curl:
            # An editable install runs straight out of a checkout, where
            # update.sh would overwrite a working tree instead of updating it.
            checkout = git_checkout(here)
            if checkout:
                return f"git -C {shlex.quote(str(checkout))} pull"

        if inside_curl or (install_dir / "run.py").exists():
            script = install_dir / "update.sh"
            if script.exists():
                return f"bash {shlex.quote(str(script))}"
    except Exception:
        pass

    if shutil.which("aesthetic-statusbar"):
        return "aesthetic-statusbar setup update"

    return f"curl -fsSL {UPDATE_URL} | bash"


def get_update() -> str:
    """Return the newer version available, or "" — never touches the network."""
    cached = read_cache()
    checked_at = cached.get("checked_at") or 0
    if time.time() - checked_at > TTL_SECONDS:
        spawn_refresh()

    latest = cached.get("latest")
    if latest and is_newer(latest, __version__):
        return latest
    return ""


if __name__ == "__main__":
    refresh()
