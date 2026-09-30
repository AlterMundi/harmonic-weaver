# Captura opcional: contrato y estado

2026-09-30. LAB-09 / #17 permanece **en desarrollo**. Base de audio:
[Shaper #4](https://github.com/AlterMundi/harmonic-shaper/pull/4), apilada sobre #3,
sin merge ni aplicación sobre la sesión de prueba. No se habilita grabación al
arrancar, al abrir una cámara ni al elegir un preset.

## Base implementada

Tap independiente después de shape/master/soft limiter, copia exacta del buffer
asignado a PortAudio. El hook antiguo pre-limitador conserva su contrato. Un
writer aparte recibe bloques en un deque acotado; callback no espera por disco
ni por capacidad. Los controles no cambian voces, fases, gain ni afinación.

API Shaper (disponible sólo en la rama compatible):

- `POST /api/audio/capture/start`: `max_seconds` (0.1..3600, default 120),
  `queue_blocks` (4..1024, default 128), `owner` opcional (nonce opaco
  alfanumérico/guión/underscore, 1..80 caracteres); requiere engine activo.
  Reintentar el mismo owner y parámetros devuelve la captura existente incluso
  cerrada; cambiar parámetros con ese owner se rechaza. No es autenticación. Límite RIFF
  validado antes de crear archivos. Inicios concurrentes no crean dos writers.
- `GET /api/audio/capture`: id/estado/error, carpeta, sample-rate, límites,
  muestras aceptadas/escritas, primera/última muestra y cola. No inicia nada.
- `POST /api/audio/capture/stop`: id opcional; id obsoleto devuelve 409.
  El cierre espera al writer fuera del callback y reporta si aún sigue activo.

Archivos locales bajo el root de captura de Shaper, subcarpeta privada por id:
`audio.wav` estéreo float; `blocks.jsonl` con sample index, timestamps de callback
monotónico/DAC, voces pre-shape y cantidad recortada; `manifest.json` atómico
al cerrar. Duración máxima recorta exactamente por muestras. Un early stop
termina el intervalo continuo actual, sin detener el instrumento.

Overflow, discontinuidad de sample-clock, cambio de sample-rate, callback status
y stream interrumpido marcan captura fallida. Disco/cola no detienen síntesis;
un fallo del stream puede detener la salida física y no se presenta como sonido
continuo. No se inventan bloques perdidos ni se comprime silenciosamente el tiempo.
Audio representa salida digital de Shaper, no volumen del dispositivo/mixer ni
otras aplicaciones. Timestamps DAC reportados no son una medición audiovisual.

## Evidencia y límites

33 pruebas hardware-free de captura/offline/laboratorio/audio/pads pasan, incluidas
9 de captura: identidad con outdata y diferencia del tap pre-limitador, muestras/
recorte, early stop, overflow/disco/reloj/stream, concurrencia, API/id y límites.
No se capturó la sesión corporal en marcha. No se afirma latencia física ni escucha.

Hay UI/colector Weaver en la rama `feat/laboratory-session-capture`, basado en
Comparador #41 y dependiente de Shaper #4 actualizado. No se instaló sobre la
sesión habitual. No hay aún video, composición, protocolo de sincronización
ni recuperación del WAV después de matar el proceso. El WAV puede quedar interrumpido en
ese caso; debe declararse como tal hasta implementar recuperación. Por cambiar
AudioEngine, el hash estricto de PCM cambia: requests congelados anteriores
requieren su checkout pinneado o una nueva corrida, nunca quitar el hash en silencio.

## Siguiente integración, sin perder el alcance de #17

1. Controles web explícitos iniciar/detener, duración/presupuesto y diagnóstico.
   Proxy al Shaper seleccionado, id propio y reconocimiento de desconexiones;
   no activar cámara ni un buffer retrospectivo como efecto de grabar audio.
2. Colector acotado fuera del tick: preset inicial, calibración/selección y
   fuente/cache/generación; cambios de configuración/revisiones, marcas,
   transporte/epochs, percepción y versiones. Preset final solo no reproduce una
   sesión cambiada. Indicar estado previo no serializado, no asumir cold start.
3. Video de archivo: timeline explícito de segmentos, loops, seeks, pausas y
   fuentes, sin copiar el original grande. Cámara: captura sólo tras acción
   explícita, timestamps/drop counts y encoder separado; límites y fallos visibles.
4. Alineación/mux con PCM y figura opcional. Distinguir reloj de captura, reloj de
   audio y presentación; registrar offsets/incertidumbre. Verificar con estímulo
   audiovisual, no sólo igual duración. No prometer identidad acústica por tap.
5. Cierre/cancelación/recuperación, manifests y artefactos verificables. Conservar
   raw válido si falla exportación; archivos interrumpidos no se llaman completos.
   Ningún paquete privado se publica automáticamente.

La exploración en tiempo real y los presets siguen funcionando sin grabar. Este
incremento no completa #17, #18 ni R01–R13.

## Colector y controles web implementados

Pestaña Captura: inicio/detención explícitos; duración máxima, cola Shaper y
frecuencia del timeline configurables. API Weaver `GET /api/captures`,
`POST /api/captures/start` (max_seconds/queue_blocks/timeline_hz),
`POST /api/captures/stop`. Requiere la API compatible de Shaper #4; errores se
muestran sin comenzar otra captura ni detener una ajena.

Carpeta local `<data-dir>/captures/<id>/`: manifest con preset/estado/calibraciones
iniciales, cursor SQLite y owner; events.jsonl conserva todas las revisiones
confirmadas posteriores y timeline.jsonl muestrea fuente/transporte/epoch,
features/modelo/audio efectivo. El cierre drena hasta un cursor final confirmado,
espera al writer Shaper y calcula hashes. El WAV permanece en la carpeta Shaper
referenciada. El journal puede comenzar antes del primer bloque de audio y terminar
después del último: sus timestamps no implican pertenencia al intervalo PCM.
Loops automáticos son observados en el timeline; no hay evento exacto por cada loop.
Estado interno caliente del modelo/router no serializado: no promete recomputación
exacta. Al reabrir, manifests sin cierre confirmado se marcan interrupted; no se
reanudan ni se detiene un Shaper sin confirmar su identidad.

Evidencia: 22 pruebas Weaver de colector/runtime/store/API (8 de colector), 33
Shaper y build TypeScript/Vite. Incluye 1205 eventos nuevos sin truncamiento,
ack perdido y owner ajeno, proceso interrumpido y una integración con API/kernel
real de Shaper usando bloques sintéticos: WAV idéntico a los buffers emitidos.
Sin dispositivo físico, datos privados, escucha humana ni prueba browser de esta
pestaña. Identidad de fuentes cambiantes aún no registrada con cada observación del timeline; captura audiovisual, mux/latencia,
recuperación del WAV y verificación visual de controles siguen pendientes.

## Identidad y prueba de navegador

Incremento posterior sobre #42: manifest conserva head/estado del worktree,
hashes Python de Weaver y hashes de archivos de interfaz; Shaper devuelve hashes
de módulos de síntesis/captura y versiones Python/numpy/soundfile. Identidad de
fuente inicial y eventos de cambio de fuente conservan media_id declarado por
biblioteca, cache_key/generación y hash del manifest de tracking cuando está
accesible. No se recalcula el hash del video original; esa procedencia se etiqueta
como declarada. Un manifest inaccesible conserva un error explícito, sin fabricar
hash ni frenar el instrumento. Regeneración automática de cache posterior al inicio
puede aparecer sólo en timeline: no hay todavía inventario completo de cada
transición ni hash garantizado de sus artefactos. Estas identidades permiten
interpretar el registro; no garantizan exactitud de recomputación ni equivalencia
entre módulos cargados y archivos editados después de arrancar el proceso.

Chrome/Playwright, componente aislado y API sintética: no inicia al montar, envía
los tres parámetros, bloqueo durante captura, detener/cierre, rutas locales y
error visible verificados (1 prueba). 23 pruebas Weaver de colector/runtime/store/
API pasan; incluye hash del manifest sin leer original. No hubo grabación privada,
prueba cámara/R24 ni aceptación humana. Servidor aislado detenido al terminar.

## Exportación video de archivo + PCM

Implementación posterior a #42, rama `feat/laboratory-capture-video-export`.
Pestaña Captura permite exportar una captura completa a MKV H.264 + pcm_f32le
(sin recodificación con pérdida del audio). Controles FPS 1..120, ancho/alto pares,
offset -5..5 s y edad máxima de observación. Exportación en thread separado,
una a la vez; cancelación explícita y cierre al salir. No toca el instrumento ni
los originales. Decodifica posiciones necesarias desde sus rutas existentes.
Requiere `ffmpeg` con libx264 en PATH y el extra `[lab]` actualizado que incluye
opencv-python-headless; aquí se probó con dependencia temporal aislada, sin
modificar el venv del workspace original ni el laboratorio de pruebas.

API: GET `/api/capture-exports`; POST `/api/captures/{id}/export` con settings;
POST `/api/capture-exports/cancel`. Carpeta local de sesión `exports/<id>/`:
manifest, frames.jsonl con referencias/causas de hueco, encoder.log y capture.mkv.
El manifest verifica hashes del journal/timeline, cuenta PCM vs bloques y conserva
hashes de entrada/salida. Errores/cancelación conservan raw de captura y manifiesto
failed; un archivo partial no es una exportación completa. Servicio no reanuda una
exportación tras reiniciar; consulta/inventario histórico y descarga/player web de
estos artefactos quedan pendientes (salida local visible por ahora).

Alineación **estimada**: sample index del PCM más timestamp generated_monotonic_s
por bloque de callback; cada fotograma toma la última posición de fuente observada
con edad inferior al umbral. No interpola entre epochs ni inventa progresión entre
observaciones. Pausas sostienen imagen; seeks/loops aparecen al observarse. Posible
error temporal por frecuencia de muestreo, decodificación/seeks, callback y reloj
visual; no se trata de latencia DAC/pantalla medida. Offset positivo consulta una
observación posterior. Intervalos no observados, sin fuente, de cámara o demasiado
viejos van en negro, con conteos explícitos. Duración video redondea hacia arriba
a frames; puede superar PCM en menos de 1/FPS. No shortest silencioso ni audio
estirado. No incluye skeleton/figura ni registra pixels de cámara. Identidad del
original permanece declarada; no se rehashea el archivo grande durante exportación.

Evidencia: 10 pruebas de plan temporal; 6 de exportación real con ffmpeg/OpenCV,
fuente roja sintética y PCM generado: muestras audio extraídas del MKV exactamente
iguales al WAV, fotograma rojo verificado, original sin cambios, huecos negros,
cancelación, hash alterado y servicio/cierre fallido. Chrome/Playwright aislado
verifica controles de captura y envío de parámetros de exportación (1 prueba).
Build TypeScript/Vite pasa. Ninguna grabación corporal privada ni escucha humana.
LAB-09 sigue abierto: cámara, recuperación WAV, sincronía medida, overlays,
player/download, inventario persistente y transiciones de fuente completas.
