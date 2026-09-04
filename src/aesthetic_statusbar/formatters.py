"""Text formatting helpers."""

from datetime import datetime, timezone


def format_reset(resets_at) -> str:
    if resets_at is None:
        return ""
    try:
        now = datetime.now(timezone.utc)
        end = datetime.fromtimestamp(resets_at, tz=timezone.utc)
        secs = max(0, int((end - now).total_seconds()))
        
        d = secs // 86400
        h = (secs % 86400) // 3600
        m = (secs % 3600) // 60
        
        if d > 0:
            return f"{d}d{h:02d}h"
        elif h > 0:
            return f"{h}h{m:02d}m"
        else:
            return f"{m}m"
    except Exception:
        return ""


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        v = n / 1000
        return f"{v:.0f}k" if v == int(v) else f"{v:.1f}k"
    return str(n)

CACHE_CAUSE_LABELS = {
    "system_prompt_changed": "system",
    "tools_changed": "tools",
    "model_changed": "model",
    "messages_rewritten": "messages",
    "ttl_expired_5m": "ttl 5m",
    "ttl_expired_1h": "ttl 1h",
    "likely_server_side": "server",
    "unknown": "unknown",
}


def cache_cause_label(cause: str) -> str:
    return CACHE_CAUSE_LABELS.get(cause, cause.replace("_", " "))
