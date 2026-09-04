# Aesthetic StatusBar for Claude Code

A customizable, colorful status bar for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that displays rate limit progress bars, git info, model name, effort level, and an animated pet companion — all in your terminal.

<img width="1060" height="53" alt="image" src="https://github.com/user-attachments/assets/f65b29f3-642c-40f8-a4d5-bd2704b4cbd2" />


## Features

- **Colorful progress bars** — 5h and 7d rate limits with percentage inside the bar
- **Animated pet companions** — blob, cat, ghost, robot, sparkle (or disable)
- **5 color palettes** — default, dracula, nord, solarized, catppuccin
- **Fully configurable** — toggle any module, change order, adjust bar width
- **Show/hide** — pet, 5h bar, 7d bar, git, model, effort, reset timer, context, prompt cache, update notice
- **Zero dependencies** — pure Python 3.8+, no pip packages needed
- **Cache fallback** — shows last known rate limits when stdin is empty
- **Update notice** — `↑1.2.0` when a new release is out, checked once a day in the background

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
    "context": true,
    "cache": true,
    "update": true
  },
  "order": ["pet", "5h_bar", "7d_bar", "git", "model", "cache", "effort", "update"]
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
aesthetic-statusbar list modules     # pet, 5h_bar, 7d_bar, git, model, effort, reset_timer, context, cache, update
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
| `cache` | Prompt cache health: hit ratio, time left before it goes cold, and the likely cause of the last miss |
| `update` | `↑1.2.0` when a newer release is available (hidden otherwise) |

### Prompt cache

The `cache` module reads Claude Code's `prompt_cache` field, so you can see when the prompt cache is being invalidated and why.

```
⚡ 95% 44m          warm — 95% hit ratio, goes cold in 44 minutes
⚡ 44% 44m ✗2 ttl 1h warm, but 2 misses this session, the last one from the TTL expiring
⚡ cold: tools       cold right now because the tool definitions changed
```

Causes come from Claude Code's own heuristic: `system` (system prompt changed), `tools`, `model`, `messages` (history rewritten), `ttl 5m` / `ttl 1h` (idle past the TTL), `server`, `unknown`.

### Update notifications

When a newer release exists, the bar shows `↑1.2.0`. The version is fetched
from GitHub at most once a day by a detached background process — the render
path only ever reads `~/.cache/aesthetic-statusbar/version_check.json`, so it
never waits on the network. Turn it off with:

```bash
aesthetic-statusbar set --disable update
```

Then update with:

```bash
aesthetic-statusbar setup update
# or, for a curl install:
curl -fsSL https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main/update.sh | bash
```

## How it works

Claude Code injects JSON data (rate limits, model info, context window, prompt cache) via stdin to the status line command every refresh cycle. The script reads this data, falls back to a cached version if stdin is empty, and renders colored ANSI segments.

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
