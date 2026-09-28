# Consonancia kinética — modo del setup en vivo

Prueba aislada: **HarMoCAP → controlador de consonancia → Shaper**.

**Configuración vigente: movimiento crudo.** Snap 0, ganancia basal 0,
sin suavizado de salida de 200 ms ni filtro One-Euro de coordenadas. En reposo
medido no hay sonido. Sólo suenan las zonas con velocidad observada distinta
de cero; las articulaciones perdidas se silencian en la siguiente muestra.
Attack/release de Shaper se ponen en cero al iniciar este modo.

La velocidad necesita dos muestras y la aceleración tres. La métrica de
predicción sigue usando historia causal del gesto; no espera muestras futuras
ni añade una cola de reproducción. Permanecen captura, inferencia, red local
y bloques de audio. El jitter de la estimación de pose también cuenta como
movimiento en esta prueba sin filtro ni umbral de velocidad.

```bash
./scripts/start-kinetic-consonance.sh --camera 0 --shaper-device "R24 Analog Stereo"
```

Sólo arranca esos tres procesos. No inicia pads/bandas, Stage/patchbay,
beacon-spatial, MIDI ni ECG. Conserva la ventana de cámara y esqueleto;
no graba tracking salvo que se pida con `--record`.

La Logitech C920e corresponde a cámara 0 y la integrada a cámara 2 en la
última enumeración comprobada. `--no-window` permite una prueba sin visor;
`--shaper-no-audio`, una prueba silenciosa. Ctrl-C detiene el experimento.

El lanzador comparte supervisión con `start-live-stack.sh`, pero selecciona
una rama aislada que tampoco carga dependencias del runtime Weaver ni necesita
el checkout del espacializador. Si un puerto está ocupado, falla sin terminar
procesos ajenos. La entrada anterior `--scene kinetic-consonance` también fuerza
este aislamiento, incluso si se agrega `--beacon-mute`.

HarMoCAP conserva captura, identidad y tracking; el controlador usa el puerto
esclavo 9003 de Shaper. El 9001 queda para control de HarMoCAP y el 9100 recibe
tracking. No se modifican las métricas ni la síntesis para esta separación.

## Ventana

La misma ventana HarMoCAP muestra video espejado, esqueleto y selección de
persona. No dibuja pads, bandas ni sus etiquetas de activación. Sobre la
persona que controla el instrumento muestra H1–H6 y, cuando suenan, sus
frecuencias. El pie distingue `Camara N | EN VIVO` de un archivo de video.

- `1`–`8`: elegir persona visible; `0`/`a`: foco automático.
- `f`: pantalla completa; `q`/Escape: cerrar y detener este modo.
- Sólo una persona controla las seis zonas en esta versión.
- Si el stream se interrumpe, el lease de dos segundos libera las voces; cambiar de persona
  o de stream reinicia la historia cinemática para evitar saltos ficticios.
- Al salir se liberan sólo las voces propias; no se envía un panic global.

`--consonance-snap 0` y `--consonance-f1 40.4` son los valores iniciales.
El mapeo anatómico y los pesos conservan los del prototipo; no representan una
calibración experimental nueva.

## Interfaz con HarMoCAP

El checkout hermano necesita las opciones `--pads-mode none` y
`--instrument-state <archivo.json>` en `scripts/run_realtime.py`. Son una
extensión de visualización: el renderizador no calcula métricas musicales.
El driver escribe atómicamente `consonance-state.json` en los artefactos de
la sesión (máximo 10 Hz); el visor descarta estados viejos o de otro stream.
Los modos grid y bands mantienen su comportamiento.

`--pads-view harmocap` es el valor predeterminado para consonancia. `none`
permite pruebas sin ventana. El overlay web de pads no representa este modo;
`web` y `both` se rechazan explícitamente.

## Verificación 2026-09-27

- Weaver: 177 tests y 4 subtests aprobados, incluidos ocho casos nuevos de
  OSC, foco, reinicio de stream, desaparición, lease y apagado selectivo.
- HarMoCAP: 29 tests aprobados de overlay, renderizado y contrato OSC.
- Arranque real acotado, sin cámara/audio: sólo Shaper y consonancia en el
  pidfile; nueve voces con frecuencia variable; silencio tras vencer el lease;
  SIGTERM limpia el estado y el supervisor termina el sintetizador.
  Evidencia local: `rehearsal/artifacts/live-consonance-check-20260927T193614/verification.json`.
- El usuario informó haber escuchado audio en la prueba anterior del
  prototipo. Ese dato no identifica por sí solo si la fuente era cámara o replay.

- Cámara física: prueba acotada sin audio ni grabación con Logitech C920e
  (`--camera 0`). Se observó la ventana HarMoCAP y actualizaciones de las
  nueve zonas desde el stream real; no hubo traceback. Evidencia local en
  `rehearsal/artifacts/live-consonance-camera-check3-20260927/verification.json`.
  La prueba detectó y resolvió la colisión de puertos 9001, separando Shaper
  a 9003 en el lanzador.

## Sustained drone / chord — 2026-09-27

Following the listening test, consonance now sustains polyphonic voices rather
than gating them on movement. Once a zone is observed its voice stays on,
including at rest. Briefly missing joints hold their previous sound; losing
the performer still releases the chord through the existing presence lease.

- Pitch: the existing kinetic deviation and snap, within ±f1/2 per harmonic.
- Gain: a quiet 0.12 baseline plus up to 0.33 from the existing motion gain,
  before Shaper's polyphonic normalization.
- Phase: an exploratory ±45° offset following signed kinetic deviation.
- All three controls approach their targets with a 200 ms time constant.

The gain floor, phase depth and smoothing are initial musical choices, not
experimentally calibrated consonance metrics. The native Shaper gain/phase
controls on UDP 9002 update held voices without note-on/strum retriggers;
frequency and voice lifecycle continue on the slave port 9003. Shaper code
and the isolated setup remain unchanged.

Validation: ten controller regression tests; actual OSC into Shaper and offline
audio rendering prove nine simultaneous sustained voices at rest, audible
nonzero output, phase modulation and release. New live listening remains the
musical evaluation step.

## Mapeo vigente de seis voces — 2026-09-27

Orden indicado por Nicolás: caderas F1, hombros F2, rodillas F3, codos F4,
tobillos F5 y muñecas F6. Reemplaza el mapeo anterior de nueve zonas,
retirando cabeza y puntos virtuales del torso. A f1=40.4 Hz las frecuencias
de reposo son 40.4, 80.8, 121.2, 161.6, 202 y 242.4 Hz.

Esta revisión cambia el mapeo. Conserva el punto medio para caderas/hombros
y la selección del lado más rápido para los pares de extremidades; combinar
métricas calculadas por lado sigue pendiente. Las evidencias de nueve voces
anteriores corresponden a la versión previa. Verificación actual: once tests
del controlador, incluido el mapeo de articulaciones a voces y al overlay.

## Revisión cruda — 2026-09-27

Reemplaza el comportamiento de drone en reposo documentado arriba. Ganancia
por voz = 0.45 × min(1, velocidad / 1.5), con velocidad en torsos/segundo;
no hay piso, rampa de salida ni descenso gradual de volumen. Pitch y fase
reciben directamente el desvío cinético calculado. Se conservan las seis
asignaciones anatómicas. Las extremidades mantienen historia independiente
por lado para evitar movimientos ficticios al cambiar de lado dominante.

Verificación: 13 tests del controlador, 9 de HarMoCAP (pose cruda y suavizado
habitual), más OSC real y render de Shaper: reposo silencioso, sólo F6 ante
movimiento de una muñeca y salida exactamente cero tras la muestra quieta.

## Listening checkpoint

`kinetic-consonance-raw-v1` preserves the six-zone raw instrument that Nicolás
liked in listening, before the next visual feedback / sensitivity changes.
Its HarMoCAP companion is commit `4503393d8bc033bed4e6cdf69dd6745042283afe`,
with the same tag in that repository. Tags are local until explicitly published.
