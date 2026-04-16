"""Text formatting helpers."""

from datetime import datetime, timezone


def format_reset(resets_at) -> str:
    if resets_at is None:
        return ""
    try:
        now = datetime.now(timezone.utc)
        end = datetime.fromtimestamp(resets_at, tz=timezone.utc)
        secs = max(0, int((end - now).total_seconds()))
        h, rem = divmod(secs, 3600)
        m = rem // 60
        if h > 0:
            return f"{h}h{m:02d}m"
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