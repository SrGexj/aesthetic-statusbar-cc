#!/usr/bin/env bash
set -euo pipefail

REPO_RAW="https://raw.githubusercontent.com/SrGexj/aesthetic-statusbar-cc/main"
INSTALL_DIR="${HOME}/.claude/aesthetic-statusbar"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}→${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
err()   { echo -e "${RED}✗${NC} $*" >&2; }

if [ ! -d "${INSTALL_DIR}" ]; then
    err "Aesthetic StatusBar not found. Install first:"
    echo "  curl -fsSL ${REPO_RAW}/install.sh | bash"
    exit 1
fi

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
    info "Updating ${mod}..."
    curl -fsSL "${REPO_RAW}/src/aesthetic_statusbar/${mod}" -o "${INSTALL_DIR}/src/aesthetic_statusbar/${mod}"
done

info "Updating run.py..."
cat > "${INSTALL_DIR}/run.py" << 'PYEOF'
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from aesthetic_statusbar.renderer import main
main()
PYEOF
chmod +x "${INSTALL_DIR}/run.py"

info "Updating update script..."
curl -fsSL "${REPO_RAW}/update.sh" -o "${INSTALL_DIR}/update.sh"
chmod +x "${INSTALL_DIR}/update.sh"

ok "Aesthetic StatusBar updated!"
echo "  Restart Claude Code to apply."