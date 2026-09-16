#!/usr/bin/env bash
# Wire Auto PiP into Hyprland and Chromium. Safe to run more than once.

set -euo pipefail

PLUGIN_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${HOME:?}"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME_DIR/.config}"
EXT_ID="bnggkdcelikbblbcmklabddbllkehach"
HYPRLAND_LUA="$CONFIG_HOME/hypr/hyprland.lua"
FLAGS_FILE="$CONFIG_HOME/chromium-flags.conf"
HOST_DIR="$CONFIG_HOME/chromium/NativeMessagingHosts"
HOST_JSON="$HOST_DIR/com.webtom.auto_pip.json"
MARKER="plugins/webtom.auto-pip/auto-pip.lua"

chmod +x "$PLUGIN_DIR/native-host.py" "$PLUGIN_DIR/pip-cmd.py"

mkdir -p "$HOST_DIR"
cat >"$HOST_JSON" <<EOF
{
  "name": "com.webtom.auto_pip",
  "description": "Omarchy Auto PiP native host",
  "path": "$PLUGIN_DIR/native-host.py",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXT_ID/"
  ]
}
EOF
echo "Wrote $HOST_JSON"

mkdir -p "$(dirname "$FLAGS_FILE")"
touch "$FLAGS_FILE"
python3 - "$FLAGS_FILE" "$PLUGIN_DIR/extension" <<'PY'
import sys
from pathlib import Path

flags_path = Path(sys.argv[1])
extension = sys.argv[2]
needed = [
    f"--load-extension={extension}",
    "--remote-debugging-address=127.0.0.1",
    "--remote-debugging-port=19222",
    "--remote-allow-origins=*",
]
lines = [line for line in flags_path.read_text().splitlines() if line.strip()]
out = []
seen_load = False
for line in lines:
    if line.startswith("--load-extension="):
        parts = [p for p in line.split("=", 1)[1].split(",") if p]
        if extension not in parts:
            parts.append(extension)
        out.append("--load-extension=" + ",".join(parts))
        seen_load = True
        continue
    if line.startswith("--remote-debugging-address="):
        continue
    if line.startswith("--remote-debugging-port="):
        continue
    if line.startswith("--remote-allow-origins="):
        continue
    out.append(line)
if not seen_load:
    out.append(f"--load-extension={extension}")
out.extend(needed[1:])
flags_path.write_text("\n".join(out) + "\n")
print(f"Updated {flags_path}")
PY

if [[ -f $HYPRLAND_LUA ]] && ! grep -Fq "$MARKER" "$HYPRLAND_LUA"; then
  cat >>"$HYPRLAND_LUA" <<EOF

-- Auto PiP: picture-in-picture playing videos when you leave their workspace.
local auto_pip = (os.getenv("HOME") or "") .. "/.config/omarchy/plugins/webtom.auto-pip/auto-pip.lua"
local auto_pip_file = io.open(auto_pip, "r")
if auto_pip_file then
  auto_pip_file:close()
  dofile(auto_pip)
end
EOF
  echo "Updated $HYPRLAND_LUA"
else
  echo "Hyprland already loads Auto PiP (or $HYPRLAND_LUA is missing)"
fi

if command -v omarchy >/dev/null 2>&1; then
  omarchy plugin enable webtom.auto-pip >/dev/null 2>&1 || true
fi

echo
echo "Auto PiP is installed."
echo "Restart Chromium/YouTube so the extension and DevTools port load, then: hyprctl reload"
