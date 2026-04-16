"""Animated pet companions."""

from datetime import datetime

PET_COLLECTIONS = {
    "blob": [
        "┌(^‿^)┘",
        "└(^‿^)┐",
        "ヾ(^‿^)ノ",
        "ヽ(^‿^)ノ",
        "(^‿^)ノ",
        "ヽ(^‿^)",
    ],
    "cat": [
        "(=^・ω・=)",
        "(=^・ω・^=)",
        "(^・ω・^=)",
        "(=^・ω・=)",
        "(^・ω・^=)",
        "(=^・ω・^=)",
    ],
    "ghost": [
        "ᕙ(^▿^)ᕗ",
        "ᕕ(^▿^)ᕗ",
        "╰(^▿^)╯",
        "╭(^▿^)╮",
        "ᕙ(^▿^)ᕗ",
        "ᕕ(^▿^)ᕗ",
    ],
    "robot": [
        "[¬º-°]¬",
        "[¬º-°]¬",
        "[¬°-º]¬",
        "¬[º-°¬]",
        "[¬º-°]¬",
        "[¬°-º]¬",
    ],
    "sparkle": [
        "✧(≖‿≖)✧",
        "✦(≖‿≖)✦",
        "✧(≖‿≖)✧",
        "✦(≖‿≖✦)",
        "✧(≖‿≖)✧",
        "✦(≖‿≖)✦",
    ],
    "none": [],
}


def get_pet_frame(pet_name: str) -> str:
    frames = PET_COLLECTIONS.get(pet_name, PET_COLLECTIONS["blob"])
    if not frames:
        return ""
    return frames[datetime.now().second % len(frames)]