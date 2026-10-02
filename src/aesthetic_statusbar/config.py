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
        "account": True,
        "5h_bar": True,
        "7d_bar": True,
        "git": True,
        "model": True,
        "effort": True,
        "reset_timer": True,
        "context": True,
        "cache": True,
        "update": True,
    },
    # Email -> name shown in the account segment; unset accounts use their display name.
    "account_labels": {},
    "order": ["pet", "account", "5h_bar", "7d_bar", "git", "model", "cache", "effort", "update"],
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg["show"] = dict(DEFAULT_CONFIG["show"])
    cfg["account_labels"] = {}
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
            if isinstance(user.get("account_labels"), dict):
                cfg["account_labels"] = user["account_labels"]
            if "show" in user:
                for k, v in user["show"].items():
                    if k in cfg["show"]:
                        cfg["show"][k] = v
            if "order" in user:
                valid = [o for o in user["order"] if o in DEFAULT_CONFIG["order"]]
                if valid:
                    # Segments added after the user wrote their config still show up;
                    # hiding one is done through "show", not by dropping it here.
                    missing = [o for o in DEFAULT_CONFIG["order"] if o not in valid]
                    cfg["order"] = valid + missing
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