#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(uname -s)" != Linux ]]; then
  echo 'This installer registers the Linux desktop handler. macOS needs its receiving native URL application; no registration was changed.' >&2
  exit 1
fi
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/harmonic-lab.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Harmonic Lab
Exec=python3 "$root/scripts/open-harmonic-lab.py" %u
Terminal=false
NoDisplay=true
MimeType=x-scheme-handler/harmonic-lab;
EOF
xdg-mime default harmonic-lab.desktop x-scheme-handler/harmonic-lab
printf 'Harmonic Lab local handler: '
xdg-mime query default x-scheme-handler/harmonic-lab
