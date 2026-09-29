#!/usr/bin/env bash
set -euo pipefail

lab_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
lab_parent="$(dirname -- "$lab_root")"
lab_python="${WEAVER_PYTHON:-$lab_root/.venv/bin/python}"
if [[ ! -x "$lab_python" && -x "$lab_parent/harmonic-weaver/.venv/bin/python" ]]; then
  lab_python="$lab_parent/harmonic-weaver/.venv/bin/python"
fi
if [[ ! -x "$lab_python" ]]; then
  echo 'Falta Python de Weaver. Crear .venv e instalar el proyecto con extras [lab], o definir WEAVER_PYTHON.' >&2
  exit 1
fi
lab_shaper="${SHAPER_DIR:-$lab_parent/harmonic-shaper-lab}"
[[ -d "$lab_shaper" ]] || lab_shaper="$lab_parent/harmonic-shaper"
lab_shaper_python="${SHAPER_PYTHON:-$lab_shaper/.venv/bin/python}"
if [[ ! -x "$lab_shaper_python" ]]; then
  lab_shaper_python="$lab_parent/harmonic-shaper/.venv/bin/python"
fi
export HARMOCAP_DIR="${HARMOCAP_DIR:-$lab_parent/HarMoCAP-lab}"
[[ -d "$HARMOCAP_DIR" ]] || export HARMOCAP_DIR="$lab_parent/HarMoCAP"
export HARMOCAP_VENV="${HARMOCAP_VENV:-$HARMOCAP_DIR/.venv}"
[[ -x "$HARMOCAP_VENV/bin/python" ]] || export HARMOCAP_VENV="$lab_parent/HarMoCAP/.venv"
lab_checkpoint="${HARMOCAP_CHECKPOINT:-$HARMOCAP_DIR/harmocap-m-pose-ft2.pt}"
[[ -f "$lab_checkpoint" ]] || lab_checkpoint="$lab_parent/HarMoCAP/harmocap-m-pose-ft2.pt"

cd -- "$lab_root/laboratory-ui"
if [[ ! -d node_modules ]]; then npm ci --no-audit --no-fund; fi
npm run build
cd -- "$lab_root"
export PYTHONPATH="$lab_root/src"
exec "$lab_python" -m harmonic_weaver.lab \
  --shaper-dir "$lab_shaper" --shaper-python "$lab_shaper_python" \
  --checkpoint "$lab_checkpoint" "$@"
