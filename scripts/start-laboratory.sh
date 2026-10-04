#!/usr/bin/env bash
set -euo pipefail

lab_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
lab_parent="$(dirname -- "$lab_root")"
lab_error() { printf '%s\n' "$1" >&2; exit 1; }
lab_describe=false
lab_check=false
lab_arguments=()
lab_shaper_cli=''
lab_shaper_python_cli=''
lab_checkpoint_cli=''
while (($#)); do
  case "$1" in
    --describe) lab_describe=true; shift ;;
    --check) lab_check=true; shift ;;
    --shaper-dir|--shaper-python|--checkpoint)
      lab_flag="$1"
      (($#>=2)) || lab_error "Falta valor de $lab_flag"
      case "$lab_flag" in
        --shaper-dir) lab_shaper_cli="$2" ;;
        --shaper-python) lab_shaper_python_cli="$2" ;;
        --checkpoint) lab_checkpoint_cli="$2" ;;
      esac
      shift 2 ;;
    --shaper-dir=*) lab_shaper_cli="${1#*=}"; shift ;;
    --shaper-python=*) lab_shaper_python_cli="${1#*=}"; shift ;;
    --checkpoint=*) lab_checkpoint_cli="${1#*=}"; shift ;;
    *) lab_arguments+=("$1"); shift ;;
  esac
done

lab_python="${WEAVER_PYTHON:-$lab_root/.venv/bin/python}"
if [[ -z "${WEAVER_PYTHON:-}" && ! -x "$lab_python" && -x "$lab_parent/harmonic-weaver/.venv/bin/python" ]]; then
  lab_python="$lab_parent/harmonic-weaver/.venv/bin/python"
fi
[[ -x "$lab_python" ]] || lab_error "Python Weaver no ejecutable: $lab_python. Crear .venv con extra [lab] o definir WEAVER_PYTHON."
lab_shaper="${lab_shaper_cli:-${SHAPER_DIR:-$lab_parent/harmonic-shaper}}"
if [[ -z "$lab_shaper_cli" && -z "${SHAPER_DIR:-}" && ! -d "$lab_shaper" ]]; then lab_shaper="$lab_parent/harmonic-shaper"; fi
[[ -d "$lab_shaper" ]] || lab_error "Checkout Shaper no encontrado: $lab_shaper"
lab_shaper_python="${lab_shaper_python_cli:-${SHAPER_PYTHON:-$lab_shaper/.venv/bin/python}}"
if [[ -z "$lab_shaper_python_cli" && -z "${SHAPER_PYTHON:-}" && ! -x "$lab_shaper_python" ]]; then lab_shaper_python="$lab_parent/harmonic-shaper/.venv/bin/python"; fi
[[ -x "$lab_shaper_python" ]] || lab_error "Python Shaper no ejecutable: $lab_shaper_python"
lab_harmocap="${HARMOCAP_DIR:-$lab_parent/HarMoCAP}"
if [[ -z "${HARMOCAP_DIR:-}" && ! -d "$lab_harmocap" ]]; then lab_harmocap="$lab_parent/HarMoCAP"; fi
[[ -d "$lab_harmocap" ]] || lab_error "Checkout HarMoCAP no encontrado: $lab_harmocap"
lab_harmocap_venv="${HARMOCAP_VENV:-$lab_harmocap/.venv}"
if [[ -z "${HARMOCAP_VENV:-}" && ! -x "$lab_harmocap_venv/bin/python" ]]; then lab_harmocap_venv="$lab_parent/HarMoCAP/.venv"; fi
[[ -x "$lab_harmocap_venv/bin/python" ]] || lab_error "Python HarMoCAP no ejecutable: $lab_harmocap_venv/bin/python"
lab_checkpoint="${lab_checkpoint_cli:-${HARMOCAP_CHECKPOINT:-$lab_harmocap/harmocap-m-pose-ft2.pt}}"
if [[ -z "$lab_checkpoint_cli" && -z "${HARMOCAP_CHECKPOINT:-}" && ! -f "$lab_checkpoint" ]]; then lab_checkpoint="$lab_parent/HarMoCAP/harmocap-m-pose-ft2.pt"; fi
[[ -f "$lab_checkpoint" ]] || lab_error "Modelo pose no encontrado: $lab_checkpoint"
export SHAPER_DIR="$lab_shaper" HARMOCAP_DIR="$lab_harmocap" HARMOCAP_VENV="$lab_harmocap_venv"

lab_checkout() {
  local lab_head
  lab_head="$(git -C "$2" rev-parse --short HEAD 2>/dev/null || true)"
  printf '%s: %s [%s]\n' "$1" "$2" "${lab_head:-sin head Git}"
}
lab_checkout 'Weaver' "$lab_root"
lab_checkout 'Shaper' "$lab_shaper"
lab_checkout 'HarMoCAP' "$HARMOCAP_DIR"
printf 'Python Weaver: %s\nPython Shaper: %s\nPython HarMoCAP: %s/bin/python\nModelo pose: %s\n' "$lab_python" "$lab_shaper_python" "$HARMOCAP_VENV" "$lab_checkpoint"
if "$lab_describe"; then exit 0; fi
if "$lab_check"; then
  PYTHONPATH="$lab_root/src" "$lab_python" -c 'import harmonic_weaver.lab, cv2, fastapi, soundfile; print("Weaver: dependencias disponibles")'
  PYTHONPATH="$lab_shaper/src" "$lab_shaper_python" -c 'import harmonic_shaper.audio_engine, harmonic_shaper.capture_recovery; print("Shaper: dependencias disponibles")'
  exit 0
fi

cd -- "$lab_root/laboratory-ui"
if [[ ! -d node_modules ]]; then npm ci --no-audit --no-fund; fi
npm run build
cd -- "$lab_root"
export PYTHONPATH="$lab_root/src"
exec "$lab_python" -m harmonic_weaver.lab \
  --shaper-dir "$lab_shaper" --shaper-python "$lab_shaper_python" \
  --checkpoint "$lab_checkpoint" --data-dir "${WEAVER_LAB_DATA_DIR:-$HOME/.local/share/harmonic-weaver/laboratory}" "${lab_arguments[@]}"
