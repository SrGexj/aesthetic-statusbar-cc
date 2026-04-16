#!/usr/bin/env bash
set -euo pipefail

REPO_RAW="https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main"
INSTALL_DIR="${HOME}/.claude/aesthetic-statusbar"
SETTINGS_FILE="${HOME}/.claude/settings.json"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}→${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}!${NC} $*"; }
err()   { echo -e "${RED}✗${NC} $*" >&2; }

command -v python3 >/dev/null 2>&1 || { err "python3 is required"; exit 1; }

info "Installing Aesthetic StatusBar for Claude Code..."

mkdir -p "${INSTALL_DIR}/src/aesthetic_statusbar"
mkdir -p "${HOME}/.config/aesthetic-statusbar"

MODULES=(
    __init__.py
    colors.py
    pets.py
    bars.py
    formatters.py
    data.py
    config.py
    renderer.py
    cli.py
)

for mod in "${MODULES[@]}"; do
    info "Downloading ${mod}..."
    curl -fsSL "${REPO_RAW}/src/aesthetic_statusbar/${mod}" -o "${INSTALL_DIR}/src/aesthetic_statusbar/${mod}"
done

cat > "${INSTALL_DIR}/run.py" << 'PYEOF'
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from aesthetic_statusbar.renderer import main
main()
PYEOF
chmod +x "${INSTALL_DIR}/run.py"

if [ ! -f "${HOME}/.config/aesthetic-statusbar/config.json" ]; then
    curl -fsSL "${REPO_RAW}/config/default.json" -o "${HOME}/.config/aesthetic-statusbar/config.json"
    ok "Default config created"
else
    warn "Existing config found — keeping it"
fi

LAUNCH_CMD="python3 ${INSTALL_DIR}/run.py"

if [ -f "${SETTINGS_FILE}" ]; then
    if python3 -c "
import json, sys
with open('${SETTINGS_FILE}') as f:
    s = json.load(f)
if s.get('statusLine', {}).get('command', '') == '${LAUNCH_CMD}':
    sys.exit(0)
sys.exit(1)
"; then
        ok "settings.json already configured"
    else
        info "Updating settings.json..."
        python3 -c "
import json
with open('${SETTINGS_FILE}') as f:
    s = json.load(f)
s['statusLine'] = {'type': 'command', 'command': '${LAUNCH_CMD}'}
with open('${SETTINGS_FILE}', 'w') as f:
    json.dump(s, f, indent=2, ensure_ascii=False)
print('Updated!')
"
        ok "settings.json updated"
    fi
else
    warn "settings.json not found at ${SETTINGS_FILE}"
    warn "Add this to your Claude Code settings manually:"
    echo ""
    echo '  "statusLine": {'
    echo '    "type": "command",'
    echo "    \"command\": \"${LAUNCH_CMD}\""
    echo '  }'
    echo ""
fi

echo ""
ok "Aesthetic StatusBar installed!"
echo ""
echo "  Configure:  aesthetic-statusbar init    (if installed via pipx)"
echo "              aesthetic-statusbar set --palette dracula --pet cat"
echo "              aesthetic-statusbar list palettes"
echo ""
echo "  Or edit:    ~/.config/aesthetic-statusbar/config.json"
echo ""
echo "  Restart Claude Code to see the status bar."