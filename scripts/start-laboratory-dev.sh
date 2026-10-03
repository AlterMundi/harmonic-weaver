#!/usr/bin/env bash
set -euo pipefail

# Deliberately separate from the everyday laboratory's process and stored state.
dev_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
dev_parent="$(dirname -- "$dev_root")"
export WEAVER_PYTHON="${WEAVER_PYTHON:-$dev_root/.venv/bin/python}"
export SHAPER_DIR="${SHAPER_DIR:-$dev_parent/harmonic-shaper-dev}"
export SHAPER_PYTHON="${SHAPER_PYTHON:-$SHAPER_DIR/.venv/bin/python}"
export HARMOCAP_DIR="${HARMOCAP_DIR:-$dev_parent/HarMoCAP-lab}"
export HARMOCAP_VENV="${HARMOCAP_VENV:-$dev_parent/HarMoCAP/.venv}"
export HARMOCAP_CHECKPOINT="${HARMOCAP_CHECKPOINT:-$dev_parent/HarMoCAP/harmocap-m-pose-ft2.pt}"
dev_data="${LAB_DEV_DATA_DIR:-${WEAVER_LAB_DATA_DIR:-$HOME/.local/share/harmonic-weaver/laboratory-dev}}"

for dev_python in "$WEAVER_PYTHON" "$SHAPER_PYTHON"; do
  if [[ ! -x "$dev_python" ]]; then
    echo "Falta el entorno propio: $dev_python. Ver docs/laboratory/RUNNING.md." >&2
    exit 1
  fi
done

if [[ "${1:-}" == "--check" ]]; then
  "$WEAVER_PYTHON" -c 'import harmonic_weaver.lab, cv2, fastapi, soundfile; print("Weaver: dependencias disponibles")'
  "$SHAPER_PYTHON" -c 'import harmonic_shaper.audio_engine, harmonic_shaper.capture_recovery; print("Shaper: audio y recuperación disponibles")'
  printf 'Web: http://127.0.0.1:8875\nShaper: http://127.0.0.1:8185\nDatos: %s\n' "$dev_data"
  exit 0
fi

printf 'Desarrollo: %s\nShaper: %s\nDatos por defecto: %s\n' "$dev_root" "$SHAPER_DIR" "$dev_data"
exec "$dev_root/scripts/start-laboratory.sh" \
  --port 8875 --shaper-port 8185 --data-dir "$dev_data" "$@"
