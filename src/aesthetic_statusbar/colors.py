"""ANSI color palette and helpers."""

RESET = "\033[0m"
DIM = "\033[38;5;238m"

PALETTES = {
    "default": {
        "yellow": "\033[38;5;220m",
        "green": "\033[38;5;114m",
        "orange": "\033[38;5;208m",
        "red_light": "\033[38;5;203m",
        "red_strong": "\033[38;5;196m",
        "gray": "\033[38;5;242m",
        "cyan": "\033[38;5;117m",
        "white_dim": "\033[38;5;252m",
        "yellow_green": "\033[38;5;148m",
        "bg_green": "\033[48;5;114m",
        "bg_yellow_green": "\033[48;5;148m",
        "bg_orange": "\033[48;5;208m",
        "bg_red_light": "\033[48;5;203m",
        "bg_red_strong": "\033[48;5;196m",
        "bg_empty": "\033[48;5;236m",
        "white_fg": "\033[97m",
        "dim_fg": "\033[38;5;244m",
    },
    "dracula": {
        "yellow": "\033[38;5;228m",
        "green": "\033[38;5;120m",
        "orange": "\033[38;5;215m",
        "red_light": "\033[38;5;210m",
        "red_strong": "\033[38;5;197m",
        "gray": "\033[38;5;246m",
        "cyan": "\033[38;5;147m",
        "white_dim": "\033[38;5;254m",
        "yellow_green": "\033[38;5;186m",
        "bg_green": "\033[48;5;120m",
        "bg_yellow_green": "\033[48;5;186m",
        "bg_orange": "\033[48;5;215m",
        "bg_red_light": "\033[48;5;210m",
        "bg_red_strong": "\033[48;5;197m",
        "bg_empty": "\033[48;5;60m",
        "white_fg": "\033[97m",
        "dim_fg": "\033[38;5;246m",
    },
    "nord": {
        "yellow": "\033[38;5;222m",
        "green": "\033[38;5;150m",
        "orange": "\033[38;5;216m",
        "red_light": "\033[38;5;174m",
        "red_strong": "\033[38;5;167m",
        "gray": "\033[38;5;245m",
        "cyan": "\033[38;5;153m",
        "white_dim": "\033[38;5;253m",
        "yellow_green": "\033[38;5;179m",
        "bg_green": "\033[48;5;150m",
        "bg_yellow_green": "\033[48;5;179m",
        "bg_orange": "\033[48;5;216m",
        "bg_red_light": "\033[48;5;174m",
        "bg_red_strong": "\033[48;5;167m",
        "bg_empty": "\033[48;5;59m",
        "white_fg": "\033[97m",
        "dim_fg": "\033[38;5;245m",
    },
    "solarized": {
        "yellow": "\033[38;5;136m",
        "green": "\033[38;5;64m",
        "orange": "\033[38;5;166m",
        "red_light": "\033[38;5;160m",
        "red_strong": "\033[38;5;125m",
        "gray": "\033[38;5;244m",
        "cyan": "\033[38;5;37m",
        "white_dim": "\033[38;5;248m",
        "yellow_green": "\033[38;5;100m",
        "bg_green": "\033[48;5;64m",
        "bg_yellow_green": "\033[48;5;100m",
        "bg_orange": "\033[48;5;166m",
        "bg_red_light": "\033[48;5;160m",
        "bg_red_strong": "\033[48;5;125m",
        "bg_empty": "\033[48;5;236m",
        "white_fg": "\033[38;5;230m",
        "dim_fg": "\033[38;5;244m",
    },
    "catppuccin": {
        "yellow": "\033[38;5;221m",
        "green": "\033[38;5;157m",
        "orange": "\033[38;5;215m",
        "red_light": "\033[38;5;210m",
        "red_strong": "\033[38;5;203m",
        "gray": "\033[38;5;246m",
        "cyan": "\033[38;5;152m",
        "white_dim": "\033[38;5;254m",
        "yellow_green": "\033[38;5;185m",
        "bg_green": "\033[48;5;157m",
        "bg_yellow_green": "\033[48;5;185m",
        "bg_orange": "\033[48;5;215m",
        "bg_red_light": "\033[48;5;210m",
        "bg_red_strong": "\033[48;5;203m",
        "bg_empty": "\033[48;5;60m",
        "white_fg": "\033[97m",
        "dim_fg": "\033[38;5;246m",
    },
}


def get_palette(name: str) -> dict:
    return PALETTES.get(name, PALETTES["default"])


def color_for_pct(pct: float, pal: dict) -> str:
    if pct <= 35:
        return pal["green"]
    elif pct <= 64:
        return pal["yellow_green"]
    elif pct <= 80:
        return pal["orange"]
    elif pct <= 95:
        return pal["red_light"]
    else:
        return pal["red_strong"]


def bg_color_for_pct(pct: float, pal: dict) -> str:
    if pct <= 35:
        return pal["bg_green"]
    elif pct <= 64:
        return pal["bg_yellow_green"]
    elif pct <= 80:
        return pal["bg_orange"]
    elif pct <= 95:
        return pal["bg_red_light"]
    else:
        return pal["bg_red_strong"]


def effort_color(effort: str, pal: dict) -> str:
    e = effort.lower()
    if e in ("low", "minimal"):
        return pal["green"]
    elif e in ("medium", "normal"):
        return pal["orange"]
    else:
        return pal["red_strong"]