"""Translate the bar's ANSI output into tmux status-line markup.

tmux does not interpret raw SGR sequences coming out of `#(command)`: it strips
them, so a bar rendered for a terminal loses every colour on the way into the
status line. Rewriting them as `#[fg=colourN]` keeps the palette intact.
"""

import re

SGR = re.compile(r"\033\[([\d;]*)m")

# Only the codes the palettes actually emit are worth translating.
NAMED = {
    "0": "default",
    "1": "bold",
    "2": "dim",
    "97": "fg=brightwhite",
}


def _style(params: str) -> str:
    codes = params.split(";") if params else ["0"]
    parts = []
    i = 0
    while i < len(codes):
        code = codes[i]
        if code in ("38", "48") and codes[i + 1 : i + 2] == ["5"] and len(codes) > i + 2:
            key = "fg" if code == "38" else "bg"
            parts.append(f"{key}=colour{codes[i + 2]}")
            i += 3
            continue
        if code in NAMED:
            parts.append(NAMED[code])
        i += 1

    return f"#[{','.join(parts)}]" if parts else ""


def ansi_to_tmux(text: str) -> str:
    """Rewrite SGR sequences as tmux styles, escaping the '#' tmux would eat."""
    out = []
    last = 0
    for match in SGR.finditer(text):
        out.append(text[last : match.start()].replace("#", "##"))
        out.append(_style(match.group(1)))
        last = match.end()
    out.append(text[last:].replace("#", "##"))
    return "".join(out) + "#[default]"
