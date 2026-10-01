# Evidencia de la primera iteración local

2026-09-29, Legion. Esto verifica software e integración; **no registra una escucha
ni aceptación humana** y no es una evaluación formal de HIT o eficacia corporal.

## Pruebas

- Weaver: suite general **229 tests + 4 subtests**, 117,68 s. Después de añadir
  identidad de control en telemetría: **45 tests del laboratorio**, 5,10 s.
- Shaper: **35 tests** de laboratorio, audio y estado, 8,72 s. Incluyen
  reconstrucción desde telemetría con 1/6/32 voces, continuidad, lease y silencio.
- Web: build TypeScript/Vite y **6 pruebas Playwright**. La prueba real comprueba
  avance de video, edición sin detenerlo, revisión efectivamente consumida por
  audio, arrastre de macro y píxeles dibujados en WebGL. Incluye el caso en que
  los esquemas llegan después del primer estado de sesión.

La cámara física produjo captura/inferencia con frames recientes, sin error del
worker en el smoke; después se cerró. No se grabó cámara ni micrófono.

## Fuente real y cache

Se extrajeron cuatro fragmentos locales de 12 s: perfil, espalda, frente y movimiento
sin soga. H.264, 540×960, rotación incorporada, sin audio original. Suman ~21 MB;
el original grande no fue copiado. Los medios y tracking no forman parte del repo.

| Fragmento | Frames | Frames con cuerpo observado |
|---|---:|---:|
| Perfil | 360 | 359 |
| Espalda | 360 | 360 |
| Frente | 359 | 359 |
| Sin soga | 359 | 359 |

«Cuerpo observado» significa al menos un joint observado en alguna persona; **no**
equivale a todos los joints correctos ni a exactitud de pose validada manualmente.
La primera reapertura frontal reutilizó el cache (2,08 s, incluido probe/hash).
Los cinco modelos alcanzaron seis voces efectivas sobre el frontal, sin errores de
runtime. Colectivo y propagación llegaron a estado observado.

### Error GPU encontrado y recuperación

Seguimiento: [issue #31](https://github.com/AlterMundi/harmonic-weaver/issues/31).

Una extracción forzada de espalda con `device=auto` falló en frame 166 por
`CUDA error: an illegal memory access was encountered`. No se determinó la causa
de bajo nivel; no se atribuye sin evidencia al video, modelo o driver.
La generación anterior de 360 frames quedó intacta y se reabrió con cache hit.
Reprocesar con `device=cpu` explícito produjo una generación completa de 360 frames.
Esa configuración tiene su propia clave de cache; no se mezclaron silenciosamente
resultados CPU/GPU. Si se repite el error, seleccionar **cpu** en percepción y
reprocesar. Un worker fallido no publica el prefijo parcial como cache completo.
Un segundo forzado CPU reemplazó su generación anterior; reabrir produjo cache hit.
El mismo preset portable se aplicó en los cuatro fragmentos con nueva calibración
explícita en cada fuente, seis voces activas y silencio comprobado después de pausar.

## Salida de audio

JACK sobre PipeWire, salida estéreo integrada, 48 kHz, bloques de 256 frames.
Se conectaron explícitamente los dos puertos de Shaper a un capturador de prueba
sin conexión a micrófono. La ruta normal hacia la salida integrada quedó conectada.

- RMS previo: 0.
- RMS durante movimiento: 0,03606; pico: 0,11401 (escala completa = 1).
- RMS posterior a pausa/liberación: 0.

Esto prueba señal en los puertos de salida y ausencia de voces colgadas al pausar.
No sustituye escuchar los altavoces. El launcher prefiere JACK porque el camino
ALSA `pipewire` tiene antecedentes de callbacks activos sin salida útil en este host.

## Prueba prolongada

600,10 s de video cacheado en loop, modelo colectivo, con cambios web durante la
prueba: 2234 observaciones de estado, 51 epochs de transporte, seis voces máximas,
**cero errores** de runtime/cliente de audio observados.

| Medida de software (ms) | p50 | p95 | p99 | máximo |
|---|---:|---:|---:|---:|
| Costo de tick de análisis | 9,45 | 37,19 | 50,74 | 117,83 |
| HTTP de control, ida/vuelta | 1,38 | 9,77 | 21,99 | 49,32 |
| Control preparado → primer bloque que lo consume | 14,45 | 27,92 | 33,25 | 84,68 |
| Edad de telemetría al consultar Weaver | 31,97 | 56,08 | 67,49 | 95,31 |

Control→bloque empieza al entregar targets al cliente Shaper; excluye preparación
del modelo y gesto/cola del navegador. La identidad de control se toma atómicamente
con los parámetros del bloque, no se deduce de un ACK HTTP. Edad de telemetría no
incluye pintura del navegador ni latencia del DAC/altavoz. No se midió latencia física
captura→sonido ni audio→luz con instrumentación. Los máximos muestran picos que
conviene seguir investigando; no se afirma cumplimiento físico de las metas.

## Límites para el primer feedback

- Tracking de cámara es 2D; el subespacio colectivo puede tener muchas dimensiones
  latentes, pero no convierte las observaciones en pose física 3D.
- Cache de archivo se carga en memoria. Para fuentes extensas conviene usar
  fragmentos durante esta iteración; no se ensayó cargar el tracking de 98 minutos.
- Evaluadores/centros son proxies cinemáticos. El score retardado es evidencia de
  mejora predictiva respecto del baseline elegido, no causalidad.
- Figura usa osciladores efectivos antes de shape/limiter; no modela una placa
  cimática física ni todos los parciales generados por procesamiento no lineal.
- Escucha, comodidad al moverse y aceptación humana siguen pendientes.

Grabación opcional, comparación formal y sensores conservan sus issues y agenda.

### Reactividad: primera escucha humana (2026-09-29)

Nicolás reportó que la primera versión responde mucho menos que el instrumento
anterior. La aceptación sonora sigue pendiente. En el fragmento frontal local,
reproduciendo el tracking guardado con el controlador preservado, el preset
baseline con plucks produjo ganancias medias por zona
[0.0062, 0.0055, 0.0131, 0.0089, 0.0157, 0.0427]; con plucks desactivados,
[0.3044, 0.2478, 0.2029, 0.4350, 0.1330, 0.4395].
Son ganancias del controlador, antes de normalización polifónica y salida física,
no una medición de volumen percibido. Las velocidades medias fueron idénticas.
Caderas, hombros y codos dispararon un solo impulso en el fragmento: la histéresis
del pluck requiere bajar del umbral de rearme, y movimiento continuo no garantiza
nuevos ataques. Esto explica una respuesta escasa en este caso, sin demostrar aún
qué configuración exacta se usó en la comparación histórica.

Se incorpora «01b · Instrumento original / movimiento continuo», con el mismo
controlador baseline y plucks desactivados. El preset original se conserva.
Próxima comparación humana: mismo fragmento, misma salida y nivel, alternar 01/01b.
Si se desea mantener articulación percutiva durante flujo continuo, estudiar
disparos por cambios de aceleración o mezcla continuo/impulso; no introducir un
reloj de retrigger que invente eventos corporales.

### Clics durante activación y cambios de movimiento

La escucha humana detectó clics repetidos con respuesta continua. Shaper aplicaba
ganancia y offset de fase como escalones entre bloques y omitía el último bloque
de algunas colas. Para voces del laboratorio se interpolan ganancia efectiva
(incluida normalización polifónica) y offset de fase por el arco corto, muestra
a muestra durante un bloque. La cola final se renderiza antes de retirar la voz.
A 48 kHz/256 muestras la transición dura 5.33 ms. El silencio explícito con
release=0 conserva su semántica inmediata.

VoiceFrame informa gain/phase_rad al inicio del bloque y gain_end/
phase_offset_delta_rad para reconstruir la transición; la figura sigue usando
el estado efectivo inicial, no el objetivo sin renderizar.
Pruebas: reconstrucción PCM de 1/6/32 voces y continuidad en activación a fase
de pico, cambios grandes de ganancia/fase y liberación. Falta confirmar por
escucha con la R24 si esto resuelve todos los clics percibidos.

### Sostenido frente a modulación rápida

Tras la corrección de clics, Nicolás reportó una textura semejante a ataques
repetidos. En 150 lecturas de estado durante unos cinco segundos del video
frontal con 01b, las seis ganancias permanecieron positivas (cero transiciones
on/off). En todas las zonas el detune recorrió -1..1 y el percentil 95 del
incremento absoluto de fase fue 90 grados. No se observó retrigger en esa muestra:
la modulación extrema de tono/fase es una hipótesis concreta para esa textura,
pendiente de comparación auditiva.

01c «Armónicos sostenidos / intensidad corporal» mantiene la serie armónica y
fases sin modulación; sólo aplica intensidad corporal, con suavizado de rutas
de ganancia de 30 ms, editable. 01 y 01b se conservan. No se ha corregido ni
validado aún la estimación ruidosa/saturada del residual del controlador original.
Prueba de Shaper: 60 actualizaciones de ganancia positiva conservan el mismo
estado de oscilador, fase acumulada y envolvente abierta.

### Feedback: sostenido aceptado y realce expresivo

Nicolás confirma que 01c se siente bien y activado por movimiento. Esto valida
esa experiencia puntual; no implica aceptación de los demás modelos.
Se agrega expression en [-1,1], default 0, portable en presets. Tras el suavizado
de rutas, la ganancia positiva x se transforma en min(1,x)^exp(-2.5*expression);
cero queda cero, y neutral conserva exactamente la ruta previa. Después se
aplican ganancia de voz y master. No altera pitch, fase, pan ni shape.
Pruebas de extremos/neutral/silencio y afinación: pasan.
Con el tracking frontal y escala medida, los cuatro modelos no baseline
generaron señales observadas y activaron las seis voces en replay offline.
La escucha humana de esos modelos sigue pendiente. Seguimiento: issue #32.


### Corrección del realce tras escucha

Nicolás rechaza el realce positivo inicial por compresión/empaste y prefiere
el contraste del lado negativo. Se reemplaza sólo la rama positiva por
x + 4*expression*(x-media_causal), acotada a [0,1], conservando cero exacto.
La media exponencial tiene constante configurable expression_window_s=0.12.
Entrada constante converge a su nivel original; subidas reciben acento y
bajadas se atenúan. Primer dato tras reset inicializa la media sin ataque
inventado. La rama negativa y el punto neutral se conservan. Esto usa cambios
de intensidad, no una medición explícita de aceleración corporal.
Pruebas: acento de subida, caída, convergencia al sostenido, silencio, reset
y preservación de afinación. Aceptación auditiva de esta curva pendiente.
Preferencia de Nicolás: priorizar ajustes de controles existentes y explicar
qué se cambió antes de introducir mecanismos nuevos.

### Realce ×10 y mezcla de transientes

Nicolás confirma mejora del contraste temporal y solicita mayor exageración.
expression pasa de máximo 1 a 10, conservando la respuesta de presets existentes.
transient_mix=0 conserva el sostenido; hasta 1 mezcla un seguidor de picos de
4*max(0,x-media), con caída exponencial configurable (0.15 s). La primera
observación no genera un impulso. Se descartan residuos menores de 1e-6 para
evitar colas infinitesimales. Frecuencia/fase permanecen sin modificar.
Pruebas cubren factor ×10 antes del límite, decaimiento en sostenido, reset y
ausencia de ataques ficticios al inicializar. Escucha de estos controles pendiente.

## Segunda iteración — 2026-09-29

Trabajo aislado en `harmonic-weaver-lab`, rama `feat/laboratory-v2`, partiendo de
6bdb47a (PR #30). Shaper 8d6de86 y HarMoCAP 27b8fc2 sin cambios de implementación
en esta entrega. Los workspaces originales conservan sus cambios.

- Suite Weaver completa final: **243 tests y 4 subtests pasaron** (122.73 s),
  incluidos preservación de referencias, métricas por estado y cancelación.
  Los seis tests dirigidos del comparador también pasaron por separado.
- Matriz sintética 2 presets × 2 fuentes: repetición con hashes iguales;
  paridad de targets con runtime live bajo tiempos idénticos; prefijo causal,
  escala obligatoria, detección de medio/cache cambiado; persistencia, repetición
  congelada tras editar un preset y cancelación de subproceso.
- Preservación de configuración guardada editada y seis voces afinadas en las
  referencias nuevas; historia de expresión conservada en ediciones compatibles.
- Shaper: **14 tests** de laboratorio/audio smoke pasaron (5.5 s). No se cambió
  el motor; estas pruebas cubren continuidad técnica, no ausencia perceptual
  universal de clicks en hardware ni aceptación musical.
- UI: TypeScript/build Vite correcto. Recorrido con navegador real: abrir
  Comparar, seleccionar dos referencias, agregar segundo segmento de la misma
  fuente, editar tiempos, lanzar, ver informe y repetir configuración congelada.
  Dos segmentos de 10 s del video local: **4/4 corridas**, repetición con solicitud,
  hashes de JSONL y hashes de comparaciones idénticos. Dos matrices adicionales
  sobre el código final 3cbd869 también conservaron identidad de código/solicitud
  y todos esos hashes. Datos y capturas privados.
- Runtime real conectado a Shaper/R24, clip CPU de 60 s recuperado de cache
  (1.800 frames). Tras calibración medida del torso, 30 muestras por modelo:
  ganancias efectivas no nulas en local 29/30, relacional 30/30, angular 29/30,
  colectivo 23/30. Son muestras de integración, no estimaciones comparables de
  eficacia ni validación del tracking. Se restauró la configuración local previa.
- Oliva PR #36, head eda50d29: **8 tests** y banco sintético ejecutados contra
  los módulos de esta iteración. Revisión publicada; directorios reservados
  intactos, sin merge. Se señaló colisión de tiempos entre épocas en su adaptador
  antes de extenderlo a loops/seeks; fixtures actuales de una época no afectados.

La aceptación histórica de Nicolás cubre 01c y el contraste temporal. No extender
esa aceptación a la mezcla nueva ×10/transientes, todos los modelos, métricas de
comparación o nuevas referencias. Cámara/hardware de captura no se volvieron a
validar físicamente en esta segunda entrega. CUDA sigue sin causa raíz resuelta;
se verificó recuperación CPU/cache y conservación de generación válida ante fallo
con worker simulado, además de reapertura del cache CPU real.

Pendientes explícitos: escucha humana de extremos y modelos; diagnóstico CUDA
#31; evaluación científica, audio PCM offline, grabación opcional y sensores/3D.
La agenda R01–R13 sigue vigente. Un visualizador polifónico no acredita cymatics
físico, profundidad 3D, intención ni un constraint armónico causal.

## Selección de cuerpo por generación — 2026-09-30

Suite Weaver: 246 tests + 4 subtests pasaron (138.41 s). Build TypeScript/Vite
correcto. Pruebas iniciales cubrieron elección requerida con dos personas (reemplazada
por selección automática por pedido de Nicolás), preferencia que
sobrevive a un store/runtime nuevo, invalidación al cambiar generación/fuente,
selección del prefijo guardada sólo tras completar y ausencia del cuerpo elegido
sin sustitución por otro. Replay conserva la persona elegida en una fuente doble.

Verificación adicional contra el cache local completo del nuevo minuto: dos
runtimes/stores sucesivos recuperan la selección de la derecha sin calibración
heredada. Se verificó checksum/medio usando el loader del comparador, sin arrancar
servicios ni tocar la configuración de Nicolás. El test local conserva sus datos
fuera de GitHub; no es validación de precisión de pose ni aceptación auditiva.

A pedido de Nicolás, los servicios iniciados por Codex se apagaron y no se
reinician durante sus pruebas. Arranque canónico: `scripts/start-laboratory.sh`
con R24 conectada; el modo `--no-audio` explica el 503 de telemetría observado.

## Selección automática y reproducción — 2026-09-30

Selección por cobertura observada o primer slot; prioridad para elección explícita
de la misma generación, sin trasladar calibración. Autoplay espera tracking listo
y respeta pausa manual. El seguidor de video espera metadata, evita seeks
repetidos y reproducción duplicada; selección de persona no recarga el elemento.
La aceptación visual de Nicolás permanece pendiente.

Validación de esta revisión: 15 pruebas runtime/evaluación/media, una prueba
Playwright del seguidor y build TypeScript/Vite pasan. Chrome headless decodificó
53 cuadros en dos segundos del archivo local (reproductor independiente del
transporte compartido). Esto verifica decodificación, no aceptación visual del
recorrido completo. La primera corrida de evaluación usó por error el venv del
workspace original sin PYTHONPATH; al usar PYTHONPATH=src pasó la corrida completa.

## PCM compartido — 2026-09-30

Weaver: **251 pruebas + 4 subtests**, 152.16 s, con Shaper compatible disponible
explícitamente en PYTHONPATH. Incluye cuatro pruebas de PCM: targets/features
idénticos con y sin render, longitud/recorte no alineado al reloj, muestras/hashes
repetibles, archivo y voice-frames, rechazo de motor congelado modificado y
servicio/API/repetición/artefactos permitidos. Estas cuatro pruebas se omiten si
no se instala un Shaper compatible; una suite sin ese repo no acredita PCM.

Shaper: **24 pruebas**, 10.59 s (offline, laboratorio, smoke audio, pads). Paridad
exacta del kernel offline/callback para 1/6/32 voces con timbre/pan/fase/release;
lease lógico, reloj inválido y rechazo de render sobre engine live.
UI: dos pruebas Playwright aisladas (controles PCM/links, seguidor de video) y
build TypeScript/Vite pasan. El harness de componentes usa Vite aparte, sin
API ni configuraciones de la sesión corporal compartida.

Fuente local real: minuto de dos cuerpos, slot derecho previamente verificado,
preset baseline de referencia con seis voces, 48 kHz / 256 samples, master Shaper
0.8, cola 0.2 s. Produjo **2 889 600 muestras estéreo**, pico 0.137206 y RMS lineal
0.038922. Repetición congelada CLI: hashes iguales de WAV, voice-frames y filas de
features/targets. No se copió el video; resultados permanecen en biblioteca local.
Estas medidas no son escucha, sensación corporal, loudness ni precisión de pose.

Una prueba inicial detectó que libsndfile escribe un timestamp de pared en PEAK:
las muestras eran idénticas pero el archivo difería. Render lógico pone ese campo
en cero, conservando picos y muestras, y lo declara en el manifest.

Recorrido de prueba: activar render en Comparar, seleccionar preset/segmento,
revisar master/sample-rate/bloque, ejecutar, escuchar/descargar WAV y repetir.
La escucha y la aceptación de esta entrega siguen pendientes. La sesión de prueba
continúa en la rama anterior; esta implementación está en los worktrees `-dev`.

Para el test UI aislado, iniciar `npm run dev -- --port 8767` en laboratory-ui y:
`LAB_COMPONENT_TEST_URL=http://127.0.0.1:8767 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/evaluationPCM.spec.ts tests/videoFollower.spec.ts`.

## Reproducción conjunta — 2026-09-30

13 pruebas específicas PCM/evaluación/API pasan, incluidas fuentes congeladas,
rechazo de fuente/artefacto alterados, requests Range y reutilización del checksum
cuando el archivo no cambió. Cuatro Playwright aislados: controles PCM, reloj de
muestras, seguidor live y reproductor conjunto. Video/audio sintéticos: decodifica
cuadros, sincronía visual dentro de 0.25 s, pausa, seek a un punto fuente conocido,
píxeles de la figura con seis voces y audio detenido al cerrar. El reloj unitario
comprueba offset del bloque recortado, interpolación gain/phase y no extrapolación
fuera de soporte. Build TypeScript/Vite pasa. No prueba latencia física ni escucha.

Durante el test se corrigió el arranque mientras el decoder estaba haciendo seek;
el harness también debe emular Range/206, como FileResponse, para que seek no se
reinicie a cero. Sólo se usaron imágenes sintéticas, sin tocar la sesión compartida.

Para repetir el test de navegador, generar un MP4 sintético con ffmpeg lavfi
`testsrc2=size=320x180:rate=30:duration=4`, H.264 y yuv420p. Iniciar Vite aislado
en puerto 8767 y ejecutar:
`LAB_COMPONENT_TEST_URL=http://127.0.0.1:8767 LAB_PLAYER_VIDEO=/ruta/synthetic.mp4 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/comparisonPlayer.spec.ts tests/replayClock.spec.ts tests/evaluationPCM.spec.ts tests/videoFollower.spec.ts`.
El test crea WAV/estado sintéticos en memoria; no publica medios corporales.

La misma prueba cubre recuperación sin WebGL: informa el problema y conserva
coordinación de video/audio. Prueba local adicional con MP4 y WAV float reales,
servidos por HTTP aparte de la sesión: 25 cuadros decodificados, diferencia
instantánea de relojes 0.100059 s, sin alertas, seek a 20 s alineado. Audio muted:
no acredita escucha/aceptación. Los primeros harnesses que interceptaban/redirectaban
medios fallaron; Chrome rechazó el redirect a loopback. Se verificó con entrega
HTTP nativa del mismo origen, sin cambiar permisos del navegador ni de la sesión.

## Base de captura Shaper — 2026-09-30

32 pruebas de captura/offline/laboratorio/audio/pads, 10.28 s. Identidad exacta
post-limitador con outdata, diferencia del tap anterior, límite 4800 muestras
incluido último bloque parcial, cierre temprano, cola acotada bloqueando writer,
disco fallido, gap/reloj/stream/callback status, id obsoleto e inicios concurrentes.
Todo fue sintético/hardware-free; no se grabó la sesión R24 ni se tocó configuración.
Vídeo/UI/colector/sincronía/recuperación quedan pendientes según CAPTURE.md.


2026-09-30 — Incremento de LAB-09: UI/API/colector de audio + journal confirmado,
nonce propio e inicio idempotente con Shaper #4, drenaje final completo y hashes.
22 pruebas Weaver y 33 Shaper; build web pasa. Integración sintética real confirma
PCM exacto. Ver CAPTURE.md para contratos y límites. No completa #17: video/mux,
latencia medida, identidad de código/fuentes y recuperación WAV pendientes. No
instalado sobre el workspace de pruebas; sin captura privada ni aceptación humana.


LAB-09 #42: prueba Chrome/Playwright aislada de controles de captura pasa;
23 pruebas colector/runtime/store/API y hashes de identidad. Shaper identifica
archivos/paquetes de captura. Identidades declaradas vs verificadas y limitaciones
para fuentes cambiantes documentadas en CAPTURE.md. No altera instrumento sonoro.


2026-09-30 — LAB-09: primer exportador web de video de archivo + PCM grabado,
MKV/H.264/pcm_f32le, plan causal muestreado configurable y huecos negros. 10 tests
plan, 6 exportación sintética real ffmpeg/OpenCV, 9 colector y 2 API (27 total);
Chrome/Playwright 1 y build web pasan. No altera venv original ni usa medios privados.
CAPTURE.md detalla sincronía estimada/offset, requisitos y pendientes de cámara,
medición, recuperación, overlays, inventario y playback. #17 no completado.


LAB-09 #43 actualizado: inventario de exportaciones al reiniciar, interrupted
explícito y descarga local con hashes y Range/206. 30 tests Python, 1 Chrome
componente y build web pasan. CAPTURE.md conserva límites y siguientes pasos;
cámara/recuperación WAV/sincronía medida/overlays/player siguen pendientes.


LAB-09: recuperación explícita de prefijo PCM confirmado con lock POSIX/metadata,
writer activo rechazado, originals conservados y estado recovered separado de
complete. 38 tests Shaper (incluido kill sintético), 31 Weaver, Chrome componente y
build web pasan. CAPTURE.md registra contratos/límites y trabajo aún pendiente.


LAB-09: opt-in de previews procesadas de cámara, budgets/cola/writer/clocks/hashes,
y exportación con elección de reloj y huecos explícitos. 45 tests pertinentes,
Chrome aislado y build web; PCM MKV sintético exacto. Sin cámara física/datos privados.
CAPTURE.md documenta preview vs flujo bruto, límites y pendientes de sincronía,
aceptación, recuperación de imágenes/journal, player y overlays. #17 sigue abierto.


LAB-09: recuperación conservadora de prefijos de journal, UTF-8/JSON/clock/sequence
con cortes explícitos y hashes; PCM válido conservado ante fallo de journal.
52 tests pertinentes y build web pasan; Chrome aislado de contadores/ruta.
CAPTURE.md y tabla vigente de IMPLEMENTATION_STATUS.md separan estado real e historia.


LAB-09: reintento de recuperación sólo con contrato idempotente; evidencia raw
sin cambios reutiliza resultado verificado, tampering se rechaza. 39 Shaper,
53 Weaver pertinentes y 14 colector tras estado unconfirmed pasan. Lock/recovery
in-flight todavía necesita job polling; ver CAPTURE.md. No modifica sonido/UI.


R01: banco sintético configurable web/CLI, procesos separados y request/manifests/
traces congelados. Estimador colectivo compartido, predictores sólo del pasado,
rotación/shuffle y dinámica no armónica. Evidencia real/repetida sin datos corporales;
research/laboratory/r01_grassmann/README.md registra observables y siguientes pasos.
Pruebas causalidad/rotación/repetición/worker/inmutabilidad, Chrome y build. No
completa R01 ni agenda R02–R13; no cambia instrumento/presets/aceptación humana.


R01: soporte compartido entre controles, paired.jsonl/hash, conteos de exclusión y
deltas sin inferencia causal/estadística. Vista pareada default sólo en Investigación,
reversible por checkbox; instrumento sin cambios. 15 tests research/API/collective,
Chrome aislado y build pasan. Evidencia sintética real/repetida en
research/laboratory/r01_grassmann/evidence-paired-2026-09-30.json. R01 no completado.


R01: descarga web de configuración/manifest/traces por id y contrato de nombres;
configuración coincidente y SHA-256 de traces, cache por fingerprint, Range/206 y
rechazo de cambios. 17 tests research/API/collective, Chrome enlaces y build.
Resultados locales sintéticos, sin publicación automática ni cambio sonoro. R01
permanece abierto para entrada corporal/HIT específicos y protocolo ampliado.

### Entornos de desarrollo independientes — 2026-09-30

Weaver-dev y Shaper-dev tienen `.venv` propios, instalados sin modificar los
originales. `start-laboratory-dev.sh --check` y `bash -n` pasan; no abren audio
ni cámara. Weaver: 30 pruebas de colector, recuperación de journals y banco
R01 pasan usando `.venv/bin/python` y `PYTHONPATH=src:../harmonic-shaper-dev/src`
para el contrato entre repos. Shaper: 15 pruebas de captura/recuperación pasan
con su propio `.venv/bin/python`. Sin ese PYTHONPATH, el test cruzado inicialmente
falló por no encontrar Shaper; no era un fallo del colector. La conexión R24,
latencia y aceptación del nuevo entorno siguen pendientes; no se inició el
laboratorio de desarrollo ni se modificó el proceso habitual en ejecución.

### Cancelación del banco R01 — 2026-09-30

13 pruebas R01 pasan: terminación de un proceso hijo real sintético, preservación
de archivos parciales, idempotencia, restauración del estado cancelado,
rechazo de descarga de trazas incompletas, protección de resultados completos,
finalización concurrente y distinción del cierre del servicio. El build de UI
pasa. No se abrieron fuentes corporales, audio ni cámara; no cambia la evidencia
científica ni los defaults del instrumento.

### Horizonte causal R01 — 2026-09-30

17 pruebas R01 pasan. Se verifica ajuste directo por pares separados, forecasts
inmutables al alterar observaciones entre origen y objetivo, rotación global,
repetición exacta, timestamps de origen/fit y ausencia de scores para historia
insuficiente. TypeScript/Vite pasa. Evidencia sintética 1/6/15 pasos repetida
sobre 149 objetivos comunes; scripts/configuraciones/hashes preservados. No hay
prueba de anticipación humana, causalidad corporal ni HIT.

### Descarga verificada de datos del comparador — 2026-09-30

12 pruebas de evaluación/PCM pasan con venv propio y checkout Shaper explícito.
Verifican restauración, descarga de request/manifest/features/comparaciones,
Range/206 y content-type, rechazo de archivos no declarados, alteración de
request/trace/comparación y symlink de trace; el informe también rechaza una
comparación modificada. Build TypeScript/Vite pasa. Fixtures sintéticos: no se
capturaron ni publicaron cuerpos y no se inició hardware.

### Ingestión de features en R01 — 2026-09-30

Contrato/snapshot/worker web conectado al comparador verificado. Suite R01+replay:
28 tests pasaron antes del cuarto test corporal de lookahead/persona; ese test se
agregó y se verificó por separado. Dos pruebas Chrome aisladas y build pasan.
Se prueban hashes, faltantes, reset de forecasts, tiempos irregulares, no-score,
deduplicación, unidades incompatibles, segmento fuera de fuente, snapshot alterado,
worker real/reinicio/download, API de selección y límites. Sin datos privados en
fixtures/commits.

Corrida corporal local separada: fragmento dúo de 60 s, fuente/persona/cache de la
evaluación previamente verificada, seis velocidades en T/s. Snapshot conserva
procedencia/calibración sin aplicarla al instrumento. Repetición exacta de artefactos;
resultados en estado laboratory-dev únicamente. No se abrió/capturó hardware ni se
copió el original; lectura de cache y features. Esta evidencia no prueba precisión
geométrica, causalidad/intención, HIT ni aceptación de la sonificación.

### Carrera de cierre de cámara — 2026-09-30

Prueba concurrente con JPEG sintético bloqueado: cierre iniciado, frame tardío
rechazado, frame aceptado drenado y hash estable al repetir cierre. Cinco pruebas
de writer y colector integradas con Shaper explícito; sin cámara física. El primer
comando omitió PYTHONPATH del contrato cruzado y falló por import de Shaper;
se corrigió el entorno de prueba, sin modificar entornos originales.

### Prefijo de cámara recuperable — 2026-09-30

Pruebas de fila truncada, raw sin cambios, hashes de imagen, symlink, writer activo,
complete/legacy rechazados y proceso hijo real terminado con SIGKILL. Prefijo
verificado preserva imágenes originales; no se recupera una imagen inferida.
Suite writer/colector y build pasan; sin cámara física ni medios privados.

### Soporte común en propagación — 2026-09-30

Regresión controlada: dos predictores con salida idéntica y retardos disponibles
distintos deben producir mejora cero al evaluar objetivos compartidos. Se
verifican tamaños distintos de soporte individual y conteo común. Suite de
colectivo, propagación, modelos y replay verifica también predictor causal,
retardo sintético conocido, ausencia de centros forzados y paridad del baseline.
No hay escucha nueva ni evidencia de causalidad corporal.

### Cambios de forma regional — 2026-09-30

Regresión: calentar predictor y luego cambiar número de regiones/dimensiones debe
volver a warming, con una sola observación de la nueva forma y sin modelos/errores
anteriores. Timestamp no finito y soporte vacío limpian historia. Suite de
propagación/colectivo/modelos pasa; sin cambios de defaults o baseline aceptado.

### Preview MP4 de captura — 2026-09-30

12 pruebas de exportación pasan: H.264/AAC declarados, fotogramas decodificados
idénticos a MKV, PCM exacto conservado, hashes/inventario/reinicio/tampering,
fallo de preview sin perder MKV. Build pasa. Chrome aislado reprodujo MP4 sintético:
metadata lista, pausado al abrir, tiempo avanzó tras play silenciado y cierre quitó
el elemento. UI verificó opt-in/bitrate enviados. Sin cuerpos, cámara real ni audio
físico. Compatibilidad comprobada en Chrome local, no en todos los navegadores.

### Auditoría acumulada de integración — 2026-09-30

[Auditoría](INTEGRATION_AUDIT.md): 143 tests laboratorio/R01 Weaver, 153 Shaper,
7 Chrome aislados pasan en los heads publicados #60/#6. Servidor de prueba detenido;
no se iniciaron audio/cámara ni se modificó el laboratorio habitual. Se detectó
entorno distinto entre renderer y Shaper; igualdad PCM entre procesos y pin de
entorno son pendientes explícitos de #18, no cubiertos por estos tests.

### Pin de entorno y comparación entre intérpretes — 2026-09-30

Request/renderer/servicio fijan y verifican entorno separado del código. Seis
pruebas PCM pasan, incluyendo discrepancia antes de WAV, API repeat rechazada,
legacy rechazado por API/CLI y repetición nueva exacta. Suite previa combinada
PCM/evaluación: 13 tests. Build y Chrome del panel pasan.

Protocolo hardware-free en research/laboratory/audio_environment: controles
sintéticos idénticos sobre ambos intérpretes, seis voces/150 bloques, shape/pan/
fases y liberación. 38400 muestras estéreo idénticas por SHA-256, máxima diferencia
cero, archivos del motor coincidentes. Evidencia sintética publicada, sin cuerpos.
Sólo prueba esa secuencia: no generalizar a otros parámetros/plataformas ni
latencia física. No se alteraron venvs ni se inició audio/cámara.

### Diagnóstico de repetición legacy — 2026-09-30

Nueve pruebas replay/evaluación pasan: inventario legacy informa repetición no
soportada mientras informe/manifest continúan accesibles. Build pasa; Chrome
verifica botón de repetición deshabilitado con motivo visible y acceso al informe/
artefactos. Fixtures sintéticos, sin cambios de venv, datos privados o audio.

### Request congelado al repetir — 2026-09-30

Pruebas de request alterado tras reiniciar, sidecar alterado, fallback a manifest
histórico y legacy con identidad de contenido correcta pero sin entorno. Request
modificado se rechaza antes de crear otro job; consulta de resultados se conserva.
La prueba API de PCM distingue alteración del request de discrepancia de entorno.
No cambia audio, presets, fuentes ni entornos originales.

Se detectó y corrigió un fallo real del primer control: default tail_s 0 se
revalidaba como 0.0 en el worker. Nuevos requests se normalizan antes del freeze;
históricos comparan contenido con equivalencia numérica restringida y digest
verificado. Tras corrección: 17 tests PCM/evaluación pasan; suite evaluación con
regresión numérica adicional pasa. No se relaja identidad de código/entorno.


## 2026-09-30 — continuidad del decoder durante drift

VideoFollower corrige desfases ordinarios menores a 2 s con playbackRate limitado
a 0.9–1.1; seeks/loops siguen usando salto explícito. No consume discontinuidades
mientras un seek o play esté pendiente. La velocidad del audio no se modifica.
Tres pruebas pasan, incluida reproducción real de MP4 H.264 sintético en Chrome:
tiempo y fotogramas avanzan durante actualizaciones con desfase de 0.6 s, sin
nuevos seeks. Build TypeScript/Vite pasa. Esto no prueba la interacción completa
de selección de Persona ni aceptación visual de Nicolás; ambas siguen pendientes.
La corrección está aplicada y compilada en harmonic-weaver-lab (b63ee20), sin
reiniciar servicios ni tocar R24; esta rama mantiene la misma corrección para dev.


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


## Cámara en exportación de prefijos recuperados

2026-09-30: el exportador consume el índice recuperado con hash verificado y
reverifica cada JPEG en su frame_root original antes de decodificar. Rechaza
symlinks del root/índice/imágenes y cambios de contenido; no copia imágenes.
20 pruebas export/input pasan, incluida recuperación real de índice sintético,
FFmpeg, fotograma azul y PCM exacto, y rechazo posterior de JPEG alterado. Build
pasa. Captura sigue recovered_partial y gaps siguen negros. Cámara física,
sincronía medida y preview integrada de prefijos permanecen pendientes.


## Preview de cámara recuperada — 2026-09-30

14 pruebas export pasan. El caso de cámara parcial genera también MP4 H.264/AAC
y conserva PCM exacto en MKV. Chrome CapturePanel consume ese mismo MP4 sintético
(vía fixture local), verifica readyState, avance currentTime, cierre y aviso de
captura parcial. El primer intento descubrió un selector de prueba ambiguo entre
el aviso de exportación y prefijo PCM; se corrigió con coincidencia de inicio.
No prueba el recorrido completo API/server ni cámara real/sincronía física.
Artefactos sintéticos en /tmp/weaver-prefix-preview-validation, fuera del repo.


## Export recuperado por API y reinicio — 2026-09-30

15 pruebas export pasan. Nueva integración con FastAPI TestClient y FFmpeg real:
POST rechaza captura interrumpida sin recovered_prefix; con opción explícita
produce MKV/MP4, polling confirma export completo y captura parcial. Un segundo
create_app reconstruye inventario, sirve preview con HTTP Range 206 y rechaza
contenido alterado con 422. Captura original sigue interrupted. Runtime sintético
no abre dispositivos. Complementa Chrome del panel; no es un navegador unido a
servidor por red ni verifica cámara física, sincronía o aceptación humana.


## Entradas alteradas durante exportación — 2026-09-30

Antes de confirmar capture.mkv, el exportador rehashea PCM, bloques, timeline,
eventos e índice/JPEG de cámara. Un cambio detectado deja manifest failed y no
confirma el MKV final. 19 tests export pasan; cuatro controles editan entradas
después del primer fotograma y comprueban el rechazo. Aplica a capturas completas
y prefijos, con la misma ruta de render. No es snapshot de filesystem ni defensa
ante modificación/restauración entre lecturas; originales de video siguen con
identidad declarada como documentado. No cambia síntesis ni defaults.


2026-09-30 — procedencia de recuperación: 25 tests export/input pasan. Los casos
de cámara y archivo comprueban recovery_provenance, identidad PCM, carpeta
journal y frame_root/conteo de cámara; sin cámara el campo es null. Mantiene
separación entre hashes de entradas verificados y source_hashes_declared. No
cambia audio, presets ni defaults.


2026-09-30 — marcas humanas tipadas: 3 tests API pasan y build pasa. Se verifica
persistencia/reinicio, categoría preparation y rechazo de categoría desconocida
sin nuevo evento. Nota libre queda default y clientes antiguos siguen aceptados.
UI compilada, interacción/aceptación humana pendientes. No cambia audio.


Marcas R03 — interacción Chrome: el componente utilizado por main se verifica
con Vite aislado. Categoría/texto no generan llamadas; guardar envía payload
correcto; error conserva texto; éxito limpia texto y mantiene categoría. Default
nota libre y botón vacío deshabilitado comprobados. Una prueba Chrome y build
pasan. API es fixture en esta prueba; integración de persistencia cubierta por
los tests API anteriores, no aceptación humana.


Snapshot de marcas: 5 tests API/store pasan, incluyendo 1005 marcas sin truncado,
hash repetible/reinicio, cursor creciente y prefijo conservado. Primer intento
incluía session_id actual y falló al reiniciar; corregido conservando IDs por
evento. Build pasa. Descargar no implica publicar ni interpretar onset físico.


Filtro de marcas: 6 tests API/store y build pasan. Dos personas y dos fuentes
sintéticas: selección exacta devuelve sólo evento correspondiente, desconocida
queda vacía, historial completo permanece idéntico y cursor no cambia. Enlace
web compilado, interacción del enlace y aceptación humana pendientes.


Selección temporal/categoría: 7 tests API/store, Chrome MovementMarks y build
pasan. Se verifica inicio incluido/fin excluido, rechazo de nan/negativos/inversión
y categoría desconocida; web genera query correcta y oculta enlace inválido.
No cambia guardado de marcas ni audio; no afirma alineación física de anotaciones.


Épocas de marcas: 14 tests runtime/API pasan. Marca antes/después de seek y
antes del siguiente tick conserva distinción observado/transporte y frame previo;
tras tick, épocas coinciden y frame avanza. Primer fallo fue cleanup del fixture
Audio sin close, corregido sin tocar audio de producción. Sin hardware ni prueba
de latencia humana.


Selección sesión/época: 8 tests API/store y build pasan. observed_epoch exige
session_id explícito, entero no negativo; selección distinta vacía, marcas
sin época no se reinterpretan. Web ofrece campos opcionales; interacción de
estos campos pendiente. Valores pueden consultarse en el JSON descargado, no
son identidad biométrica ni onset físico.


Selector de época actual: runtime snapshot expone observed_epoch del último
tick, distinto del epoch de transporte. Botón explícito copia sesión/época al
filtro, no las sigue automáticamente ni guarda/inicia análisis. Chrome verifica
valores/query y ausencia de llamadas. 7 tests runtime, Chrome y build pasan.
No observado => botón deshabilitado; interacción humana completa pendiente.


Cursor repetible de marcas: 9 tests API/store y build pasan. Descargar, agregar
marca y repetir through_sequence conserva JSON/hash exactos; cursor cero vacío
y valores negativos/futuros rechazados. Campo web compilado; interacción de
este campo pendiente. No cambia defaults del instrumento.


R03 matching temporal: 7 tests sintéticos pasan (one-to-one, mínimo lag, soporte
común/gaps/extremo excluido, offset declarado, repetición y vacíos/invalidación).
Sin datos corporales ni cambio del instrumento. Integración API/UI y estudio
con anotaciones/candidatos reales pendientes.
