#!/usr/bin/env python3
"""CLI tool for configuring Aesthetic StatusBar."""

import argparse
import json
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

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()