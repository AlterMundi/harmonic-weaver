#!/usr/bin/env bash
# Isolated experiment: camera/tracking -> kinetic consonance -> Shaper.
set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
args=(--pads-view none --harmocap-device cuda --harmocap-imgsz 320)
while [ "$#" -gt 0 ]; do
    case "$1" in
        --camera|--shaper-device|--harmocap-device|--harmocap-checkpoint|--harmocap-imgsz|--harmocap-max-slots|--max-runtime-s|--run-id|--record|--stop|--consonance-snap|--consonance-f1|--consonance-ui-port|--consonance-settings)
            args+=("$1" "${2:?$1 requires a value}"); shift 2 ;;
        --no-record|--shaper-no-audio|--no-harmocap)
            args+=("$1"); shift ;;
        --window)
            args+=(--pads-view harmocap); shift ;;
        --no-window)
            args+=(--pads-view none); shift ;;
        -h|--help)
            cat <<'HELP'
Consonancia kinética — prueba aislada

  scripts/start-kinetic-consonance.sh [opciones]

Sólo HarMoCAP (GPU, sin ventana), controlador de consonancia y Shaper.
Esqueleto y controles: http://localhost:8766
Sin pads, bandas, patchbay, espacializador, MIDI ni ECG.

  --camera N                  Cámara (default: 0)
  --shaper-device NOMBRE       Audio (default: R24 Analog Stereo)
  --consonance-snap 0..1       Snap (default: 0)
  --consonance-ui-port PORT    UI local (default: 8766)
  --consonance-settings PATH   Archivo de parámetros persistentes
  --consonance-f1 HZ           Fundamental (default: 40.4)
  --harmocap-imgsz N           Resolución de inferencia (default: 320)
  --harmocap-device auto|cpu|cuda
  --window                    Abrir también el video HarMoCAP
  --no-window                 Sólo UI web (default)
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
