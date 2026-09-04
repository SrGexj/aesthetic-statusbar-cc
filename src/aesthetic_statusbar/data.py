"""Data reading: stdin, cache, git, settings."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .formatters import fmt_tokens

CACHE_FILE = Path.home() / ".cache" / "aesthetic-statusbar" / "last_stdin.json"


def read_stdin() -> dict:
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        if not raw:
            return {}
        data = json.loads(raw)
        if data.get("rate_limits", {}).get("five_hour"):
            try:
                CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
                CACHE_FILE.write_text(raw, encoding="utf-8")
            except OSError:
                pass
        return data
    except Exception:
        return {}


def read_cached_stdin() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_rate_data(stdin_data: dict) -> dict:
    rl = stdin_data.get("rate_limits", {})
    fh = rl.get("five_hour", {}) or {}
    sd = rl.get("seven_day", {}) or {}

    if not fh and not sd:
        cached = read_cached_stdin()
        cached_rl = cached.get("rate_limits", {})
        fh = cached_rl.get("five_hour", {}) or {}
        sd = cached_rl.get("seven_day", {}) or {}

    return {
        "pct_5h": fh.get("used_percentage"),
        "reset_5h": fh.get("resets_at"),
        "pct_7d": sd.get("used_percentage"),
        "reset_7d": sd.get("resets_at"),
    }


def read_settings() -> dict:
    try:
        with open(Path.home() / ".claude" / "settings.json") as f:
            return json.load(f)
    except Exception:
        return {}


def get_model(stdin_data: dict, settings: dict) -> str:
    model_obj = stdin_data.get("model", {})
    if isinstance(model_obj, dict):
        name = model_obj.get("display_name") or model_obj.get("id")
        if name:
            return name
    return settings.get("model", "?")


def get_context_suffix(stdin_data: dict) -> str:
    cw = stdin_data.get("context_window", {})
    if not cw:
        return ""
    size = cw.get("context_window_size", 0)
    used_pct = cw.get("used_percentage", 0)
    used_tok = (
        int(size * used_pct / 100)
        if size and used_pct
        else (stdin_data.get("total_input_tokens", 0) + stdin_data.get("total_output_tokens", 0))
    )
    if not size:
        return ""
    return f"({fmt_tokens(used_tok)}/{fmt_tokens(size)})"


def get_effort(settings: dict) -> str:
    return settings.get("effortLevel", "?")


def get_git_info() -> tuple:
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        toplevel = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        repo = os.path.basename(toplevel)
        return f"{repo} \u00b7 {branch}", True
    except Exception:
        return "git repo not connected", False


def get_cache_data(stdin_data: dict) -> dict:
    pc = stdin_data.get("prompt_cache") or {}
    if not pc:
        pc = read_cached_stdin().get("prompt_cache") or {}
    if not pc or not pc.get("caching_observed"):
        return {}

    last = pc.get("last_miss_cause") or {}
    causes = last.get("causes") or []

    expires_at = pc.get("expires_at")
    warm = bool(pc.get("warm"))
    ttl = pc.get("ttl")
    if warm and expires_at is not None and expires_at <= time.time():
        # Data can come from the cached stdin, which may have gone stale.
        warm = False
        causes = [f"ttl_expired_{ttl}"] if ttl else causes

    return {
        "warm": warm,
        "ttl": ttl,
        "expires_at": expires_at,
        "hit_ratio": pc.get("hit_ratio"),
        "misses": pc.get("misses", 0),
        "last_cause": causes[0] if causes else None,
        "miss_causes": pc.get("miss_causes") or {},
    }
