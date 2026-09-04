"""Main statusbar renderer."""

from .colors import RESET, DIM, get_palette, color_for_pct, effort_color
from .pets import get_pet_frame
from .bars import progress_bar
from .formatters import format_reset, fmt_tokens, cache_cause_label
from .data import (
    read_stdin,
    get_rate_data,
    read_settings,
    get_model,
    get_context_suffix,
    get_effort,
    get_git_info,
    get_cache_data,
)
from .config import load_config
from .version_check import get_update


def render_cache(cache: dict, pal: dict) -> str:
    """Prompt-cache health: hit ratio, time to cold, and why it last missed."""
    if not cache["warm"]:
        cause = cache["last_cause"]
        label = cache_cause_label(cause) if cause else "cold"
        return f"{pal['red_light']}\u26a1 cold: {label}{RESET}"

    ratio = cache["hit_ratio"]
    if ratio is None:
        head = f"{pal['cyan']}\u26a1 warm{RESET}"
    else:
        pct = ratio * 100
        head = f"{color_for_pct(100 - pct, pal)}\u26a1 {pct:.0f}%{RESET}"

    ttl_left = format_reset(cache["expires_at"])
    if ttl_left:
        head += f" {pal['white_dim']}{ttl_left}{RESET}"

    if cache["misses"]:
        cause = cache["last_cause"]
        label = cache_cause_label(cause) if cause else "unknown"
        head += f" {DIM}\u2717{cache['misses']} {label}{RESET}"

    return head


def render() -> str:
    stdin_data = read_stdin()
    settings = read_settings()
    cfg = load_config()
    pal = get_palette(cfg["palette"])

    pet_frame = get_pet_frame(cfg["pet"]) if cfg["show"].get("pet", True) and cfg["pet"] != "none" else ""
    git_text, git_ok = get_git_info() if cfg["show"].get("git", True) else ("", False)
    model = get_model(stdin_data, settings) if cfg["show"].get("model", True) else ""
    ctx_suffix = get_context_suffix(stdin_data) if cfg["show"].get("context", True) else ""
    effort = get_effort(settings) if cfg["show"].get("effort", True) else ""
    rate = get_rate_data(stdin_data) if (cfg["show"].get("5h_bar", True) or cfg["show"].get("7d_bar", True)) else {}
    cache = get_cache_data(stdin_data) if cfg["show"].get("cache", True) else {}
    update = get_update() if cfg["show"].get("update", True) else ""

    sep = f" {DIM}{cfg['separator']}{RESET}"

    segments = {}

    if pet_frame:
        segments["pet"] = f"{pal['cyan']}{pet_frame}{RESET}"

    if cfg["show"].get("5h_bar", True) and rate.get("pct_5h") is not None:
        bar = progress_bar(rate["pct_5h"], pal, width=cfg["bar_width"])
        reset_str = format_reset(rate["reset_5h"]) if cfg["show"].get("reset_timer", True) else ""
        reset_fmt = f" {pal['white_dim']}{reset_str}{RESET}" if reset_str else ""
        segments["5h_bar"] = f"5h {bar}{reset_fmt}"

    if cfg["show"].get("7d_bar", True) and rate.get("pct_7d") is not None:
        bar = progress_bar(rate["pct_7d"], pal, width=cfg["bar_width"])
        reset_str = format_reset(rate["reset_7d"]) if cfg["show"].get("reset_timer", True) else ""
        reset_fmt = f" {pal['white_dim']}{reset_str}{RESET}" if reset_str else ""
        segments["7d_bar"] = f"7d {bar}{reset_fmt}"

    if cfg["show"].get("git", True):
        git_col = pal["green"] if git_ok else pal["gray"]
        segments["git"] = f"{git_col}\u25cf {git_text}{RESET}"

    if cfg["show"].get("model", True) and model:
        ctx = f"{DIM}{ctx_suffix}{RESET}" if ctx_suffix else ""
        segments["model"] = f"{pal['yellow']}{model}{ctx}{RESET}"

    if cache:
        segments["cache"] = render_cache(cache, pal)

    if update:
        segments["update"] = f"{pal['cyan']}\u2191{update}{RESET}"

    if cfg["show"].get("effort", True) and effort:
        ec = effort_color(effort, pal)
        segments["effort"] = f"{ec}effort: {effort}{RESET}"

    ordered = [segments[k] for k in cfg["order"] if k in segments]
    return sep.join(ordered)


def main():
    print(render())


if __name__ == "__main__":
    main()