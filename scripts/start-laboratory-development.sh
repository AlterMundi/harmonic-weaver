#!/usr/bin/env bash
# Explicit development profile; the daily launcher/profile remain separate.
set -euo pipefail
lab_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
lab_parent="$(dirname -- "$lab_root")"
export SHAPER_DIR="${SHAPER_DIR:-$lab_parent/harmonic-shaper-dev}"
export SHAPER_PYTHON="${SHAPER_PYTHON:-$SHAPER_DIR/.venv/bin/python}"
export HARMOCAP_DIR="${HARMOCAP_DIR:-$lab_parent/HarMoCAP-lab}"
export HARMOCAP_VENV="${HARMOCAP_VENV:-$lab_parent/HarMoCAP/.venv}"
export HARMOCAP_CHECKPOINT="${HARMOCAP_CHECKPOINT:-$lab_parent/HarMoCAP/harmocap-m-pose-ft2.pt}"
lab_data="${WEAVER_LAB_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/harmonic-weaver/laboratory-dev}"
printf 'Perfil desarrollo · datos por defecto: %s\n' "$lab_data"
exec "$lab_root/scripts/start-laboratory.sh" --data-dir "$lab_data" "$@"
