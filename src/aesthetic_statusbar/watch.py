"""Keep the bar on screen while Codex runs.

Codex owns its TUI and offers no statusline hook, so the bar has to live on a
surface Codex does not draw:

- a tmux status line (see `tmux.py`),
- a split pane next to Codex, which keeps the colours,
- the terminal's title bar, which does not, so the bars are drawn with block
  characters and everything is stripped down to plain text.
"""

import os
import re
import signal
import sys
import time

ANSI = re.compile(r"\033\[[\d;]*m")

# Every surface here is redrawn wholesale, so a slow cadence is enough and
# keeps the rollout read off the hot path of whatever else is running.
DEFAULT_INTERVAL = 3.0

SET_TITLE = "\033]2;{}\007"
CLEAR = "\033[H\033[2J"


def plain(text: str) -> str:
    return ANSI.sub("", text)


def _bar(text_bars: bool) -> str:
    from .codex import codex_snapshot
    from .renderer import render_snapshot

    return render_snapshot(codex_snapshot(), text_bars=text_bars)


def title_text() -> str:
    return plain(_bar(text_bars=True)).strip()


def pane_text() -> str:
    return _bar(text_bars=False)


def _writer():
    """Write to the terminal itself: stdout may be a pipe or captured."""
    try:
        return open("/dev/tty", "w", encoding="utf-8", errors="replace")
    except OSError:
        return sys.stdout


def _loop(paint, interval: float, once: bool, on_exit=None) -> None:
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
                out.write(paint())
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
        if not once and on_exit:
            try:
                out.write(on_exit())
                out.flush()
            except OSError:
                pass


def title_loop(interval: float = DEFAULT_INTERVAL, once: bool = False) -> None:
    _loop(
        lambda: SET_TITLE.format(title_text()),
        interval,
        once,
        on_exit=lambda: SET_TITLE.format(os.path.basename(os.getcwd())),
    )


def pane_loop(interval: float = DEFAULT_INTERVAL, once: bool = False) -> None:
    """Fill a split pane with the bar, colours and all."""
    _loop(lambda: f"{CLEAR}{pane_text()}\n", interval, once)
