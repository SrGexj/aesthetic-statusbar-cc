#!/usr/bin/env python3
"""CLI tool for configuring Aesthetic StatusBar."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from aesthetic_statusbar.config import (
    CONFIG_FILE,
    DEFAULT_CONFIG,
    load_config,
    save_config,
    init_config,
)
from aesthetic_statusbar.colors import PALETTES
from aesthetic_statusbar.pets import PET_COLLECTIONS

SETTINGS_FILE = Path.home() / ".claude" / "settings.json"

STATUSBAR_COMMAND = "aesthetic-statusbar-run"


def cmd_init(args):
    print(init_config())


def cmd_show(args):
    print(json.dumps(load_config(), indent=2, ensure_ascii=False))


def cmd_set(args):
    cfg = load_config()

    if args.palette is not None:
        if args.palette not in PALETTES:
            print(f"Unknown palette '{args.palette}'. Available: {', '.join(PALETTES.keys())}")
            sys.exit(1)
        cfg["palette"] = args.palette

    if args.pet is not None:
        if args.pet not in PET_COLLECTIONS:
            print(f"Unknown pet '{args.pet}'. Available: {', '.join(PET_COLLECTIONS.keys())}")
            sys.exit(1)
        cfg["pet"] = args.pet

    if args.bar_width is not None:
        cfg["bar_width"] = args.bar_width

    if args.separator is not None:
        cfg["separator"] = args.separator

    if args.enable is not None:
        for key in args.enable:
            if key in cfg["show"]:
                cfg["show"][key] = True

    if args.disable is not None:
        for key in args.disable:
            if key in cfg["show"]:
                cfg["show"][key] = False

    if args.order is not None:
        valid = [o for o in args.order.split(",") if o in DEFAULT_CONFIG["order"]]
        if valid:
            cfg["order"] = valid

    save_config(cfg)
    print(f"Config saved to {CONFIG_FILE}")


def cmd_reset(args):
    save_config(DEFAULT_CONFIG)
    print(f"Config reset to defaults at {CONFIG_FILE}")


def cmd_list(args):
    if args.what == "palettes":
        print("Available palettes:")
        for name in PALETTES:
            print(f"  - {name}")
    elif args.what == "pets":
        print("Available pets:")
        for name, frames in PET_COLLECTIONS.items():
            if frames:
                print(f"  - {name}: {frames[0]}")
            else:
                print(f"  - {name}: (disabled)")
    elif args.what == "modules":
        print("Toggleable modules:")
        for key in DEFAULT_CONFIG["show"]:
            print(f"  - {key}")


def cmd_setup(args):
    action = args.setup_action

    if action == "install":
        cmd_setup_install()
    elif action == "uninstall":
        cmd_setup_uninstall()
    elif action == "update":
        cmd_setup_update()


def cmd_setup_install():
    init_config()

    cmd = STATUSBAR_COMMAND
    try:
        result = shutil.which(cmd)
    except Exception:
        result = None

    if not result:
        print(f"Warning: '{cmd}' not found in PATH. Make sure the package is installed via pipx/pip.")

    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                s = json.load(f)
            current = s.get("statusLine", {}).get("command", "")
            if current == cmd:
                print(f"settings.json already configured with '{cmd}'")
                return
            if current:
                print(f"Replacing existing statusLine command: {current}")
            s["statusLine"] = {"type": "command", "command": cmd}
            with open(SETTINGS_FILE, "w") as f:
                json.dump(s, f, indent=2, ensure_ascii=False)
            print(f"settings.json updated — statusLine set to '{cmd}'")
        except Exception as e:
            print(f"Error updating settings.json: {e}")
    else:
        print(f"settings.json not found at {SETTINGS_FILE}")
        print(f"Add this manually:")
        print(f'  "statusLine": {{"type": "command", "command": "{cmd}"}}')

    print("\nRestart Claude Code to see the status bar.")


def cmd_setup_uninstall():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                s = json.load(f)
            if "statusLine" in s:
                old = s.pop("statusLine")
                with open(SETTINGS_FILE, "w") as f:
                    json.dump(s, f, indent=2, ensure_ascii=False)
                print(f"Removed statusLine from settings.json (was: {old})")
            else:
                print("No statusLine found in settings.json")
        except Exception as e:
            print(f"Error updating settings.json: {e}")

    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        print(f"Removed config at {CONFIG_FILE}")
    else:
        print("No config file to remove")

    print("\nRestart Claude Code to apply changes.")


def cmd_setup_update():
    import subprocess

    curl_dir = Path.home() / ".claude" / "aesthetic-statusbar"

    if curl_dir.exists() and (curl_dir / "run.py").exists():
        print("Detected curl install at", curl_dir)
        print("Re-running curl installer...")
        try:
            subprocess.run(
                ["bash", "-c", "curl -fsSL https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/install.sh | bash"],
                check=True,
            )
        except Exception as e:
            print(f"Update failed: {e}")
        return

    try:
        result = shutil.which("pipx")
    except Exception:
        result = None

    if result:
        print("Detected pipx install, updating...")
        try:
            subprocess.run(
                ["pipx", "upgrade", "aesthetic-statusbar"],
                check=True,
            )
            print("Updated via pipx!")
        except subprocess.CalledProcessError:
            print("pipx upgrade failed, trying reinstall...")
            subprocess.run(
                ["pipx", "install", "--force", "git+https://github.com/SrGexj/aesthetic-statusbar-cc.git"],
                check=True,
            )
            print("Reinstalled via pipx!")
        return

    print("Could not detect install method. Update manually:")
    print("  pipx:  pipx upgrade aesthetic-statusbar")
    print("  curl:  curl -fsSL https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/install.sh | bash")
    print("  pip:   pip install --upgrade git+https://github.com/SrGexj/aesthetic-statusbar-cc.git")


def cmd_run(args):
    from aesthetic_statusbar.renderer import render
    print(render())


def main():
    parser = argparse.ArgumentParser(
        prog="aesthetic-statusbar",
        description="Aesthetic StatusBar for Claude Code",
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Create default config file")
    p_init.set_defaults(func=cmd_init)

    p_show = sub.add_parser("show", help="Show current config")
    p_show.set_defaults(func=cmd_show)

    p_set = sub.add_parser("set", help="Set config values")
    p_set.add_argument("--palette", help="Color palette name")
    p_set.add_argument("--pet", help="Pet companion name")
    p_set.add_argument("--bar-width", type=int, dest="bar_width", help="Progress bar width")
    p_set.add_argument("--separator", help="Segment separator string")
    p_set.add_argument("--enable", nargs="+", help="Enable modules")
    p_set.add_argument("--disable", nargs="+", help="Disable modules")
    p_set.add_argument("--order", help="Comma-separated module order")
    p_set.set_defaults(func=cmd_set)

    p_reset = sub.add_parser("reset", help="Reset config to defaults")
    p_reset.set_defaults(func=cmd_reset)

    p_list = sub.add_parser("list", help="List available options")
    p_list.add_argument("what", choices=["palettes", "pets", "modules"], help="What to list")
    p_list.set_defaults(func=cmd_list)

    p_run = sub.add_parser("run", help="Run the statusbar renderer (for testing)")
    p_run.set_defaults(func=cmd_run)

    p_setup = sub.add_parser("setup", help="Install, update, or uninstall")
    p_setup.add_argument(
        "setup_action",
        choices=["install", "uninstall", "update"],
        help="Action to perform",
    )
    p_setup.set_defaults(func=cmd_setup)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()