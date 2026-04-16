#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${HOME}/.claude/aesthetic-statusbar"
SETTINGS_FILE="${HOME}/.claude/settings.json"
CONFIG_DIR="${HOME}/.config/aesthetic-statusbar"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}→${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
err()   { echo -e "${RED}✗${NC} $*" >&2; }

info "Uninstalling Aesthetic StatusBar..."

if [ -d "${INSTALL_DIR}" ]; then
    rm -rf "${INSTALL_DIR}"
    ok "Removed ${INSTALL_DIR}"
else
    err "Install directory not found"
fi

if [ -f "${SETTINGS_FILE}" ]; then
    info "Removing statusLine from settings.json..."
    python3 -c "
import json
with open('${SETTINGS_FILE}') as f:
    s = json.load(f)
if 'statusLine' in s:
    del s['statusLine']
    with open('${SETTINGS_FILE}', 'w') as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
    print('Removed!')
else:
    print('Already clean.')
"
fi

echo ""
read -p "Remove config directory ${CONFIG_DIR}? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "${CONFIG_DIR}"
    ok "Removed config directory"
fi

ok "Aesthetic StatusBar uninstalled"
echo "  Restart Claude Code to apply."