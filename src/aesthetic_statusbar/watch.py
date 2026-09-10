"""Keep the bar on screen while Codex runs.

Codex owns its TUI and offers no statusline hook, so the bar has to live on a
surface Codex does not draw: the tmux status line, or the terminal's title bar.
The title carries no colour and no background, so the segments are rendered
plain and joined with the configured separator.
"""

import os
import re
import signal
import sys
import time

ANSI = re.compile(r"\033\[[\d;]*m")

# The title is redrawn by the terminal on every write, so a slow cadence is
# enough and keeps the sqlite read off the hot path of whatever else runs.
DEFAULT_INTERVAL = 3.0

SET_TITLE = "\033]2;{}\007"


def plain(text: str) -> str:
    return ANSI.sub("", text)


def title_text() -> str:
    from .codex import codex_snapshot
    from .renderer import render_snapshot

    return plain(render_snapshot(codex_snapshot(), text_bars=True)).strip()


def _writer():
    """Write to the terminal itself: stdout may be a pipe or captured."""
    try:
        return open("/dev/tty", "w", encoding="utf-8", errors="replace")
    except OSError:
        return sys.stdout


def title_loop(interval: float = DEFAULT_INTERVAL, once: bool = False) -> None:
    out = _writer()
    stop = {"now": False}

    def handle(signum, frame):
        stop["now"] = True

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, handle)
        except (ValueError, OSError):
            pass

    try:
        while not stop["now"]:
            try:
                out.write(SET_TITLE.format(title_text()))
                out.flush()
            except OSError:
                return
            if once:
                return
            # Sleep in slices so a signal stops the loop without waiting it out.
            waited = 0.0
            while waited < interval and not stop["now"]:
                time.sleep(0.2)
                waited += 0.2
    finally:
        if not once:
            try:
                out.write(SET_TITLE.format(os.path.basename(os.getcwd())))
                out.flush()
            except OSError:
                pass
