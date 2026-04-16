"""Progress bar renderer."""

from .colors import RESET, bg_color_for_pct


def progress_bar(pct: float, pal: dict, width: int = 14) -> str:
    bg_fill = bg_color_for_pct(pct, pal)
    white = pal["white_fg"]
    dim_fg = pal["dim_fg"]
    bg_empty = pal["bg_empty"]

    filled = int(round(pct / 100 * width))
    pct_str = f"{pct:.0f}%"
    pct_len = len(pct_str)
    center = width // 2
    lbl_start = center - pct_len // 2
    lbl_end = lbl_start + pct_len

    result = ""
    for i in range(width):
        in_label = lbl_start <= i < lbl_end
        in_fill = i < filled
        bg = bg_fill if in_fill else bg_empty
        if in_label:
            fg = white if in_fill else dim_fg
            result += bg + fg + pct_str[i - lbl_start]
        else:
            result += bg + " "

    return result + RESET