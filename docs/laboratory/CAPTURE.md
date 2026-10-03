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

Actualización 2026-10-03: recovery in-flight dispone de jobs consultables en el
nuevo Shaper. Weaver guarda shaper_recovery_job_id antes del envío; respuesta
perdida se resuelve consultando ese mismo recibo. GET no relanza. Reload conserva
ID y Recuperar vuelve a consultar explícitamente. Timeout/5xx/transporte ambiguo
quedan unconfirmed, con ID reutilizable; job muerto es interrupted y un nuevo
intento después de fallo terminal requiere acción explícita. Espera acotada a
120s por intento, solicitudes de8s. Shaper viejo conserva camino anterior.
Job recuperado no equivale a captura normalmente completa ni revalida por sí
solo archivos actuales: exportación mantiene sus verificaciones. Las menciones
históricas de polling pendiente abajo quedan superadas por este corte.

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

## Inventario y descarga persistentes

Actualización de #43: al iniciar se descubren manifests bajo captures/<id>/exports;
rendering sin cierre se marca interrupted y conserva diagnóstico. GET
`/api/capture-exports/jobs` lista historial. Descargas explícitas desde la UI:
`/api/capture-exports/{id}/artifacts/{name}` sólo admite capture.mkv, frames.jsonl
y manifest.json. Video/timeline requieren exportación completa y hash válido;
manifest puede descargarse también para diagnosticar fallos. Rechaza symlinks de
carpeta/archivo y nombres fuera del contrato; no recibe una ruta arbitraria.
FileResponse atiende Range/206 sin cargar el video completo en memoria. El hash
se memoiza por path/dev/inode/tamaño/mtime/ctime; un cambio invalida la verificación.
No sube ni publica archivos. No hay player web del MKV todavía.

Evidencia adicional: reinicio recupera salida completa, rendering interrumpido,
rechazo de artefacto modificado/nombre indebido y API HTTP Range/206. 30 pruebas
colector/timeline/export/API; Chrome aislado verifica enlace de descarga y
controles; build TypeScript/Vite. Servidor aislado detenido. No cambió la sesión
habitual, ni hubo grabación privada o aceptación humana. Pendientes LAB-09:
player, cámara, recuperación WAV, medición de sincronía y overlays.

## Recuperación explícita de prefijos PCM

Ramas `feat/laboratory-capture-recovery` de Weaver/Shaper; Shaper #5 sobre #4.
Capturas nuevas tienen capture.json y lock POSIX del writer. Flush periódico de
WAV/journal ocurre fuera del callback; no se afirma resistencia a corte eléctrico.
Shaper POST `/api/audio/capture/recover` recibe sólo id bajo root configurado,
rechaza writer activo/captura complete/capturas legacy sin contrato de lock y
metadata. Lee RIFF float32 estéreo aun con longitudes de header obsoletas y
recupera exclusivamente bloques completos consecutivos confirmados por el journal.
Corta ante fila parcial/discontinua/PCM insuficiente. Nada rellena muestras.

Resultado en `<Shaper-capture>/recovered/<id>/`: WAV, journal y manifest con status
recovered, muestras confirmadas/disponibles/descartadas, motivo del corte, hashes
de originales y resultado. Originals y manifest original no cambian. Es un
prefijo recuperado, no una captura completa; exportador no lo promueve a complete.

Web: botones Recuperar audio en capturas failed/interrupted con id Shaper conocido.
Weaver POST `/api/captures/{id}/recover` y GET `/api/capture-recovery`; worker HTTP
separado con timeout 120 s. Preserva manifest Weaver, registra recovery.json aparte
y lo recupera al reiniciar. Carpeta/muestras visibles; descarga/player de prefijos
recuperados y recuperación del journal Weaver interrumpido siguen pendientes.
No hay recuperación automática ni grabación implícita. Fallos/timeouts visibles;
un timeout no demuestra que Shaper no haya creado un resultado (inventario del
lado Shaper y resolución de acknowledgements de recuperación pendientes).

Evidencia: 38 tests Shaper incluidas 5 de recuperación (process kill sintético real,
PCM exacto, hashes raw preservados, writer activo, prefijo vacío, API/id vs ruta).
31 tests Weaver de colector/plan/export/API; prueba adicional comprueba recovery.json
persistente y manifest original intacto por hash. Chrome aislado de botones/envío/
resultado y build pasan. No prueba cámara/R24 ni datos privados o aceptación humana.
Pendientes LAB-09: cámara, player, overlays, sincronía medida; recuperación legacy,
power-loss, journal de sesión y resolución de ack perdido no se dan por hechas.

## Captura opcional de previews de cámara

Rama `feat/laboratory-capture-camera`, sobre #44. CaptureSettings ahora expone
record_camera=false (opt-in explícito), camera_queue_frames=8, camera_max_frames=10000
y camera_max_mb=256. UI muestra controles y contador de previews/saltos/error. No
enciende cámara ni añade captura retrospectiva. Guarda solamente nuevas previews
JPEG ya producidas por tracking (máximo 960 px en worker actual), no el flujo bruto
de adquisición ni resolución/FPS completos. Frecuencia efectiva depende de tracking,
timeline_hz y disco. max_mb limita bytes JPEG; journal/timeline/metadata son adicionales.

Lectura atómica del paquete preview/stream/sequence/timestamps bajo lock breve;
decodificación base64 y escritura fuera del tick/audio. Writer separado con deque
acotado, sin esperar por espacio: overflow/budget/disco fallan la captura y cierran
su registro audio, manteniendo el instrumento/fuente operando. No se rellenan imágenes
faltantes. Cada JPEG/hash queda en camera/, con frames.jsonl y manifest propios;
timeline enlaza paquetes nuevos. Sequence gaps incluyen adquisición, pose y muestreo
del recolector: no se atribuyen a sensor ni calidad sin evidencia. Stream nuevo admite
reinicio de secuencia; un retroceso dentro del mismo stream se rechaza.

Exportación reconoce cámara grabada y valida hash de índice y JPEG; respeta stream
seleccionado en el timeline. Reloj configurable camera_clock: collector_monotonic_s
(default, observación del recolector), available_monotonic_s (post-tracking) o
captured_monotonic_s (captura software). Conserva los tres; no confunde sus retrasos
con latencia audiovisual medida. Usa último JPEG con reloj <= tiempo alineado y edad
máxima configurada. Huecos/cámara no grabada/stale en negro; archivos siguen en su
ruta sin copia. Reloj de captura sirve para explorar la correspondencia temporal del
movimiento; no garantiza reproducción del feedback que el operador vio en vivo.

Evidencia: 45 tests cámara/plan/export/colector/runtime/API/decoder; cuatro del writer
cubren clocks/hash/duplicados, stream/gaps, budget, overflow con disco bloqueado y
fallo de disco. Colector comprueba ausencia de píxeles sin opt-in. Export real sintético
con JPEG azul y PCM: imagen verificada y audio MKV idéntico por muestras; JPEG alterado
se rechaza. Prueba Chrome aislada verifica opt-in inicialmente apagado, envío de
límites y elección de reloj; build TypeScript/Vite pasa. Sin abrir cámara física ni
capturar datos privados o cambiar workspace de pruebas. Servidor aislado detenido.

Pendientes LAB-09: prueba cámara real/aceptación humana, protocolo de sincronía física,
player/overlays, recuperación de imágenes/journal tras kill, resolución de ack recovery.
Captura de flujo bruto de cámara o mayor resolución/FPS es una entrega adicional,
no una capacidad de esta preview. #17 sigue abierto.

## Prefijos recuperados del journal de sesión

Incremento sobre #45: después de confirmar id/PCM recuperado, conserva filas
completas válidas de events.jsonl y timeline.jsonl en journal-recovered/<id>/.
Checks: JSON finito/forma mínima, secuencias consecutivas de eventos y reloj
monotónico de observaciones. Corta ante JSON/UTF-8 truncado, fila incompleta o
invalidez, con motivo/contador. Lee líneas binarias y decodifica individualmente
para preservar prefijos anteriores a un final UTF-8 roto. Guarda hashes raw/output
sin modificar originales. Estado partial, no reconstrucción exacta ni garantía de
cobertura temporal/cursor final. No agrega eventos futuros de SQLite ni inventa
observaciones. Cámara/JPEG no se recuperan en este incremento.

PCM confirmado se registra antes de intentar salvar bitácora; si ésta falla,
resultado de audio sigue visible/persistido y journal failed separado. UI muestra
contadores/ruta parcial o error. Si falla guardar metadata, no se declara que la
recuperación del lado Shaper no ocurrió. Resolución de ack pendiente permanece.

Evidencia: 52 tests colector/journal/cámara/plan/export/runtime/API/decoder; seis
pruebas de prefijo incluyen final UTF-8 roto, filas/JSON/NaN/secuencias/reloj
inválidos y raw hashes preservados. Fallo del journal no oculta PCM confirmado.
Chrome aislado verifica presentación de contadores y build web pasa. Datos
sintéticos; ninguna aceptación humana o grabación física. #17 sigue abierto.

## Reintento compatible de recuperación

Shaper anuncia GET `/api/audio/capture/recovery-contract` schema_version=1,
idempotent_source_hashes=true. Para los mismos hashes de raw WAV/journal/metadata,
recovery devuelve el resultado existente sólo tras verificar WAV/journal recuperados,
con reused=true y ruta anclada al inventario local. Artefacto alterado se rechaza;
no crea otra copia silenciosa. Cambio de raw produce nueva recuperación y hashes
explícitos. Lock sigue excluyendo writers/recuperaciones concurrentes.

Weaver consulta ese contrato antes de intentar recovery. Ante TransportError del
POST reintenta una vez el mismo id sólo con compatibilidad declarada. Errores HTTP
normales no se interpretan como ack perdido; servidor legacy admite un intento,
sin reintento automático. Si perdió confirmación y no confirma después, status
unconfirmed; no declara que Shaper falló ni que no exista resultado. Un recovery aún
en curso puede rechazar segundo intento por lock; polling/inventario de jobs en
Shaper sigue pendiente. No se da ese caso por resuelto.

Evidencia: 39 tests Shaper; incluye mismo resultado/ruta, una única carpeta y
rechazo de resultado alterado. 53 tests pertinentes Weaver antes del último guard
unconfirmed; 14 colector reejecutadas tras guard, incluidos ack perdido resuelto
contra contrato compatible y legacy con un único POST/unconfirmed. No hubo UI,
parámetros sonoros ni cambios del workspace de pruebas. Sin medios/hardware/escucha.

### Cierre del writer de previews — 2026-09-30

Aceptación de paquetes y señal de cierre comparten un lock breve, sin operaciones
de disco ni join dentro del lock. Al cerrar, todo paquete previamente aceptado
se drena; paquetes posteriores se rechazan explícitamente, incluso mientras el
writer termina un JPEG lento. Evita devolver referencias a frames que nunca se
escribirían. Cerrar nuevamente conserva el hash del índice. No cambia la captura
opt-in, los budgets ni el instrumento.

### Recuperación de previews tras interrupción — 2026-09-30

Los nuevos writers mantienen un lock POSIX durante su vida. La recuperación
verifica un prefijo consecutivo de frames.jsonl: fila completa, referencia local
cerrada, SHA-256 de cada imagen, clocks finitos y orden de colección/secuencia.
Se detiene en la primera fila/imagen inválida; no salta huecos, inventa frames ni
ordena retrospectivamente. Rechaza writer activo, captura complete y captures
legacy sin lock/metadata. Genera camera-recovered/<id>/ con índice/manifest
recovered; originales e imágenes quedan intactos y sin copiar.

El índice apunta a frame_root original: quien lo consuma debe volver a verificar
los hashes. No es una copia autosuficiente ni una exportación audiovisual completa.
El recorrido web de recuperación PCM intenta también este prefijo y muestra su
conteo/corte/carpeta; un fallo de imágenes no descarta el audio recuperado.
Quedan pendientes reproducción/exportación del prefijo, sincronía física y cámara
real. La evidencia incluye kill real de un proceso con imágenes sintéticas, no
una captura corporal ni una garantía frente a pérdida de energía del disco.

### Preview reproducible por navegador — 2026-09-30

Exportación ofrece **Generar preview MP4 para navegador**, apagado por defecto.
El MKV mantiene H.264/PCM float exacto. La preview copia el stream H.264 y deriva
AAC del audio confirmado, con bitrate web configurable 64–320 kbps (192 inicial).
No sustituye al PCM: AAC implica compresión/padding posibles. Manifest distingue
ambos archivos, hash/estado/bitrate y límites. Si falla sólo la preview, conserva
la exportación primaria y muestra el fallo; cancelar sigue interrumpiendo el job.

Preview terminada: **Ver preview de captura** abre video con controles sin
reproducir automáticamente; **Cerrar preview** lo desmonta. Descarga MP4 local
por contrato de nombres/hash, reutilizable después de reiniciar el inventario.
No abre cámaras, no captura fuentes nuevas y no modifica el sonido en vivo.
Todavía sin overlays de esqueleto/figura, exportación de prefijos recovered ni
validación de sincronía física. Reproducir PCM con la figura sigue en Comparar;
esta preview AAC no es una validación sample-for-sample de esa figura.


## 2026-09-30 — estado durable de recuperación

El recolector persiste inicio, PCM confirmado antes de recuperar bitácora y
resultado terminal, incluida confirmación perdida. El listado expone estos
estados durante la operación y después de reiniciar; la web muestra el error de
cada captura. Un estado en curso al reiniciar se marca interrupted, conserva PCM
confirmado y no relanza trabajo automáticamente. Fallos de persistencia terminal
se exponen en memoria como persistence_error; no se promete durabilidad si falla
el disco. 16 pruebas de captura pasan, incluidas respuesta perdida y restauración
del PCM parcial. No sustituye el job polling pendiente en Shaper ni permite
exportar prefijos como capturas completas.


### Fallo de disco al persistir recuperación

Prueba adicional con OSError después de confirmar PCM: el snapshot global y el
listado de capturas conservan el mismo resultado y persistence_error. La web
muestra explícitamente que el estado no pudo guardarse; no queda sólo una
recuperación histórica en curso. El archivo anterior puede seguir en recovering
y será interrupted al reiniciar, sin afirmar persistencia del resultado perdido.
17 pruebas de captura, panel Chrome y build pasan. No se abrió audio físico.


## 2026-09-30 — exportación explícita de prefijo recuperado

El botón Exportar prefijo recuperado solicita recovered_prefix=true (default
false). Verifica hashes de WAV/bloques/journal recuperados, identidad Shaper,
conteo PCM y continuidad del sample-clock. Renderiza el video de archivo desde
observaciones recuperadas; observaciones ausentes y cámara aparecen negras.
Conserva capture_completeness=recovered_partial en el manifest: export completo
no significa captura completa. No modifica ni copia originales. La opción MP4
existente permite preview web del derivado; PCM exacto se conserva en MKV.
19 pruebas de export/input pasan, incluido FFmpeg real y comparación exacta de
PCM sintético; Chrome CapturePanel y build pasan. Sin datos corporales publicados
ni hardware. Pendientes: incorporar imágenes de cámara recuperadas, validar
preview integrada de prefijos y sincronía física; job polling Shaper sigue aparte.


La exportación de prefijos también admite recovery.camera.status=recovered:
usa índice recuperado verificado y frame_root original, con hash JPEG comprobado
en cada consumo. Sin prefijo de cámara disponible, conserva intervalos negros.
Esta actualización sustituye la limitación anterior de cámara no incluida.


### Procedencia del export recuperado

recovery_provenance registra identidad/carpeta PCM, carpeta y cortes del journal,
y carpeta/frame_root/índice/corte del prefijo de cámara consumido. input_hashes e
índice de cámara corresponden a los artefactos comprobados para exportar. Los
source_hashes_declared se conservan como declaraciones de recuperación; no se
afirma revalidación del raw original. Todo permanece local, no portable ni apto
para publicación automática sin revisar rutas/datos privados.

### Overlay opcional de esqueleto — 2026-10-03

En Exportar video + audio, **Incluir esqueleto observado en la exportación**
arranca apagado. Elegí persona seleccionada en cada observación o todas; confianza
mínima (0), grosor (2 px) y desfase máximo pose/video (0.1 s) son configurables.
Funciona para capturas completas y prefijos recuperados, MKV y preview MP4.
No modifica el PCM ni activa fuentes o tracking. No cambia defaults del instrumento.

Usa el MotionFrame guardado en el timeline: joints observados, coordenadas
camera_isotropic/frame_height y letterbox del video. Descarta held/missing,
puntos fuera de imagen y confianza inferior al umbral. No proyecta coordenadas
world. Requiere época observada confirmada; archivo debe coincidir en identidad
y stream y estar dentro de la tolerancia temporal. Cámara exige el mismo stream
y sequence del JPEG grabado y geometría compatible. Una observación posterior de
pose no se aplica a un JPEG anterior: la omisión es explícita, sin interpolación.

frames.jsonl registra observation_index y resultado del overlay por fotograma;
el manifest resume frames dibujados y causas de omisión. Capturas históricas sin
pose siguen exportándose, con pose_not_recorded si se solicita overlay. El desfase
es una tolerancia de selección, no una medida de sincronía física.

La preview de prefijos ya tiene integración API/export/reinicio/rangos; las
menciones históricas a ese pendiente arriba están superadas. Pendientes: figura
armónica exportada desde estado efectivo de síntesis, medición física y feedback
humano de cámara. No se declara que el esqueleto esté sincronizado acústicamente.

### Figura de osciladores efectivos en exportación — 2026-10-03

**Incluir figura de todos los osciladores grabados**, apagado por defecto,
añade un panel a la derecha del video dentro del tamaño de salida elegido.
Conserva el letterbox a la izquierda y es compatible con el esqueleto, las
capturas completas, los prefijos recuperados y la preview MP4. No cambia el audio.

Usa voices del blocks.jsonl que acompaña al PCM; ninguna voz se reconstruye desde
targets ni se limita a dos señales o al número de componentes del análisis.
La muestra de salida selecciona el bloque y desplaza sus fases con frecuencia
y reloj de muestras, incluyendo gain_end/phase_offset_delta_rad cuando existen.
La rampa conserva la longitud original del callback aunque el final de captura
lo trunque. Silencio confirmado y telemetría ausente se distinguen: la ausencia
o invalidez limpia el panel y deja una causa en frames.jsonl/manifest.

**Frecuencia de referencia de la ventana** (40.4 Hz) determina la duración de
la curva, no la frecuencia de las voces. **Estilo de figura exportada (JSON)**
acepta VisualSettings; {} utiliza defaults. Por ejemplo
`{"color":"gold","components":true,"persistence":0.3,"window_periods":3.0}`.
Permite samples, line_width, brightness, scale y auto_scale además de los campos
del ejemplo. Se congela en settings del manifest para recuperar la configuración.

Reutiliza RasterFigure/voices_at del comparador: suma fasorial de todos los
osciladores antes de waveshaping/limiter, no reproducción de la forma de onda
post-limiter ni simulación de membrana. offset_s afecta sólo la selección de
video/pose; la figura permanece ligada al PCM. Persistencia depende de FPS de
exportación y no pretende reproducir cada refresco WebGL de una sesión anterior.
Siguen pendientes medición física de sincronía, feedback humano e instalación
de estas PRs; el software no valida por sí mismo HIT ni cymatics físico.

### Configuraciones portables de captura/exportación — 2026-10-03

El panel ofrece configuraciones con nombre: **Guardar configuración de captura**,
selector y **Cargar configuración de captura**. Se conservan en SQLite junto a
los presets del laboratorio, en un namespace separado; no reemplazan el preset
sonoro. Cargar sólo cambia borradores de controles; no inicia captura, cámara,
exportación ni audio. Importar/cargar controles se deshabilita durante una
captura o exportación activa.

**Preparar JSON de captura**, **Descargar configuración de captura** y
**Aplicar JSON de captura** permiten transportar la misma configuración a otra
fuente/biblioteca. El objeto schema_version=1 contiene id, name, capture y export,
incluidos parámetros de cámara, offsets, calidad, esqueleto y VisualSettings de
figura. No admite fuentes, personas, calibración ni rutas de archivos.
recovered_prefix se decide con el botón de cada captura; no es un modo portable.
Importar valida todo antes de cambiar controles; guardar valida antes de escribir.
Los valores anteriores quedan intactos ante un error. Una importación válida no
reemplaza lo guardado hasta pulsar Guardar.

API: GET/POST /api/capture-profiles; GET /api/capture-profiles/{id} descarga JSON;
POST /api/capture-profiles/validate normaliza sin persistir ni ejecutar acciones.
Guardar reutiliza id para actualizar esa configuración; Nueva configuración
permite crear otra con los controles actuales. Defaults son los ya existentes;
record_camera, skeleton_overlay, harmonic_figure y browser_preview siguen apagados.
## Consultas de estado fallidas (2026-10-03)

El panel distingue inventario todavía no confirmado del estado idle. Los fallos
al consultar capturas, exportaciones o recuperación aparecen como alertas, con
el último estado confirmado conservado y reintento automático. Cada grupo mantiene
una consulta en vuelo; si una exportación falla mientras su inventario demora,
el fallo se muestra de inmediato y no se acumulan consultas al inventario.

Un inventario de capturas desconocido/fallido deshabilita nuevos inicios; un estado
de exportación o recuperación desconocido/fallido bloquea nuevos pedidos respectivos.
Detener/cancelar una operación conocida sigue disponible. Recuperar la consulta
quita la alerta y reconcilia los botones; no inicia ni repite operaciones por sí solo.
Esto no modifica buffers, PCM, codecs, snapshots ni defaults de grabación.

Chrome contra bundle de producción/API real, con 503 y demoras introducidos
explícitamente en las consultas de prueba: inventario inicial pendiente, tres
alertas, estado anterior conservado, una consulta por grupo, recuperación y cero
POST/errores JS. No se grabó audio/cámara ni se usaron medios corporales.
