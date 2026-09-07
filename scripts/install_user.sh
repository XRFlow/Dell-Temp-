#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB_DIR="$HOME/.local/lib/delltemp"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

DOC_DIR="$HOME/.local/share/doc/delltemp"

mkdir -p "$LIB_DIR" "$BIN_DIR" "$APP_DIR" "$ICON_DIR" "$DOC_DIR"

python3 - "$ROOT_DIR/src/delltemp" "$LIB_DIR/delltemp" <<'PY'
import shutil
import sys
from pathlib import Path

src, dest = Path(sys.argv[1]), Path(sys.argv[2])
if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(
    src,
    dest,
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
)
PY

cat > "$BIN_DIR/delltemp" <<LAUNCHER
#!/usr/bin/env bash
export PYTHONPATH="$LIB_DIR"
exec /usr/bin/python3 -m delltemp "\$@"
LAUNCHER
chmod 755 "$BIN_DIR/delltemp"

install -m 644 "$ROOT_DIR/packaging/delltemp.svg" "$ICON_DIR/delltemp.svg"
install -m 644 "$ROOT_DIR/LICENSE" "$DOC_DIR/copyright"

cat > "$APP_DIR/delltemp.desktop" <<DESKTOP
[Desktop Entry]
Name=DellTemp
Comment=Monitor CPU/GPU temperatures and fan speeds
Exec=$BIN_DIR/delltemp
Icon=delltemp
Terminal=false
Type=Application
Categories=System;Monitor;
StartupWMClass=DellTemp
Keywords=temperature;fan;gpu;cpu;monitor;sensors;
DESKTOP

# Refresh the app menu cache when the tool exists.
if command -v update-desktop-database >/dev/null; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Installed user launcher:"
echo "  $BIN_DIR/delltemp"
echo "  $APP_DIR/delltemp.desktop"
echo "Search for DellTemp in the app grid (or log out/in if the icon is stale)."
