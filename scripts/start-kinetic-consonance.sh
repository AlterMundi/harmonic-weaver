#!/usr/bin/env bash
# Isolated experiment: camera/tracking -> kinetic consonance -> Shaper.
set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
args=()
while [ "$#" -gt 0 ]; do
    case "$1" in
        --camera|--shaper-device|--harmocap-device|--harmocap-checkpoint|--harmocap-imgsz|--harmocap-max-slots|--max-runtime-s|--run-id|--record|--stop|--consonance-snap|--consonance-f1)
            args+=("$1" "${2:?$1 requires a value}"); shift 2 ;;
        --no-record|--shaper-no-audio|--no-harmocap)
            args+=("$1"); shift ;;
        --no-window)
            args+=(--pads-view none); shift ;;
        -h|--help)
            cat <<'HELP'
Consonancia kinética — prueba aislada

  scripts/start-kinetic-consonance.sh [opciones]

Sólo HarMoCAP (video + esqueleto), controlador de consonancia y Shaper.
Sin pads, bandas, patchbay, espacializador, MIDI ni ECG.

  --camera N                  Cámara (default: 0)
  --shaper-device NOMBRE       Audio (default: R24 Analog Stereo)
  --consonance-snap 0..1       Snap (default: 0)
  --consonance-f1 HZ           Fundamental (default: 40.4)
  --harmocap-device auto|cpu|cuda
  --no-window                 Sin ventana
  --shaper-no-audio            Prueba silenciosa
  --record ARCHIVO            Grabar tracking (default: no grabar)
  --max-runtime-s SEGUNDOS     Duración máxima (default: 14400)
  --stop ID                   Detener una sesión por su identificador
HELP
            exit 0 ;;
        *) echo "Unsupported option for isolated consonance: $1" >&2; exit 2 ;;
    esac
done
exec "$SCRIPT_DIR/start-live-stack.sh" --scene kinetic-consonance --no-record "${args[@]}"
