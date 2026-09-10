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
from aesthetic_statusbar.colors import PALETTES, enable_unicode_output
from aesthetic_statusbar.pets import PET_COLLECTIONS

SETTINGS_FILE = Path.home() / ".claude" / "settings.json"

STATUSBAR_COMMAND = "aesthetic-statusbar-run"
CODEX_COMMAND = "aesthetic-statusbar-codex"
TMUX_CONF = Path.home() / ".tmux.conf"
TMUX_MARKER = "# aesthetic-statusbar (codex)"
SHELL_MARKER = "# >>> aesthetic-statusbar (codex) >>>"
SHELL_END = "# <<< aesthetic-statusbar (codex) <<<"


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
        update_script = curl_dir / "update.sh"
        if update_script.exists():
            try:
                subprocess.run(["bash", str(update_script)], check=True)
                return
            except Exception as e:
                print(f"Local update script failed: {e}")
        print("Falling back to remote update script...")
        try:
            subprocess.run(
                ["bash", "-c", "curl -fsSL https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/update.sh | bash"],
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
    print("  curl:  curl -fsSL https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/update.sh | bash")
    print("  pip:   pip install --upgrade git+https://github.com/SrGexj/aesthetic-statusbar-cc.git")


def cmd_run(args):
    from aesthetic_statusbar.renderer import render
    print(render())


def cmd_codex(args):
    if args.codex_action == "run":
        cmd_codex_run(as_tmux=args.tmux)
    elif args.codex_action == "watch":
        from aesthetic_statusbar.watch import pane_loop, title_loop

        pane_loop() if args.pane else title_loop()
    elif args.codex_action == "install":
        cmd_codex_install()
    elif args.codex_action == "uninstall":
        cmd_codex_uninstall()


def cmd_codex_run(as_tmux: bool = False):
    from aesthetic_statusbar.codex import codex_snapshot
    from aesthetic_statusbar.renderer import render_snapshot

    line = render_snapshot(codex_snapshot())
    if as_tmux:
        from aesthetic_statusbar.tmux import ansi_to_tmux

        line = ansi_to_tmux(line)
    print(line)


def tmux_line() -> str:
    return f'set -g status-left "#({CODEX_COMMAND} --tmux)"'


TMUX_SESSION_CONF = Path.home() / ".config" / "aesthetic-statusbar" / "codex.tmux.conf"

WARP_DIR = Path.home() / ".warp"
WARP_CONFIG = WARP_DIR / "launch_configurations" / "codex-statusbar.yaml"


def tmux_session_conf() -> str:
    """A tmux config for one purpose: hold the bar under a Codex session.

    Everything tmux normally puts on the status line is turned off, so what is
    left looks like a status bar belonging to Codex rather than a multiplexer
    someone wrapped around it.
    """
    return "\n".join(
        [
            "# Written by aesthetic-statusbar — used only by the codex wrapper.",
            'set -g default-terminal "tmux-256color"',
            'set -ga terminal-overrides ",*256col*:Tc"',
            "set -g status on",
            "set -g status-position bottom",
            "set -g status-style bg=default",
            # Left, like Claude Code's own status line — and left-aligned text
            # is clipped from the right, so the pet and the bars survive a
            # narrow window while the tail segments go first.
            f'set -g status-left "#({CODEX_COMMAND} --tmux)"',
            "set -g status-left-length 400",
            'set -g status-right ""',
            "set -g status-right-length 0",
            'set -g window-status-format ""',
            'set -g window-status-current-format ""',
            "set -g status-interval 5",
            "set -g mouse on",
            "set -g escape-time 0",
            "set -g history-limit 50000",
            "",
        ]
    )


def write_tmux_session_conf():
    TMUX_SESSION_CONF.parent.mkdir(parents=True, exist_ok=True)
    TMUX_SESSION_CONF.write_text(tmux_session_conf(), encoding="utf-8")
    print(f"Wrote the codex tmux config to {TMUX_SESSION_CONF}")


def remove_tmux_session_conf():
    if TMUX_SESSION_CONF.exists():
        TMUX_SESSION_CONF.unlink()
        print(f"Removed {TMUX_SESSION_CONF}")


def warp_launch_config(cwd: str) -> str:
    """A Warp launch configuration: Codex on top, the bar in a pane below it.

    Warp paints the terminal title itself, so the title watcher is invisible
    there. A split pane is the surface Warp does leave alone.
    """
    return "\n".join(
        [
            "---",
            "name: Codex + statusbar",
            "windows:",
            "  - tabs:",
            "      - title: codex",
            "        layout:",
            "          split_direction: horizontal",
            "          panes:",
            f"            - cwd: {cwd}",
            "              commands:",
            "                - exec: codex",
            f"            - cwd: {cwd}",
            "              commands:",
            f"                - exec: {CODEX_COMMAND} --pane",
            "",
        ]
    )


def write_warp_config(cwd: str = None):
    cwd = cwd or os.getcwd()
    WARP_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    WARP_CONFIG.write_text(warp_launch_config(cwd), encoding="utf-8")
    print(f"Wrote a Warp launch configuration to {WARP_CONFIG}")
    print("  Open it from the command palette: 'Launch Configuration' > Codex + statusbar")


def remove_warp_config():
    if WARP_CONFIG.exists():
        WARP_CONFIG.unlink()
        print(f"Removed {WARP_CONFIG}")


def shell_rc() -> Path:
    shell = os.path.basename(os.environ.get("SHELL", "")) or "zsh"
    if shell == "bash":
        return Path.home() / ".bashrc"
    return Path.home() / ".zshrc"


def shell_function() -> str:
    """Wrap `codex` so the bar is simply there, the way it is under Claude Code.

    With tmux around, Codex runs inside a throwaway session whose only piece of
    chrome is the bar, pinned to the bottom of the window. Without tmux there is
    nowhere to pin anything, so the terminal title is the fallback — except in
    Warp, which paints its own title at the top of the window and would put the
    bar in the last place anyone looks.
    """
    return "\n".join(
        [
            SHELL_MARKER,
            "codex() {",
            '  if [ -n "$TMUX" ]; then',
            '    command codex "$@"',
            "    return",
            "  fi",
            "  if command -v tmux > /dev/null 2>&1; then",
            f'    tmux -f "{TMUX_SESSION_CONF}" new-session -- codex "$@"',
            "    return $?",
            "  fi",
            '  if [ "$TERM_PROGRAM" = "WarpTerminal" ]; then',
            '    command codex "$@"',
            "    return",
            "  fi",
            f"  {CODEX_COMMAND} --watch &",
            "  local __statusbar_pid=$!",
            # Disowned, so the shell does not print job-control noise when the
            # watcher is killed at the end of the session.
            "  disown 2>/dev/null || true",
            '  command codex "$@"',
            "  local __statusbar_status=$?",
            '  kill "$__statusbar_pid" 2>/dev/null || true',
            "  return $__statusbar_status",
            "}",
            SHELL_END,
            "",
        ]
    )


def cmd_codex_install():
    init_config()

    if not shutil.which(CODEX_COMMAND):
        print(f"Warning: '{CODEX_COMMAND}' not found in PATH. Install the package via pipx/pip first.")

    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    if not codex_home.exists():
        print(f"Warning: no Codex home at {codex_home}. The bar will have nothing to read.")

    print("Codex has no statusline hook, so the bar is drawn outside its TUI:")
    print("  - inside tmux, on the status line")
    print("  - in Warp, in a split pane below Codex")
    print("  - anywhere else, in the terminal's title bar while codex runs")

    if shutil.which("tmux"):
        write_tmux_session_conf()
        write_tmux_config()
    else:
        print("\ntmux not installed — codex will fall back to the terminal title.")

    if WARP_DIR.exists():
        write_warp_config()

    write_shell_function()

    print(f"\nOpen a new shell (or: source {shell_rc()}) and run codex as usual.")
    print("If Codex overwrites the title, turn its own off with /terminal-title inside Codex.")


def write_shell_function():
    rc = shell_rc()
    existing = rc.read_text(encoding="utf-8") if rc.exists() else ""
    if SHELL_MARKER in existing:
        print(f"{rc} already wraps codex")
        return

    sep = "" if existing.endswith("\n") or not existing else "\n"
    rc.write_text(f"{existing}{sep}\n{shell_function()}", encoding="utf-8")
    print(f"Wrapped the codex command in {rc}")


def remove_shell_function():
    rc = shell_rc()
    if not rc.exists():
        print(f"No {rc} to clean")
        return

    lines = rc.read_text(encoding="utf-8").splitlines()
    if SHELL_MARKER not in lines or SHELL_END not in lines:
        print(f"No codex wrapper found in {rc}")
        return

    start = lines.index(SHELL_MARKER)
    end = lines.index(SHELL_END, start) + 1
    del lines[start:end]

    rc.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    print(f"Removed the codex wrapper from {rc}")


def write_tmux_config():
    block = "\n".join(
        [
            TMUX_MARKER,
            tmux_line(),
            "set -g status-left-length 400",
            "set -g status-interval 5",
            "",
        ]
    )

    existing = TMUX_CONF.read_text(encoding="utf-8") if TMUX_CONF.exists() else ""
    if TMUX_MARKER in existing:
        print(f"\n{TMUX_CONF} already has the statusbar block")
        return

    sep = "" if existing.endswith("\n") or not existing else "\n"
    TMUX_CONF.write_text(f"{existing}{sep}\n{block}", encoding="utf-8")
    print(f"\nAppended the statusbar block to {TMUX_CONF}")
    print("Reload it with:  tmux source-file ~/.tmux.conf")


def cmd_codex_uninstall():
    remove_shell_function()
    remove_warp_config()
    remove_tmux_session_conf()
    remove_tmux_config()


def remove_tmux_config():
    if not TMUX_CONF.exists():
        print(f"No {TMUX_CONF} to clean")
        return

    lines = TMUX_CONF.read_text(encoding="utf-8").splitlines()
    if TMUX_MARKER not in lines:
        print(f"No statusbar block found in {TMUX_CONF}")
        return

    start = lines.index(TMUX_MARKER)
    end = start + 1
    while end < len(lines) and lines[end].startswith("set -g status"):
        end += 1
    del lines[start:end]

    TMUX_CONF.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    print(f"Removed the statusbar block from {TMUX_CONF}")
    print("Reload it with:  tmux source-file ~/.tmux.conf")


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

    p_codex = sub.add_parser("codex", help="Use the bar with OpenAI Codex CLI")
    p_codex.add_argument(
        "codex_action",
        choices=["run", "watch", "install", "uninstall"],
        help="Print the bar once, keep it in the terminal title, or set it up / remove it",
    )
    p_codex.add_argument(
        "--tmux",
        action="store_true",
        help="With 'run', emit tmux markup instead of ANSI",
    )
    p_codex.add_argument(
        "--pane",
        action="store_true",
        help="With 'watch', fill a split pane with the coloured bar instead of the title",
    )
    p_codex.set_defaults(func=cmd_codex)

    p_setup = sub.add_parser("setup", help="Install, update, or uninstall")
    p_setup.add_argument(
        "setup_action",
        choices=["install", "uninstall", "update"],
        help="Action to perform",
    )
    p_setup.set_defaults(func=cmd_setup)

    enable_unicode_output()

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()