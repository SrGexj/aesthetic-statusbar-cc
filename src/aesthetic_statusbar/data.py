"""Data reading: stdin, cache, git, settings."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .formatters import fmt_tokens, pick_cache_cause

CACHE_DIR = Path.home() / ".cache" / "aesthetic-statusbar"
# Set by tests to pin the cache to one path; otherwise the file is per account.
CACHE_FILE = None


def claude_config_dir() -> Path:
    """The config dir of the Claude Code that spawned us; each account gets its own."""
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env).expanduser() if env else Path.home() / ".claude"


def get_account() -> dict:
    """The logged-in account, read from the global config next to this config dir.

    Claude Code keeps it in $CLAUDE_CONFIG_DIR/.claude.json, or ~/.claude.json
    when the variable is unset.
    """
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    path = Path(env).expanduser() / ".claude.json" if env else Path.home() / ".claude.json"
    try:
        acct = json.loads(path.read_text(encoding="utf-8")).get("oauthAccount") or {}
    except Exception:
        return {}
    uuid = acct.get("accountUuid")
    if not uuid:
        return {}
    email = acct.get("emailAddress") or ""
    return {
        "uuid": uuid,
        "email": email,
        "name": acct.get("displayName") or email.split("@")[0],
        "slot": account_slot(uuid),
    }


def account_slot(uuid: str) -> int:
    """Order in which this machine first saw the account, so two accounts never share a tint."""
    path = CACHE_DIR / "accounts.json"
    try:
        seen = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        seen = []
    if uuid not in seen:
        seen.append(uuid)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(seen), encoding="utf-8")
        except OSError:
            pass
    return seen.index(uuid)


def cache_file(account: dict) -> Path:
    """One stdin cache per account, so two accounts open at once never read each other's limits."""
    if CACHE_FILE is not None:
        return CACHE_FILE
    uuid = account.get("uuid")
    return CACHE_DIR / (f"last_stdin-{uuid[:8]}.json" if uuid else "last_stdin.json")


def read_stdin(account: dict) -> dict:
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        if not raw:
            return {}
        data = json.loads(raw)
        if data.get("rate_limits", {}).get("five_hour"):
            try:
                path = cache_file(account)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(raw, encoding="utf-8")
            except OSError:
                pass
        return data
    except Exception:
        return {}


def read_cached_stdin(account: dict) -> dict:
    try:
        return json.loads(cache_file(account).read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_rate_data(stdin_data: dict, account: dict) -> dict:
    rl = stdin_data.get("rate_limits", {})
    fh = rl.get("five_hour", {}) or {}
    sd = rl.get("seven_day", {}) or {}

    if not fh and not sd:
        cached = read_cached_stdin(account)
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
        with open(claude_config_dir() / "settings.json") as f:
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


def get_effort(stdin_data: dict, settings: dict) -> str:
    effort = stdin_data.get("effort", {})
    if isinstance(effort, dict):
        level = effort.get("level")
        if level:
            return level
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


def claude_snapshot() -> dict:
    """Everything the renderer needs, read from Claude Code's statusline payload."""
    account = get_account()
    stdin_data = read_stdin(account)
    settings = read_settings()
    return {
        "account": account,
        "model": get_model(stdin_data, settings),
        "ctx_suffix": get_context_suffix(stdin_data),
        "effort": get_effort(stdin_data, settings),
        "rate": get_rate_data(stdin_data, account),
        "cache": get_cache_data(stdin_data, account),
    }


def get_cache_data(stdin_data: dict, account: dict = None) -> dict:
    pc = stdin_data.get("prompt_cache") or {}
    if not pc:
        pc = read_cached_stdin(account or {}).get("prompt_cache") or {}
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
        "last_cause": pick_cache_cause(causes) or None,
        "miss_causes": pc.get("miss_causes") or {},
    }
