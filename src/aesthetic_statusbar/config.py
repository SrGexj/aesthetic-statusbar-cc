"""Configuration loader."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "aesthetic-statusbar"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "palette": "default",
    "pet": "blob",
    "bar_width": 14,
    "separator": " │ ",
    "show": {
        "pet": True,
        "5h_bar": True,
        "7d_bar": True,
        "git": True,
        "model": True,
        "effort": True,
        "reset_timer": True,
        "context": True,
    },
    "order": ["pet", "5h_bar", "7d_bar", "git", "model", "effort"],
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg["show"] = dict(DEFAULT_CONFIG["show"])
    cfg["order"] = list(DEFAULT_CONFIG["order"])

    if CONFIG_FILE.exists():
        try:
            user = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if "palette" in user:
                cfg["palette"] = user["palette"]
            if "pet" in user:
                cfg["pet"] = user["pet"]
            if "bar_width" in user:
                cfg["bar_width"] = user["bar_width"]
            if "separator" in user:
                cfg["separator"] = user["separator"]
            if "show" in user:
                for k, v in user["show"].items():
                    if k in cfg["show"]:
                        cfg["show"][k] = v
            if "order" in user:
                valid = [o for o in user["order"] if o in DEFAULT_CONFIG["order"]]
                cfg["order"] = valid if valid else cfg["order"]
        except Exception:
            pass

    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def init_config() -> str:
    if CONFIG_FILE.exists():
        return f"Config already exists at {CONFIG_FILE}"
    save_config(DEFAULT_CONFIG)
    return f"Created default config at {CONFIG_FILE}"