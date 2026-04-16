# Aesthetic StatusBar for Claude Code

A customizable, colorful status bar for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that displays rate limit progress bars, git info, model name, effort level, and an animated pet companion — all in your terminal.

<img width="1060" height="53" alt="image" src="https://github.com/user-attachments/assets/f65b29f3-642c-40f8-a4d5-bd2704b4cbd2" />


## Features

- **Colorful progress bars** — 5h and 7d rate limits with percentage inside the bar
- **Animated pet companions** — blob, cat, ghost, robot, sparkle (or disable)
- **5 color palettes** — default, dracula, nord, solarized, catppuccin
- **Fully configurable** — toggle any module, change order, adjust bar width
- **Show/hide** — pet, 5h bar, 7d bar, git, model, effort, reset timer, context
- **Zero dependencies** — pure Python 3.8+, no pip packages needed
- **Cache fallback** — shows last known rate limits when stdin is empty

## Quick Install (curl)

One-liner to install and auto-configure your Claude Code settings:

```bash
curl -fsSL https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/install.sh | bash
```

This downloads the script to `~/.claude/aesthetic-statusbar/` and updates your `~/.claude/settings.json` automatically.

## Install via pipx (recommended)

```bash
pipx install git+https://github.com/SrGexj/aesthetic-statusbar-cc.git
```

Then init the config and update your Claude Code settings:

```bash
aesthetic-statusbar init
```

Add to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "aesthetic-statusbar-run"
  }
}
```

## Install via pip

```bash
pip install git+https://github.com/SrGexj/aesthetic-statusbar-cc.git
```

Same post-install steps as pipx.

## Manual Install

```bash
git clone https://github.com/SrGexj/aesthetic-statusbar-cc.git
cd aesthetic-statusbar-cc
pip install -e .
```

## Configuration

Config file: `~/.config/aesthetic-statusbar/config.json`

Create it with:

```bash
aesthetic-statusbar init
```

### Default config

```json
{
  "palette": "default",
  "pet": "blob",
  "bar_width": 14,
  "separator": " │ ",
  "show": {
    "pet": true,
    "5h_bar": true,
    "7d_bar": true,
    "git": true,
    "model": true,
    "effort": true,
    "reset_timer": true,
    "context": true
  },
  "order": ["pet", "5h_bar", "7d_bar", "git", "model", "effort"]
}
```

### CLI configuration

```bash
# Change palette
aesthetic-statusbar set --palette dracula

# Change pet
aesthetic-statusbar set --pet cat

# Adjust bar width
aesthetic-statusbar set --bar-width 20

# Change separator
aesthetic-statusbar set --separator " | "

# Toggle modules
aesthetic-statusbar set --disable pet 7d_bar
aesthetic-statusbar set --enable pet 7d_bar

# Reorder segments
aesthetic-statusbar set --order "git,5h_bar,7d_bar,model,effort,pet"

# View current config
aesthetic-statusbar show

# Reset to defaults
aesthetic-statusbar reset
```

### List available options

```bash
aesthetic-statusbar list palettes    # default, dracula, nord, solarized, catppuccin
aesthetic-statusbar list pets        # blob, cat, ghost, robot, sparkle, none
aesthetic-statusbar list modules     # pet, 5h_bar, 7d_bar, git, model, effort, reset_timer, context
```

## Palettes

| Palette | Style |
|---------|-------|
| `default` | Vibrant 256-color classic |
| `dracula` | Dracula theme inspired |
| `nord` | Nord frost palette |
| `solarized` | Solarized warm tones |
| `catppuccin` | Catppuccin Mocha pastels |

## Pets

| Pet | Frames |
|-----|--------|
| `blob` | ┌(^‿^)┘ └(^‿^)┐ ... |
| `cat` | (=^・ω・=) ... |
| `ghost` | ᕙ(^▿^)ᕗ ... |
| `robot` | [¬º-°]¬ ... |
| `sparkle` | ✧(≖‿≖)✧ ... |
| `none` | No pet shown |

## Modules

| Module | Description |
|--------|-------------|
| `pet` | Animated companion |
| `5h_bar` | 5-hour rate limit progress bar |
| `7d_bar` | 7-day rate limit progress bar |
| `git` | Current repo and branch |
| `model` | Active model name with context usage |
| `effort` | Current effort level (low/medium/high) |
| `reset_timer` | Time until rate limit resets |
| `context` | Token usage in model display |

## How it works

Claude Code injects JSON data (rate limits, model info, context window) via stdin to the status line command every refresh cycle. The script reads this data, falls back to a cached version if stdin is empty, and renders colored ANSI segments.

## Uninstall

### curl install

```bash
curl -fsSL https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/uninstall.sh | bash
```

### pipx / pip install

```bash
pipx uninstall aesthetic-statusbar
# or: pip uninstall aesthetic-statusbar
```

Then remove the `statusLine` key from `~/.claude/settings.json`.

## Requirements

- Python 3.8+
- Claude Code (Claude CLI)
- A terminal with 256-color support

## License

MIT
