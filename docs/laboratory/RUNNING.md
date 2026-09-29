# Arranque y primer recorrido local

Estado: primera iteración local disponible; ver IMPLEMENTATION_STATUS. La escucha y
aceptación de Nicolás no se infieren de las pruebas automatizadas.

[Evidencia, mediciones y límites conocidos](VALIDATION.md).

## Dependencias

En Legion, el comando corto prepara la web e inicia la sesión:

```sh
cd /home/nicolas/Projects/harmonic-weaver-lab
./scripts/start-laboratory.sh
```

El modo `auto` prefiere JACK sobre PipeWire si está disponible y selecciona una salida estéreo JACK. En Legion, el camino ALSA `pipewire` puede reportar callbacks activos sin salida útil; se usa JACK. `--audio-backend native` y `--device` permiten elegir otra ruta.

El wrapper acepta `WEAVER_PYTHON`, `SHAPER_DIR`, `SHAPER_PYTHON`, `HARMOCAP_DIR`,
`HARMOCAP_VENV` y `HARMOCAP_CHECKPOINT` para otros checkouts/entornos. Los flags
posteriores se pasan al launcher Python.

Weaver `feat/laboratory-live` (PR #30), HarMoCAP
`feat/laboratory-capture-baseline` (PR #1), Shaper
`feat/laboratory-telemetry` (PR #2). Los tres checkouts están separados de los
workspaces originales preservados. No requiere fusionar las PRs para probar.

Entorno Weaver: dependencias del proyecto y extra `lab`. Entorno HarMoCAP:
dependencias propias + `av>=12,<17` y modelo pose local. Entorno Shaper:
dependencias propias, dispositivo de audio disponible. Frontend: Node 22.

```sh
cd laboratory-ui
npm ci
npm run build
```

Desde el checkout Weaver, un arranque genérico:

```sh
PYTHONPATH=src HARMOCAP_DIR=/ruta/HarMoCAP HARMOCAP_VENV=/ruta/HarMoCAP/.venv \
python -m harmonic_weaver.lab \
  --shaper-dir /ruta/harmonic-shaper \
  --shaper-python /ruta/harmonic-shaper/.venv/bin/python \
  --checkpoint /ruta/modelo-pose.pt
```

En Legion, los checkouts y entornos ya preparados permiten:

```sh
cd /home/nicolas/Projects/harmonic-weaver-lab
PYTHONPATH=src \
HARMOCAP_DIR=/home/nicolas/Projects/HarMoCAP-lab \
HARMOCAP_VENV=/home/nicolas/Projects/HarMoCAP/.venv \
/home/nicolas/Projects/harmonic-weaver/.venv/bin/python -m harmonic_weaver.lab \
  --shaper-dir /home/nicolas/Projects/harmonic-shaper-lab \
  --shaper-python /home/nicolas/Projects/harmonic-shaper/.venv/bin/python \
  --checkpoint /home/nicolas/Projects/HarMoCAP/harmocap-m-pose-ft2.pt \
  --audio-backend jack --device "Built-in Audio Analog Stereo"
```

Abrir **http://127.0.0.1:8765**. Shaper propio usa localhost:8085, sin MIDI ni OSC.
Si un puerto está ocupado, el launcher informa el conflicto; no mata ese proceso.
Usar `--port` / `--shaper-port` para otra sesión, o `--external-shaper` para conectar
explícitamente un motor ya iniciado que tenga la API de laboratorio.
Ctrl+C termina esta sesión y solo su proceso Shaper propio.

`--no-audio` es diagnóstico: no representa un laboratorio sonoro funcionando.
Los presets/bitácora van a `~/.local/share/harmonic-weaver/laboratory` (cambiable
con `--data-dir`). El tracking vive junto al video o en el fallback documentado
en SOURCES. La cámara y el audio live no se graban automáticamente.

## Recorrido breve

1. Fuente: ingresar la ruta de un video y abrirlo; esperar el tracking o explorar
   el prefijo procesado. Reproducir y activar Loop. Reabrir el mismo archivo debe
   mostrar «cache reutilizado»; «Forzar tracking» genera una extracción nueva.
   En esta máquina ya hay cuatro fragmentos en `~/Videos/weaver-lab/` y en la
   biblioteca. No hace falta abrir/procesar el original de 15 GB para empezar.
2. Presets: elegir «Instrumento original» para el baseline de seis voces.
   Cambiar master, sensibilidades y ruteos mientras la fuente sigue corriendo.
3. Para modelos nuevos, elegir la persona y **Calibrar escala con este cuerpo**.
   Aplicar un preset local, relacional, angular o colectivo. Si no hay datos
   suficientes para una señal, se muestra missing; no se fabrica movimiento.
4. Figura: ver la suma de todos los armónicos activos y habilitar componentes.
   Las fases/ganancias vienen de Shaper. Shape y limiter pueden agregar contenido
   al audio que esta figura preprocesamiento no representa.
5. Guardar como nuevo y exportar JSON. Reaplicar al mismo video u otro; la
   calibración y la historia no viajan en el preset. Una marca guarda un comentario
   y contexto de sesión, no un fragmento audiovisual.

La aceptación humana evalúa lo que se siente al moverse/observar/escuchar.
Los tests verifican contratos, continuidad y comportamiento técnico; no esa sensación.
