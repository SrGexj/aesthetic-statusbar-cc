"""Codex CLI adapter.

Codex has no statusline hook: `/statusline` only picks from a fixed list of
built-in items, so a custom renderer cannot run inside its TUI. What Codex does
leave behind is a rollout file per session (`~/.codex/sessions/**/rollout-*.jsonl`)
holding the same numbers Claude Code hands to a statusline command: token usage,
context window, rate limits and cache hits. This module reads the rollout of the
session running in the current directory and shapes it like a Claude snapshot, so
the bar can be painted somewhere else — tmux, the terminal title, a spare pane.
"""

import json
import os
import sqlite3
import time
from pathlib import Path

from .formatters import fmt_tokens

# Only the tail of a rollout matters: the last token_count and turn_context.
# Rollouts of long sessions run into megabytes, so never read the whole file.
TAIL_BYTES = 512 * 1024


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def read_codex_config() -> dict:
    """Parse the handful of top-level scalars we need out of config.toml."""
    cfg = {}
    path = codex_home() / "config.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return cfg

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            # Table headers start the nested sections; everything we want is above them.
            break
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        cfg[key.strip()] = value.strip().strip('"').strip("'")
    return cfg


def _state_db() -> Path:
    """Newest state_N.sqlite — Codex bumps N when it migrates the schema."""
    dbs = sorted(codex_home().glob("state_*.sqlite"))
    return dbs[-1] if dbs else codex_home() / "state.sqlite"


def find_thread(cwd: str = None) -> dict:
    """Most recent Codex session, preferring one started in this directory."""
    cwd = cwd or os.getcwd()
    rows = []
    try:
        con = sqlite3.connect(f"file:{_state_db()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        rows = [
            dict(r)
            for r in con.execute(
                "SELECT rollout_path, cwd, model, reasoning_effort, updated_at_ms "
                "FROM threads WHERE archived = 0 "
                "ORDER BY updated_at_ms DESC LIMIT 50"
            )
        ]
        con.close()
    except Exception:
        rows = []

    if not rows:
        rows = _scan_rollouts()

    for row in rows:
        if row.get("cwd") == cwd:
            return row
    return rows[0] if rows else {}


def _scan_rollouts() -> list:
    """Fallback when the thread store is unreadable: newest files on disk."""
    sessions = codex_home() / "sessions"
    try:
        files = sorted(
            sessions.glob("**/rollout-*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:20]
    except OSError:
        return []

    rows = []
    for path in files:
        cwd = ""
        try:
            with open(path, encoding="utf-8") as f:
                head = json.loads(f.readline() or "{}")
            cwd = (head.get("payload") or {}).get("cwd", "")
        except Exception:
            pass
        rows.append({"rollout_path": str(path), "cwd": cwd})
    return rows


def read_rollout(path: str) -> dict:
    """Last token_count and turn_context events of a rollout."""
    if not path:
        return {}
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            if size > TAIL_BYTES:
                f.seek(size - TAIL_BYTES)
                f.readline()  # The first line of a tail read is usually cut in half.
            raw = f.read().decode("utf-8", "replace")
    except OSError:
        return {}

    out = {}
    for line in reversed(raw.splitlines()):
        if "token_count" not in line and "turn_context" not in line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        payload = entry.get("payload") or {}
        if entry.get("type") == "turn_context" and "turn_context" not in out:
            out["turn_context"] = payload
        elif payload.get("type") == "token_count" and "token_count" not in out:
            out["token_count"] = payload
        if len(out) == 2:
            break
    return out


def window_label(minutes) -> str:
    """'5h' for a 300-minute window, '7d' for a weekly one, and so on."""
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return ""
    if minutes < 60:
        return f"{minutes}m"
    if minutes < 1440:
        return f"{minutes // 60}h"
    return f"{minutes // 1440}d"


def get_rate_data(token_count: dict) -> dict:
    """Codex reports its limits as primary/secondary, each with its own window."""
    limits = token_count.get("rate_limits") or {}
    primary = limits.get("primary") or {}
    secondary = limits.get("secondary") or {}

    # The shorter window goes in the first slot, so the bar reads like it does
    # under Claude Code: tighter limit on the left.
    windows = [w for w in (primary, secondary) if w.get("used_percent") is not None]
    windows.sort(key=lambda w: w.get("window_minutes") or 0)
    first = windows[0] if windows else {}
    second = windows[1] if len(windows) > 1 else {}

    return {
        "pct_5h": first.get("used_percent"),
        "reset_5h": first.get("resets_at"),
        "label_5h": window_label(first.get("window_minutes")) or "use",
        "pct_7d": second.get("used_percent"),
        "reset_7d": second.get("resets_at"),
        "label_7d": window_label(second.get("window_minutes")) or "",
    }


def get_context_suffix(token_count: dict) -> str:
    info = token_count.get("info") or {}
    size = info.get("model_context_window") or 0
    last = info.get("last_token_usage") or {}
    used = (last.get("input_tokens") or 0) + (last.get("output_tokens") or 0)
    if not size or not used:
        return ""
    return f"({fmt_tokens(used)}/{fmt_tokens(size)})"


def get_cache_data(token_count: dict) -> dict:
    """Codex reports cached input tokens, but never why a prompt missed the cache."""
    last = (token_count.get("info") or {}).get("last_token_usage") or {}
    inp = last.get("input_tokens") or 0
    if not inp:
        return {}
    cached = last.get("cached_input_tokens") or 0
    return {
        "warm": cached > 0,
        "ttl": None,
        "expires_at": None,
        "hit_ratio": cached / inp,
        "misses": 0,
        "last_cause": None,
        "miss_causes": {},
    }


def get_effort(thread: dict, turn_context: dict, config: dict) -> str:
    settings = (turn_context.get("collaboration_mode") or {}).get("settings") or {}
    for value in (
        settings.get("reasoning_effort"),
        turn_context.get("reasoning_effort"),
        thread.get("reasoning_effort"),
        config.get("model_reasoning_effort"),
    ):
        if value:
            return value
    return "?"


def codex_snapshot(cwd: str = None, rollout_path: str = None) -> dict:
    # A hook payload names the session's own rollout, which beats guessing from
    # the working directory: two Codex sessions can share one.
    thread = {} if rollout_path else find_thread(cwd)
    rollout = read_rollout(rollout_path or thread.get("rollout_path", ""))
    token_count = rollout.get("token_count") or {}
    turn_context = rollout.get("turn_context") or {}
    config = read_codex_config()

    model = turn_context.get("model") or thread.get("model") or config.get("model") or "?"

    return {
        "model": model,
        "ctx_suffix": get_context_suffix(token_count),
        "effort": get_effort(thread, turn_context, config),
        "rate": get_rate_data(token_count),
        "cache": get_cache_data(token_count),
        "session_age": _age(thread),
    }


def _age(thread: dict) -> float:
    updated = thread.get("updated_at_ms")
    if not updated:
        return 0.0
    return max(0.0, time.time() - updated / 1000)


def hook_line(payload: dict) -> str:
    """The bar for a Stop-hook payload, which names its own session."""
    from .renderer import render_snapshot

    snap = codex_snapshot(
        cwd=payload.get("cwd"),
        rollout_path=payload.get("transcript_path") or None,
    )
    if snap.get("model") in ("", "?") and payload.get("model"):
        snap["model"] = payload["model"]
    return render_snapshot(snap)


def hook_main() -> None:
    """Codex Stop hook: print the bar into the response area after each turn.

    Codex has no command-backed statusline, but a Stop hook may return a
    `systemMessage`, which the TUI prints and the model never sees. It is not
    the bottom bar — it is the closest thing Codex offers to one.

    Anything that goes wrong here must stay invisible: a hook that fails or
    stalls is a hook that gets in the way of the session it decorates.
    """
    import json as _json
    import sys as _sys

    try:
        raw = _sys.stdin.read()
        payload = _json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    try:
        line = hook_line(payload)
    except Exception:
        _sys.exit(0)

    body = {"systemMessage": line} if line else {}

    # Codex swallows a hook's output, so there is no other way to see what it
    # was handed. Set AESTHETIC_HOOK_DEBUG to a path to find out.
    debug = os.environ.get("AESTHETIC_HOOK_DEBUG")
    if debug:
        try:
            with open(debug, "a", encoding="utf-8") as fh:
                fh.write(_json.dumps({"payload": payload, "output": body}, ensure_ascii=False) + "\n")
        except OSError:
            pass

    if body:
        _json.dump(body, _sys.stdout)
    _sys.exit(0)
