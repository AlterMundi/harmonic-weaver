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


R03 emparejamiento — 9 tests pasan. Control de soporte contiguo detectó borde
artificial: intervalos adyacentes ahora se unen sin inventar gap; gaps reales
siguen bloqueados. Un oracle exhaustivo independiente enumera asignaciones
para 64 pares de conjuntos de hasta 3 eventos y confirma cardinalidad máxima
y costo absoluto mínimo, sin suponer orden monótono en el oracle. Esto verifica
el núcleo, no candidatos corporales, UI, protocolo científico ni intención.


R03 candidatos: 14 tests candidatos/matching pasan. Prueban ausencia de evento
inicial/held, consumo de cruce durante refractario, rearme bajo después de gaps,
invariancia causal del prefijo y rechazo de clocks/settings inválidos. No modifica
activación sonora: extractor sólo en research y aún sin integración web.


R03 entrada de marcas: 15 tests mark_input/candidates/matching pasan. Snapshot
real SessionStore, repetibilidad, cambio de texto/hash, persona distinta y seek
pendiente cubiertos. Sin datos corporales ni integración de banco/UI.


R03 adapter features: 6 tests candidate_input/body pasan; adapter con fixture
de missingness y reader real sobre comparación/replay sintético. Se verifica
procedencia compartida, T/s, una señal y holds excluidos. No prueba todavía
compatibilidad de identidad entre marca live y asset replay ni banco completo.


Identidad de marcas live/replay: 18 tests runtime/API/mark_input pasan; controles
de binding prueban otra generación e identidad ausente. Cache usa media_sha256
(no media_id); adapter explicita correspondencia. Hash de biblioteca declarado
no constituye verificación nueva del video ni identidad biométrica. No banco
integrado ni prueba corporal de ese binding todavía.


R03 contraste integrado preliminar: 17 tests coincidence/mark_input/candidates/
matching pasan. Snapshot real + features sintéticas, match y soporte esperado,
repetición exacta, alteración de features y persona incorrecta rechazadas. No
job persistido, UI, controles temporales ni evidencia corporal todavía.


R03 run_frozen: prueba integrada pasa con dos corridas independientes, SHA
result.json idéntico, output verificado y rechazo de sobrescritura. Inputs
SQLite/sintéticos preparados localmente. Lock/errores de proceso y API/UI
requieren cobertura adicional; sin hardware ni datos corporales publicados.


Worker R03 — 20 tests de núcleos/worker pasan. Lock ocupado rechaza sin crear
manifest; request desconocido deja failed sin output; mutación y sustitución
por symlink durante compare impiden result.json y dejan failed. El cálculo se
sustituye en estos últimos controles para provocar la carrera deliberadamente,
no son pruebas científicas. Worker.lock symlink rechazado. Falta crash/restart
y administración API/UI; no se promete protección frente a cambios/restauración
entre checks ni fallo de disco al escribir manifest.


R03 crash/restart: 5 tests de contraste/worker pasan. Un child real mantiene
writer lock durante comparación sintética bloqueada; inspect_run conserva
running mientras activo. Tras SIGKILL y wait del mismo proceso, restaura
interrupted preservando hashes y sin resultado/relaunch; lectura posterior
idempotente. Relee manifest bajo lock para no pisar completion concurrente.
Servicio R01 usa otro formato y requiere adapter R03; API/UI aún pendientes.


Servicio R03: 5 tests worker/contraste pasan, incluido subprocess real vía
CoincidenceService, inventario restaurado y resultado igual a corrida directa.
Whitelist/traversal/alteración de artifact comprobados. Cancelación y API/UI
aún requieren integración/cobertura; no se abrió audio ni tracking.


R03 API inicial: POST /api/research/r03 congela CandidateRequest desde el
lector verificado de evaluación y marcas del store con persona/fuente/sesión/
época/categoría y through_sequence explícitos. mark_support es lista de
intervalos [inicio,fin), nunca inferida de botones. tolerance_s (0–10 s) y
mark_offset_s (−10–10 s) son explícitos; offset no se estima. Valida binding de
medio/cache/generación/persona antes de lanzar worker. GET inventario y
artifacts, POST {id}/cancel reutilizan servicio R03; cierre sólo workers propios.
7 tests API/worker pasan: child real, corte de marcas preservado tras append,
restauración al recrear app, descarga idéntica, tampering/whitelist rechazados,
intervalo invertido/persona incorrecta y ausencia de biblioteca rechazados.
Reader replay mockeado en este test HTTP; lector real tiene cobertura separada
y aún falta integración browser/API/replay completa. No audio ni datos privados.
UI R03, controles temporales y experimento humano siguen pendientes.


R03 UI inicial en pestaña Investigación: comparación/corrida/señal, grupos
explícitos de marcas por fuente/persona/sesión/época/categoría, corte congelado
y cobertura JSON [inicio,fin) manual. Configura high/low/refractario/gap/
tolerancia/offset; no deriva cobertura de botones. Actualizar el corte deselecciona
el grupo. Configuración portable sólo settings y signal_id, no contexto humano.
Inventario, cancelar, descargar artefactos y ver precisión/recall/soporte común.
Prueba Chrome aislada pasa: cobertura inválida/ausente y tolerancia fuera de
rango bloquean ejecución; payload conserva contexto/cursor; export excluye
contexto, refresh exige reselección y resultado visible. Build TS/Vite pasa.
API simulada en prueba UI; todavía falta recorrido browser/API/replay real,
controles temporales y aceptación humana. No cambian defaults del instrumento.


R03 integración evaluación→lector real→API→worker: fixture de pose sintética
produce replay causal local en caché CPU explícita. candidate_snapshot real
verifica artefactos, unidades/procedencia y excluye control holds. Marcas
sintéticas ligadas al mismo manifest/cache/generación; no anotación humana real.
Dos POST HTTP producen exactamente mismos bytes de resultado y coinciden con
compare_frozen directo (entrada normalizada: límites float, corte explícito).
Features descargadas iguales al lector. Alterar trace hace fallar otro POST antes
de crear worker; inventario conserva dos corridas. Tres tests integración/API
pasan. Se corrigió referencia de prueba: corte omitido y límite int vs float
son entradas diferentes para hashes; no se relajó el chequeo de igualdad.
Esta prueba usa TestClient, no browser contra servidor de red ni cuerpo humano.
Pendientes browser/API real, cancelación concurrente y controles temporales.


R03 ciclo de vida: 12 tests servicio/worker/API pasan, cinco casos nuevos
con children reales. Cancel queued y running deja cancelled, close deja
interrupted y confirma proceso terminal; hashes de entrada se preservan,
resultado inexistente no se descarga. Cancel de completed preserva output;
cancel repetido es idempotente. Instancia restaurada no cancela procesos ajenos
ni altera estado. Dos threads con barrera contra un mismo servicio admiten
un solo child; después de cancelar admite otro en carpeta nueva. close ahora
marca closed bajo el mismo RLock y rechaza start posterior: evita un child
que escape del cierre. No verifica admisión global entre instancias distintas
ni carrera completion exactamente durante terminate. No hardware/audio.


R03 controles temporales declarados: offsets opcionales (default [], sin
cambio de audio), hasta 16 distintos no nulos ±10 s; suma con offset manual
también limitada. Cada condición tiene métricas disponibles y paired sobre
intersección idéntica del soporte de todas las condiciones, sin puentes por gaps
ni circular wrap. Cuenta marcas/candidatos elegibles por condición: mismos
segundos no implica mismos denominadores. No optimiza offsets ni calcula
p-values. UI permite JSON de offsets, configuración portable y tabla comparativa.
10 tests núcleo (incluye soporte fragmentado/empty/invalid), API con child real
confirma controles congelados, Chrome panel pasa payload/invalid/export.
17 tests núcleo/worker/API pasan antes de ampliar API a controles; luego 12
núcleo/API y Chrome pasan con controles. Build TS/Vite pasa. No evidencia
corporal/humana ni significación; controles elegidos post-hoc son exploratorios.


R03 browser→HTTP→lector replay→worker completo: Chrome contra Uvicorn
localhost aislado sirve bundle CoincidencePanel con fetch real, sin route mocks.
Fixture pose/cache y marcas sintéticas, sin dispositivos ni medios privados.
Selecciona comparación/señal/grupo, declara cobertura y shifts ±0.1 s, ejecuta
dos workers; resultados iguales byte a byte, tabla de tres condiciones visible,
features.json descarga real con nombre esperado. No errores de API visibles.
No es recorrido completo de main/WebSocket ni escucha/aceptación corporal.
Servidor propio detenido al terminar. Reproducción:

```bash
npx --prefix laboratory-ui vite build laboratory-ui/tests/r03_harness --outDir /tmp/weaver-r03-network-ui --emptyOutDir
PYTHONPATH=src:tests:../harmonic-shaper-dev/src .venv/bin/python tests/r03_http_fixture.py --root /tmp/weaver-r03-fresh-unique --ui /tmp/weaver-r03-network-ui --port 8879
# En otro terminal, desde laboratory-ui:
LAB_R03_NETWORK_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/coincidenceNetwork.spec.ts --reporter=line
```

Root de fixture debe ser nuevo (no sobreescribe); Ctrl+C cierra servicio y
workers propios. Prueba exige endpoint de fixture explícito, no usa lab del
usuario por defecto. Aún pendiente experimento humano y agenda científica R03.


R04 prerrequisito (2026-09-30): RelativeMode de producción valida reloj finito
no negativo y vector 2D finito antes de actualizar historia. Faltante/vector
no válido/tiempo inválido limpian historia, anterior y derivador; no propagan
NaN a observaciones posteriores. Nueve casos inválidos se recuperan tras
warmup fresco; 11 tests existentes modelos/matemática pasan. Sin cambios de
defaults ni síntesis; no prueba interferencia física, técnica ni HIT. Próximo:
banco R04 usando este mismo estimador y controles de rotación/inversión/
oposición, con configuraciones y evidencia reproducibles.


R04 banco sintético inicial: [protocolo y CLI](../../research/laboratory/r04_relational/README.md) usa
RelativeMode de producción en cinco escenarios de Anni con rotación uniforme,
inversión de ambos extremos y velocidad común. Dos tests pasan: invariancia
numérica, frenado contextual, prefijo causal, repetición SHA y no overwrite.
CLI real 30 muestras produce valores declarados en README; son construcciones
sintéticas, no evidencia corporal. Pendientes backend/UI, replay verificado,
oposición local favorable y controles de emparejamiento/ruido/ángulos/humanos.


R04 servicio/API inicial: RelationalService comparte ciclo de vida owned con
R03, pero root research/r04, inputs request.json y whitelist propios. Worker
flock congela hash request, compara tras cómputo, publica result/manifest sólo
con hash confirmado; error deja failed. Inventario restaura por mismo protocolo
de writer lock; close sellado y cancel sólo child propio. POST/GET
/api/research/r04, {id}/cancel y {id}/artifacts/{name}. Dos tests propios
con child real cubren restauración/hash/tampering/whitelist/inventario separado
y HTTP real TestClient; 11 servicio/worker/lifecycle R03 antes de conectar API,
9 R04/R03 API+lifecycle después pasan. No dispositivos/audio. Pendientes panel
R04, browser/red R04, interrupción específica a mitad de cómputo y replay
corporal/control de oposición favorable. No ciencia resuelta.


R04 panel web inicial en Investigación: todos los 10 parámetros del banco
editables, validación de rangos y samples entero, JSON portable importar/exportar.
Inventario/cancel/artifacts/result; traza y muestra seleccionables con valores
I/R/A y velocidades de extremos. Faltantes se muestran indefinidos, nunca cero
ni neutralidad. Prueba Chrome aislada pasa edición sin llamadas/ejecución
congelada/rango inválido/export-import sin ejecutar/resultado faltante. Build
TS/Vite pasa. API simulada en este test UI; backend con child real probado
separado. Pendientes browser→API real R04, entrada corporal y controles ampliados.
No cambian defaults del instrumento ni audio. Vite propio detenido al finalizar.


R04 browser→API→worker verificado por Chrome contra Uvicorn real, sin mocks.
Panel aislado usa fetch same-origin, servidor sin runtime/audio/cámara. Dos
corridas de 30 muestras producen bytes de resultado idénticos; 20 trazas,
request.json descargado con nombre correcto. UI mantiene I/R/A indefinidos
para aceleración compartida; muestra 10 del mismo frenado distal da I=−1
con proximal quieto y +1 con proximal móvil. No errores API visibles. Servidor
propio detenido con shutdown confirmado. No verifica main/WebSocket ni datos
corporales reales; entrada corporal y controles ampliados siguen pendientes.

```bash
npx --prefix laboratory-ui vite build laboratory-ui/tests/r04_harness --outDir /tmp/weaver-r04-network-ui --emptyOutDir
PYTHONPATH=src .venv/bin/python tests/r04_http_fixture.py --root /tmp/weaver-r04-fresh-unique --ui /tmp/weaver-r04-network-ui --port 8879
# Otro terminal, desde laboratory-ui:
LAB_R04_NETWORK_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/relationalNetwork.spec.ts --reporter=line
```

Root debe ser nuevo: fixture nunca pisa inventario previo. Ctrl+C cierra
servicio/workers propios. URL explícita requerida; no usa laboratorio del usuario.


R04 fallos específicos del worker: 8 tests worker/servicio pasan. Requests
mutados en contenido o reemplazados por symlink, resultado alterado y manifest
interno symlink no pueden confirmar output; quedan failed sin result raíz.
Lock ocupado no crea manifest; settings inválidos quedan failed. Child real
produce computed/result, mantiene lock antes del commit externo; inventario
lo conserva running. SIGKILL+wait permite restaurar interrupted con hashes,
idempotente, sin descargar resultado interno ni relanzar. Worker ahora valida
manifest computed regular/no symlink antes de leerlo. No verifica todos los
puntos de crash del filesystem ni hardware; replay corporal sigue pendiente.


R04 entrada de extremos corporal, preparación inicial: EndpointRequest elige
evaluación/run, COCO parent/child distintos y segmento ≤120 s. Lector carga
generación de pose congelada/hash mediante load_source; no copia video ni
recalcula tracking. Exige escala/procedencia de calibración congeladas para
esa persona; Kinematics causal de producción con settings del preset, warmup
desde inicio seleccionado sin preroll inventado. Velocidades T/s, faltantes
explícitos, reloj estricto y límite 14400. Snapshot conserva código de
Kinematics/analysis/contracts, escala/settings/source/cache/preset. Test con
replay sintético real pasa repetición exacta, warmup/gaps/contexto y rechazo
de extremos iguales/fuera de segmento/generación alterada. No medición
corporal nueva ni observación humana; worker/API/UI corporal aún pendientes.


R04 extremos congelados→contrastes→worker/API: start_body congela request e
input.json del lector verificado. Worker incluye ambos hashes y verifica
cambios antes de commit. probe_endpoints usa RelativeMode real en original,
rotación uniforme, inversión de ambos y velocidad común, con relojes/validez/
vectores/unidad/segmento validados. Faltantes reinician historia sin relleno.
Samples/hz sintéticos se declaran unused; no resampling. Resultado conserva
scale/settings/provenance/code y límites. POST /api/research/r04/trace recibe
{settings,selection}; descarga input verificada. Nueve tests integración/
worker/servicio pasan: replay sintético real, dos children con SHA idéntico
y mismo resultado directo, invariancia numérica, HTTP con lector real.
Panel corporal R04 y recorrido browser siguen pendientes. No ejecución corporal
humana nueva ni calibración transferida/audio cambiado.


R04 selección corporal web: comparación/run, COCO proximal/distal, segmento
configurables con persona/escala/procedencia congeladas visibles. Usa settings
relacionales de panel principal, samples/hz no aplican a pose. Bloquea ausencia
de calibración explícita, extremos idénticos y límites fuera de segmento.
No transfiere calibración ni ejecuta al editar. Chrome dos tests panel/panel
corporal pasan payload seleccionado, bloqueos e import/export existentes;
build TS/Vite pasa. Test UI con API simulada; backend lector real/child probado
separado, recorrido corporal browser→API real todavía pendiente. Endpoints
no se incorporan aún al JSON portable; fuente/calibración no se transfieren.
No defaults de audio modificados. Vite propio cerrado.


R04 recorrido de entrada corporal browser→HTTP→lector pose→worker pasa con
fixture de pose sintética real en cache. Chrome elige COCO 7/9, segmento .2–2,
efectúa dos corridas con bytes idénticos; cuatro contrastes, faltantes y
relaciones observadas. Snapshot input.json descargado realmente; UI muestra
persona one/escala/unidad del resultado congelado, no de fuente actual.
API/lector no mockeados, sin dispositivos ni datos corporales privados.
Servidor propio cerrado. No evidencia humana ni main/WebSocket completo.

```bash
npx --prefix laboratory-ui vite build laboratory-ui/tests/r04_harness --outDir /tmp/weaver-r04-body-network-ui --emptyOutDir
PYTHONPATH=src:tests:../harmonic-shaper-dev/src .venv/bin/python tests/r03_http_fixture.py --root /tmp/weaver-r04-body-fresh-unique --ui /tmp/weaver-r04-body-network-ui --port 8879
# Otro terminal, desde laboratory-ui:
LAB_R04_BODY_NETWORK_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/relationalBodyNetwork.spec.ts --reporter=line
```

Reusa fixture R03 de evaluación/pose, no inputs privados. Root nuevo requerido.
Extremos portables y controles ampliados de oposición/ruido siguen pendientes.


R04 configuración corporal portable v1: export/import JSON con schema_version,
settings y endpoints COCO. Valida versión/keys/índices/distinción y parámetros
antes de aplicar; no incluye fuente/persona/escala/calibración/segmento.
Importar no corre worker ni cambia selección fuente/segmento. Dos tests Chrome
panel/body pasan recuperación de extremos/settings, segmento preservado y
cero llamadas al editar/importar; build pasa. No aceptación humana ni nuevos
experimentos corporales; controles ampliados y evidencia siguen pendientes.
No cambian defaults de síntesis; Vite propio cerrado.


R04 perturbación local proximal: proximal_multiplier configurable ±4
(default −1 sólo banco investigación; audio intacto). Nueva condición
proximal_scaled transforma únicamente velocidad proximal antes de RelativeMode: 
−1 invierte, 0 detiene, 1 conserva original. Sintético ahora 25 trazas, pose
5 condiciones. No supone pose físicamente posible ni oposición beneficiosa.
Tres tests banco, dos servicio y uno lector real/worker pasan (6 total);
identity multiplier=1 da mismas traces que original, inversión local en
shared_acceleration cambia missing a relación reforzada construida. Controles
globales conservan invariancia; no se exige invariancia local. Dos Chrome
panel/body pasan edición/payload/JSON y build pasa. Network tests actualizados
a nuevos conteos pero no reejecutados en este incremento. Control de tarea/
valor global, ruido/emparejamiento y anotación humana siguen pendientes.


R04 requisito de calibración auditado: evaluación local existente del fragmento
de dos personas/cuerpo indicado está complete pero baseline sin escala ni
procedencia. No se ejecutó R04 real inventando normalización ni se alteró
inventario/calibraciones privadas. Próxima corrida corporal exige calibración
explícita para esa fuente/persona y una evaluación nueva que la congele.
Test de integración nuevo con replay baseline sin escala confirma endpoint
reader y POST /trace rechazan antes de worker; inventario R04 vacío y tabla
de calibraciones idéntica. Dos tests integración pasan, incluido positivo
con escala explícita. Esto no bloquea bancos independientes ni cierra R04.
No publicar IDs/rutas/hashes/medios privados.


R04 ruido reproducible: perturbation_std (0–2, default 0) y
perturbation_seed (0–2147483647, default 0) en API/UI/JSON. Nueva condición
noisy_endpoints añade ruido gaussiano independiente a velocidades preparadas,
no a pose cruda. Sintético usa streams por escenario para conservar prefijos;
pose consume ruido por observación y no vuelve válido ningún faltante.
Ahora 30 trazas sintéticas/6 condiciones pose. Ocho tests banco/servicio/
entrada pasan; añadido test sintético semilla distinta sólo cambia ruido,
misma repite, cero exacto y prefijo causal. Test pose real sintética verifica
ruido repetible, prefijo y faltantes todavía missing; dos tests entrada pasan.
Dos Chrome panel/body y build pasan. Network conteos actualizados pero no
reejecutados aquí. No ruido calibrado de cámara ni estimación de robustez
corporal todavía, ni cambio de audio. Vite propio cerrado.


R04 resúmenes pareados: summarize intersecta timestamps observados exactos
de todas las condiciones y reporta disponibles/pareadas/excluidas, medias
I/R/A y MAE vs original en esa misma muestra. No medios estimados en soportes
distintos. Soporte en segundos sólo entre rows adyacentes en TODAS las
condiciones y dentro de max_gap: no puente sobre fila missing ni extrapolación.
Medias por muestra, no integral temporal. Empty produce None, no cero.
Resultados sintéticos por escenario y de pose incluyen resúmenes/hash de
módulo; panel muestra tabla. Once tests summary/banco/entrada pasan: cinco
nuevos comunes/availability desigual/gaps/empty/invalid, reader real/worker
existentes mantienen repetición. Chrome panel/tabla y build pasan. Tests
network selectores actualizados sin rerun aquí. Estadística descriptiva, no
significación/eficacia ni aceptación corporal humana. Vite propio cerrado.


R04 revalidación network tras controles/resúmenes: Chrome corporal y
sintético contra mismo Uvicorn aislado con std=.02/seed17 pasan; cada
recorrido repite dos workers con resultados idénticos byte a byte. Tablas
noisy_endpoints visibles, settings congelados correctos y denominadores
pareados iguales en resultado de pose. Downloads reales conservados.
Primer intento sintético falló por selector global de indefinidos: nuevas
tablas muestran None legítimos, por lo que se limitó assertion a Muestra R04.
No cálculo cambiado; rerun del test afectado pasa. Servidor y children
propios cerrados. Fixture pose sintética, no evidencia humana ni hardware.
Actuales 30 traces sintéticas y 6 condiciones pose, con proximal/noise.
Reproducir con fixture r03_http_fixture + harness R04 y variables
LAB_R04_NETWORK_URL / LAB_R04_BODY_NETWORK_URL al mismo endpoint8879.


R05 núcleo inicial aislado: resonadores complejos pasivos con pasos exactos
expm, seis voces default (ampliables32), ratios/carriers/amortiguamiento/grafo
configurables por contrato Python. Siete tests impulso analítico, cola libre,
partición de bloques/fase/reset/silencio, norma libre no creciente y invalid
pasan. No audio/live ni parámetros aceptados cambiados. Norma interna no
es energía física; coupling puede cambiar modos efectivos, opción separada
de investigación. [Protocolo](../../research/laboratory/r05_resonators/README.md). Worker/API/UI,
excitación desde features, PCM/figura y niveles/latencias comparables pendientes.
No experimento humano ni claim HIT.


R05 excitación causal inicial: prepare acepta documento de selección
single-signal congelada (compatible CandidateRequest/snapshot verificado),
unidad explícita, settings y sr/nvoices. Modos threshold_crossings (impulso
fijo) y positive_delta (diferencia positiva cruda, no aceleración), gain,
reference_scale/unidad, max_impulse, umbral delta, thresholds/refractario/gap,
6–32 pesos de voces independientes. Eventos sparse con hash input/provenance
y sample_index ceil relativo a inicio: no anticipar observación. Reusa detector
causal R03; primer high y recuperación no reactivan, held no repluck ni
refractario retrasado. Tres tests propios + siete resonadores pasan.
Sin PCM/dispositivo/UI ni niveles normalizados; política de cola, preparación
real por API, comparación de mecanismos y evaluación humana pendientes.


R05 render por bloques: Render prepara excitación sparse y genera voces,
suma cruda y norma interna en memoria limitada al bloque (16–8192). Reloj
segment_frames=ceil(duración·sr), tail_frames=ceil(tail_s·sr), eventos siempre
ceil, fuera del crop no pasan a cola. Policies ring(default) vs reset
configurables: reset en timestamps de invalid/gap detectado, no onset físico
inferido; puede ser discontinuo y no declara ausencia de clicks. Manifest
de preparación conserva clocks/settings/events/resets/procedencia/límites.
Indices sparse por bisección evitan revisar todos los eventos por bloque.
Trece tests render/excitación/kernel pasan; tres de render repetidos tras
optimizar índice mantienen igualdad exacta al partir bloques y reejecutar.
Cola sin nuevas observaciones, ring/reset y silencio/crop exacto verificados.
Sin WAV/PCM persistido, worker/API/UI/comparador/niveles ni aceptación humana.
No se integra al Shaper aceptado ni abre dispositivos.


R05 — persistencia PCM experimental (2026-09-30): sum.wav y voices.wav DOUBLE
por bloques, entradas congeladas, hashes de código/entorno/PCM, manifest final
complete sólo tras verificar entradas y cantidad de muestras; fallos quedan
failed sin output_hashes. Peak/RMS/full-scale explícitos sin normalización.
16 tests R05 pasan; 3 de persistencia repetidos tras completar hashes de código.
Roundtrip/suma exactos, repetibilidad y partición 256/317 con hashes WAV iguales,
no sobrescritura y alteración de entrada verificadas. CLI y límites en
research/laboratory/r05_resonators/README.md. Worker/API/UI/comparación de
mecanismos, recuperación tras kill y aceptación humana siguen pendientes.
No cambia Shaper/live ni abre dispositivos; datos corporales permanecen locales.


R05 — verificador read-only (2026-09-30): `resonator_artifacts.verify(folder)`
requiere manifest complete, inventario exacto, archivos regulares sin symlinks,
hashes antes/después, preparación consistente con entradas congeladas, WAV DOUBLE
con sr/canales/duración exactos, PCM finito y suma de todas las voces exacta.
Recalcula niveles por bloques; tolerancia RMS 1e-12 relativa/1e-15 absoluta por
agrupamiento flotante, pico/conteos exactos. No rerenderiza osciladores ni demuestra
que una falsificación coherente sea auténtica: integridad local sin firma, no
custodia ni evidencia científica. Preparación se comprueba con código instalado;
compatibilidad histórica entre versiones no garantizada.
CLI: `PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.resonator_artifacts /ruta/local/corrida`.
24 tests R05 pasan, incluidos 8 de verificación: read-only sin cambios, hash,
symlink, manifest no terminado, WAV truncado con hash actualizado, suma alterada
con hash actualizado, niveles y preparación inconsistentes. Worker/API/UI,
recuperación de corridas interrumpidas y comparación de mecanismos pendientes.
Sin cambios a audio live/defaults ni aceptación humana.


R05 — worker/service (2026-09-30): `ResonatorService` inventario separado r05,
misma propiedad/cancelación/close/admisión por instancia R03/R04. Valida y congela
settings antes de encolar; worker one-shot bajo flock, manifest running, render
interno y verificación integral antes de promover WAV/manifest complete. Rehash
de entradas exteriores, hashes worker/verificador. Descargas de entradas o PCM
requieren verificación de todo el resultado; manifest disponible para diagnóstico.
No descarga completa de cancelados; no cancela procesos ajenos/restaurados.
Tres tests propios con procesos reales: completa/restaura/verifica/tamper y no
sobrescritura; render largo cancelado con process.wait confirmado, segunda
corrida rechazada mientras activo, cierre impide nuevos trabajos; contrato inválido
no encola. 27 tests R05 pasan. Sin procesos de prueba vivos al terminar.
Pendientes: endpoints/API/UI/presets, pruebas de interrupción abrupta y carreras
específicas R05, comparación de mecanismos, soporte común y aceptación humana.
No rutas web habilitadas aún, no dispositivos ni cambios al Shaper/live/defaults.


R05 — API y selección replay verificada (2026-09-30): GET/POST /api/research/r05,
POST {id}/cancel y GET {id}/artifacts/{name}. POST selección explícita
{evaluation_id,run_index,signal_id,start_s,end_s}, objetos resonators/excitation/render;
los umbrales/refractario/gap derivan exclusivamente de excitation. Reusa
candidate_snapshot sobre comparador congelado: hashes, persona, unidad, lookahead
cero, timestamps y holds duplicados verificados; sin recalcular tracking ni
trasladar calibración. Lifespan cierra únicamente workers propios.
Integración TestClient con evaluación/pose sintética real (sin mock del reader)
y dos workers: PCM descargado idéntico, 15200 muestras (1.8s+0.1s a 8k), persona
congelada, deduplicación, restore y descargas verificadas. Replay alterado no encola;
PCM alterado invalida toda descarga de resultado; contratos inválidos/ausencia
biblioteca y artefactos no permitidos rechazados. No evidencia corporal humana.
17 tests integración/persistencia/verificador/regresión R03/R04 pasan.
La corrida HTTP detectó timestamp wall-clock en chunk PEAK libsndfile: se fija
ese timestamp a cero antes de hashes, conservando peaks/posiciones y PCM. No usa
APIs privadas ni altera reloj de fuente; RIFF WAV limitado al contrato actual.
Pendientes UI/presets, prueba navegador/red real R05, comparación de mecanismos,
carreras/interrupción abrupta y escucha humana. Audio live/defaults intactos.


R05 — controles web y configuración portable inicial (2026-09-30):
ResonatorPanel en ResearchPanel: elegir comparación terminada/corrida/señal/
segmento con persona/calibración congeladas visibles; todos los campos de
resonators/excitation/render configurables, listas/matriz como JSON, scalar
numérico y modos/topologías por select. Inicio explícito con validación server,
inventario/poll/cancel/descargas y niveles. No reproducción automática de PCM.
POST /api/research/r05/configuration valida preset schema1 sin selección,
fuente/persona/calibración/segmento ni jobs; defaults seis voces. Export/import
JSON preserva selección de origen y no ejecuta. Arrays malformed no encolan.
Build TypeScript/Vite pasa; tres tests API pasan incluyendo integración con
reader real y preset roundtrip/rechazo de source/version/pesos/grafo inválidos.
Interacción navegador R05 todavía no probada: próximo paso harness aislado y
red real; no afirmar aceptación/escucha humana. Comparación de mecanismos,
figura sincronizada para esta variante experimental y experiencias pendientes.
Defaults live/sonido aceptado intactos; controles R05 son offline separados.


R05 — navegador/red real (2026-09-30): harness aislado r05_harness, Chrome
headless contra Uvicorn create_app sobre evaluación/pose sintética congelada;
fetch/endpoints/reader y dos workers reales, sin mocks de API, audio ni cámaras.
resonatorNetwork.spec.ts pasa: configuración seis voces export/import server,
selección señal/persona/segmento conservada al importar (sin jobs), dos corridas
14400 muestras a 8k/1.7s+0.1tail, PCM descargado byte-idéntico, descarga browser
sum.wav terminada sin error. Los primeros intentos corrigieron sólo expectativas
de selector accesible y decimal .3/0.3; no se cambió producto para hacer pasar.
Servidor propio cerrado; no se tocaron servicios del usuario. No prueba de
main/WebSocket/R24 ni escucha/experiencia humana. Pendientes campos extremos/
grafos/contratos inválidos desde browser, carreras/interrupción abrupta, comparación
de mecanismos y figura experimental sincronizada. Audio live/defaults intactos.


R05 — brazo experimental de mapeo de amplitud (2026-09-30): parameter_render
usa la misma selección single-signal, unidad y clocks que resonadores. Mapea
max(0,value)/reference_scale × gain, limitado por max_amplitude, a 6–32
portadoras f1×ratios/pesos explícitos. Attack/release one-pole por muestra,
max_hold_s explícito; expire/missing/crop liberan amplitud. Ceil a muestras no
anticipa observaciones; fases de portadoras continuas por reloj de muestras,
sin reataques al actualizar valor sostenido ni fase corporal inferida. Tail
es liberación del instrumento, no actividad corporal medida.
Exige carriers isolated/coupling0; damping_per_s y missing_policy heredados se
registran explícitamente como no usados. No es núcleo Shaper aceptado ni claim
paridad con live. Sin normalización/limitador/audio dispositivo. Tres tests pasan:
carrier/suma analítica, held/expiry/missing, partición y repetición exactas,
prefijo causal, cola/negativos/contratos. Settings mapping declarados: escala,
gain, max_amplitude, attack/release, max_hold y pesos. Pendientes comparación
persistida de ambos brazos sobre input común, niveles/latencias, UI de este
brazo y evaluación humana. No da por resuelta organización vs instrumento.


R05 — comparación pareada de mecanismos inicial (2026-09-30):
mechanism_compare.compare prepara resonadores excitados y mapeo de amplitud
sobre el mismo documento/clock/sr/f1/ratios/tail; mapeo declara carriers
isolated/coupling0 aunque resonador pueda acoplar. Procesa bloques compartidos,
sin acumular PCM completo. Métricas frames/peak/RMS/full-scale por brazo y
segmento/common_observed/unsupported_segment/tail; diferencia PCM sólo común.
Soporte común: intervalos entre filas válidas adyacentes con gap <= mínimo de
excitation.max_gap_s/mapping.max_hold_s, cuantización ceil, sin cubrir faltantes,
gaps, última observación aislada ni extrapolar. Soporte vacío => None, no cero.
Ganancia sugerida para igual RMS común es diagnóstico, no aplicada; no equivale
a loudness perceptual. Detector/envelope tienen latencias distintas registradas,
no declaración automática de equivalencia. Fases acústicas ≠ fase corporal.
Seis tests comparator/mapping pasan: soporte fragmentado, colas separadas,
actividad sin soporte no convierte undefined en coincidencia, repetición exacta
a misma partición y métricas equivalentes en 256/317 con tolerancia flotante.
No inferencia eficacia/HIT/agencia ni aceptación humana. Pendiente persistencia
pareada/worker/API/UI/niveles/latencias para recorrido humano. Sonido live intacto.


R05 — persistencia comparación pareada (2026-09-30): mechanism_run.run
congela input/request, renderiza informe y guarda excited/ y mapped/ con WAV
DOUBLE suma/voces vía escritor común. Manifest padre complete sólo tras ambos
brazos verificados y rehash; clocks/canales/sr exactos compartidos. Fallo de
segundo brazo deja padre failed, no resultado completo. Verificador padre
requiere hashes de informe/manifests/entradas, reconstruye preparación desde
request, verifica ambos PCM y misma entrada congelada. No prueba de custodia
firmada; informe y persistencia usan traversals deterministas separados.
17 tests persistencia/verificador/service pasan tras refactor de writer; tres
pareados repetidos tras endurecer verificación parent request. Report bytes y
PCM hashes de ambos brazos idénticos entre repeticiones, mapping roundtrip
exacto, fallo segundo brazo/tamper/no carpeta en contrato inválido probados.
Métricas/niveles crudos; sin ajuste loudness ni aceptación humana. Pendientes
worker/API/UI de comparación pareada (API R05 actual sigue corrida resonador),
latencias/escucha/figura experimental. Audio live/defaults intactos.


R05 — comparación pareada worker/API/UI (2026-09-30): request/config opcional
mapping habilita mecanismo pareado explícito; ausente conserva corrida anterior.
Servicio valida/prepara ambos antes de encolar; mismo worker/lock/propiedad/cancel,
verificación del padre y brazos antes de promover carpetas/result/manifiesto.
Descargas whitelist alias excited-sum/voices.wav y mapped-sum/voices.wav,
result.json e inputs; verifica comparación integral en cualquier descarga completa.
Panel checkbox habilita mapping configurable/preset portable, tabla regiones/
muestras/RMS/pico, identidad congelada y ganancia diagnóstica no aplicada.
Diez tests API/service/persistencia pasan con dos workflows y restore/tamper;
cuatro API repetidos tras preset opcional. Build TypeScript/Vite pasa. Prueba
navegador de variante pareada todavía pendiente; anterior sólo resonador verificada.
No PCM automático en navegador, sin loudness matching perceptual ni escucha
humana. Pendientes red real pareada, interrupción abrupta/carreras, sincronización
figura y modalidades transposición/audificación/más controles. Sonido live intacto.


R05 — Chrome HTTP pareado y corrección selección (2026-09-30): dos tests
resonatorNetwork.spec.ts pasan contra servidor/reader/4 workers reales con
biblioteca de pose sintética. Preset portable conserva fuente/señal/segmento,
variante mapping explícita, tabla de ambos mecanismos sobre soporte común,
dos pares de WAV byte-idénticos y descarga browser efectiva sin error. Build
TypeScript/Vite pasa. El intento inicial reveló carrera de efecto pasivo: reset
posterior a cargar report podía borrar señal recién elegida. resetSelection
ahora ocurre junto con report/cambio de corrida, antes de exponer catálogo;
ambos recorridos repetidos pasan. No se relajó la exigencia de conservar señal.
Servidor propio terminado (PID 411110), ningún servicio del usuario tocado.
No main/WebSocket/audio físico ni escucha humana. Pendientes carreras/kill,
campos extremos browser, modalidades adicionales/figura experimental y protocolo
perceptual con niveles/latencias medidos; roadmap no completado.


R05 — auditoría de interrupción/commit (2026-09-30): once tests específicos
worker pasan para resonador y comparación pareada. Mutaciones request/input
symlink/PCM/manifest symlink tras cálculo interno rechazan commit público,
failed sin output/hash de brazos. Dos procesos reales bajo lock calculan
resultados internos completos y se matan antes de promover; restore conserva
inputs y hash PCM interno, marca padre interrupted, no descarga/no autorelaunch.
Writer duplicado con lock tomado rechazado; lifecycle tests cierran hijos.
Suite R05 conjunta (kernel/excitación/render/PCM/verificador/service/mapping/
comparación/persistencia/worker/API): 51 tests pasan. Alcance sólo fallos probados,
no garantía general de crash-safety/transacciones FS; interrupción a mitad de
promoción aún pendiente. Sin procesos de prueba vivos ni cambios al audio live.
Escucha/percepción, figura experimental y modalidades adicionales pendientes.


R05 — estado complejo para proyección fiel (2026-09-30): kernel y render
exponen quadrature por voz (real(z)) junto a salida audible imag(z), mismo
sample clock; mapeo expone cosine × envelope × weight junto al sine audible.
Writer compartido persiste quadrature.wav DOUBLE multicanal, hashes/header/
finiteza verificados y worker lo promueve. API whitelist admite quadrature y
aliases por brazo; no sirve archivos ausentes del inventario firmado por hashes.
Verificador conserva compatibilidad con inventario anterior de dos WAV; no
crea cuadratura retrospectiva ni la infiere del audio. No nueva ruta al Shaper.
35 tests regresión kernel/mapping/persistencia/worker pasan y dos nuevos prueban
coseno/decaimiento analítico, partición exacta, persistencia/clock/legacy/tamper.
Seis API+quadrature pasan tras endurecer inventario de descargas. Componente real
es estado del modelo, no fase corporal ni medio cimático físico. No modifica PCM
sum/voices ni ratios; próxima entrega proyección/recorrido web sincronizado usando
estas componentes, sin extrapolar carriers acoplados como frecuencias aisladas.
Escucha/aceptación humana y modalidades adicionales siguen pendientes.


R05 — proyección exacta de todas las voces/API inicial (2026-09-30):
model_projection.project y POST /api/research/r05/{id}/projection requieren
corrida completa verificada, brazo single/excited/mapped, start_sample, points
2–4096 y stride1–32; lectura acotada <=131041 frames. X suma quadrature y Y
suma voices; pesos/default1 y phase offsets/default0 por todas las voces,
scale_x/y explícitos sin normalización. No extrapola portadoras acopladas ni
estima Hilbert; usa componentes guardadas de estado efectivo. Respuesta conserva
indices, reloj right-edge (sample+1)/sr, time fuente, región tail y hashes.
Stride es decimación visual sin antialias, no conversión de audio. Fase modelo
no corporal ni cymatic físico. Verificación integral por llamada puede ser
costosa: NO recorrido low-latency/realtime todavía, requiere optimización/UI.
12 tests API/proyección pasan: sumas exactas con acoplamiento, rotación/pesos/
escalas/crop/tail, clocks, bounds/NaN/brazo incompatible rechazados y endpoints
ambos workflows; ocho proyección repetidos tras límites 6–32 arrays. Primer
intento corrigió nombre reservado pytest, sin relajar contratos. Audio intacto.
Pendiente lector eficiente/preview sincronizado/UI/presets de proyección y
aceptación humana, además de modalidades restantes del protocolo.


R05 — lector acotado y caché de verificación (2026-09-30): ProjectionReader
por servicio, LRU máximo8 entradas, verifica hashes/PCM/preparación una vez
antes de primer acceso y compara fingerprint lstat de directorios/archivos
(inode/dev/mode/size/mtime_ns/ctime_ns) antes/después de cada ventana. Incluye
ambos brazos/informe en comparación, no sólo brazo mostrado. Cualquier cambio
invalida/reverifica; symlink/faltante/cambio durante read rechaza y descarta.
No persiste caché entre sesiones ni presume firma/custodia; semántica FS normal,
no defensa contra atacante que controle kernel. API usa lector; módulo project
sin lector conserva verificación íntegra por llamada. Modo expuesto en respuesta.
16 tests reader/proyección/API pasan: verificación invocada una vez por ventanas
repetidas single/paired, reescritura igual con mtime restaurado invalida por ctime,
tamper del otro brazo también invalida, cambio durante read/symlink/capacidad/
close. No render/retracking ni copias de video. Ventanas bounded PCM; latencia
UI y sincronía física aún no medidas. Próximo UI/player/presets de proyección;
audio live/defaults intactos y aceptación humana pendiente.


R05 — inspección manual figura web/preset (2026-09-30): ModelProjectionPanel
por corrida completa y brazo explícito; start_sample, points/stride, weights/
phase_offsets JSON y scale_x/y configurables. Canvas traza puntos efectivos de
todas las voces, sin extrapolar frecuencias acopladas ni normalizar escala.
Resultado declara indices/reloj/tail/verificación. Preset separado schema1 vía
POST projection/configuration conserva settings pero excluye corrida/persona/
calibración/muestra inicial; import no lee ventana ni reproduce. Brazo incompatible
rechazado; respuestas de ventana obsoletas al cambiar brazo/import/unmount se
descartan. Seguir audio todavía NO implementado; inspección manual únicamente.
TypeScript/Vite build y 12 proyección/API pasan, test portable API repetido con
rechazo source/start_sample/weights/version inválidos y sin encolar. Navegador
para este nuevo panel pendiente; no afirmar aceptación humana ni sincronía física.
Defaults/audio live intactos. Próximos: Chrome canvas/presets y player/clock.


R05 — Chrome proyección manual real (2026-09-30): dos recorridos existentes
resonador/pareado ahora incluyen ModelProjectionPanel contra API/reader reales:
preset de escala export/import conserva muestra400 y source/job, listas/defaults
sin sample en preset; selección mapped explícita en par, lectura512 puntos de
seis voces con índices400..911/verificación cacheada, canvas visible y tinta
comprobada cuando datos no silenciosos. Ambos tests pasan; repetición WAV previa
sigue byte-idéntica. Fixture pose sintética, no video/escucha humana.
Servidor propio cerrado (PID de sesión 52997); no servicios/hardware usuario.
No afirmar seguimiento de audio ni sincronía física: próximo player/reloj de
reproducción y control de respuestas obsoletas durante seeks. Modalidades
restantes, niveles/latencias/percepción y investigación formal pendientes.


R05 — vista escucha compatible y seek (2026-09-30): Chrome actual rechazó
WAV DOUBLE con DEMUXER_ERROR_NO_SUPPORTED_STREAMS (diagnóstico sin play).
GET /api/research/r05/{id}/listen/{single|excited|mapped}?gain=1 verifica fuente
y sirve vista WAV IEEE FLOAT32 generada por bloques4096; raw DOUBLE original
permanece intacto/no copias persistidas. Ganancia0–10 explícita, sin normalización
ni limiter. Cabeceras declaran conversión, gain y no-store; ranges bytes simples,
suffix/open-ended/416 permiten seeks. Metadatos fuente controlados al transmitir.
Seis tests preview/API pasan: roundtrip exacto del casteo f64×gain→f32, ranges
incluyendo límites no alineados a muestra, full-scale>1 intacto, original sin
cambios y endpoints reales. Chrome contra API/worker real decode duration1.9s,
seek0.5s y paused true pasa sin ejecutar play, con fixture pose sintética.
Servidor propio cerrado. Esto es decodificación/seek, NO escucha/aceptación ni
sincronía física. Próximo integrar audio controls y reloj al panel de figura;
audio live/defaults/R24 intactos. No considerar vista float32 PCM científico exacto.


R05 — player/clock UI inicial (2026-09-30): ModelProjectionPanel carga vista
float32 sólo por botón, audio controls sin autoplay; brazo/ganancia/import detienen
vista y descartan carga/ventanas obsoletas. Config playback portable opcional
follow_audio(defaulttrue), refresh_hz10 (1–30), preview_gain1 (0–10), loopfalse;
import viejo sin playback conserva compatibilidad por defaults. Figura sigue
ventana trailing de PCM ya reproducido: floor(currentTime×sr), no puntos futuros,
crop exacto/end/stride. Máximo una petición automática en vuelo; generación
invalida seeks/loops/settings/unmount, tick coalescea al reloj vigente. Metadata
incluye total_frames; errores de lectura pausan escucha/limpian figura. Inspección
manual se conserva. Posición/muestra/fuente no forman parte del preset.
Build TypeScript/Vite pasa (repetido tras guard de carga obsoleta), dos tests reloj
validan inicio/fin/stride/seeks/no futuro y 12 API/proyección pasan incluyendo
preset playback/validación. NO reproducción continua Chrome verificada todavía:
siguiente prueba muted contra servidor/reader reales para seeks/loops/pause.
Sin escucha humana, latencia física ni paridad con Shaper; audio live intacto.


R05 — reproducción Chrome y seek demorado (2026-09-30): cuatro recorridos
normales pasan contra API/reader/workers reales (resonador/pareado presets,
descargas y playback muted). Dos playback prueban metadata sin autoplay,
seek en pausa0.5s=>muestra3488, seguimiento de6 voces sin muestras posteriores
al clock pausado, cese de requests tras pausa, seek hacia atrás y loop1.85s→inicio.
Prueba adicional retiene respuesta REAL de servidor (sin datos sintéticos
inyectados) y hace segundo seek pausado: inicialmente falló en ambos brazos;
respuesta vieja era descartada pero nueva ventana no se solicitaba por inFlight.
pendingFollow ahora coalescea el pedido al liberar slot; dos playback demorado
repiten y pasan, muestran muestra288 para0.1s sin reaparecer ventana anterior.
TypeScript/Vite pasa; servidor propio cerrado. No escucha humana ni timing físico
medido; muted reproducción software no es aceptación. Próximos protocolo/niveles/
latencias, video de origen en este recorrido y modalidades restantes. Live intacto.


R05 — vínculo verificado al video original (2026-10-01): source_binding
resuelve sólo vía evaluación/run congelados, comparando request/preset/trace/code,
source/persona y source_record completos; valida crop seleccionado, artefacto
trace y hash del medio original. API GET /r05/{id}/source-info y /source sólo
para R05 completo y biblioteca disponible, reusa lectores verificados existentes.
Devuelve info sin ruta local, mantiene escala/procedencia y crop R05 (puede ser
subsegmento de evaluación). FileResponse abre archivo original, no copia ni
retracking/identidad inferida/calibración trasladada.
Cuatro tests API pasan para single/paired con entrega de bytes originales de
fixture; nueve source-binding prueban ruta exacta/crop, siete campos de procedencia
alterados y media/trace cambiados rechazados. Fixture es bytes sintéticos, no
video decodificable ni prueba humana. No cambia runtime/library actual ni audio.
Pendiente UI video+clock/crop/tail/offset y Chrome con video sintético válido;
sincronía física/escucha/modos adicionales e investigación formal siguen abiertas.

## Seguimiento de video: epoch consumido al solicitar seek — 2026-10-01

Incorporada la corrección publicada en PR #39, commit 370d16d: el seguidor
consume el epoch al solicitar un seek asíncrono. La prueba nueva mantiene
`seeking=true` hasta el evento `seeked`, avanza el reloj del servidor y verifica
que no se repita el seek por el mismo epoch. Tres pruebas del seguidor y build
TypeScript/Vite pasan en el workspace de desarrollo. No prueba sincronización
física ni confirma todavía el recorrido de Nicolás con video/persona.

Nota de ejecución: el primer intento de aplicar el patch completo se rechazó
porque desarrollo contiene un test adicional del decoder; no cambió los archivos
de código. Se aplicó después sólo el patch del seguidor y se agregó la regresión
sin reemplazar los tests existentes. Una primera corrida sin canal de navegador
falló por falta del Chromium de Playwright. La corrida declarada arriba usó
`PLAYWRIGHT_CHANNEL=chrome` y seleccionó las tres pruebas del elemento simulado;
no ejecutó la prueba del decoder real, que requiere Vite y un MP4 sintético.

## R05: video de origen en UI — 2026-10-01

ModelProjectionPanel ofrece carga explícita de la fuente verificada por
`source-info`/`source`. El seguidor reutiliza VideoFollower y el reloj del audio;
el helper sourcePlayback suma el inicio del crop, limita al final y pausa en la
cola. Un retroceso del reloj genera nuevo epoch. No hay autoplay del audio,
retracking, copia del medio ni cambio del instrumento live.

Build TypeScript/Vite y un test Playwright del cálculo de reloj pasan: crop,
cola, pausa, retroceso e inputs temporales inválidos. Esto no verifica todavía
reproducción conjunta real de audio/video, latencia física, formato del medio
corporal ni aceptación humana. Próximo paso: fixture MP4 decodificable y prueba
HTTP/Chrome del recorrido completo. Overlay de pose y offset ajustable pendientes.

Además, 13 tests de source_binding/API R05 pasan (20.87 s), incluyendo selección
congelada y rechazo de cambios de procedencia/medio/tracking. Esas fixtures
contienen bytes de video sintéticos no decodificables; no amplían la evidencia
de reproducción audiovisual.

## R05: recorrido audiovisual HTTP/Chrome — 2026-10-01

Dos pruebas nuevas `resonatorSourceVideo.spec.ts` pasan (8.8 s), para resonadores
simples y el brazo mapped de una comparación. El harness genera una evaluación
real de pose sintética con MP4 FFmpeg testsrc2 de tres segundos; el hash del MP4
se calcula antes de escribir el cache. API y workers reales, sin respuestas
simuladas. Chrome recibe fuente original verificada, carga audio float32 muted,
verifica crop inicial, seek pausado, avance de cuadros con audio, pausa,
seek a cola con video detenido, loop con video reanudado y ocultamiento.
Build TypeScript/Vite pasa. El servidor temporal se detuvo al terminar.

No hubo reproducción en R24, medios corporales, percepción nueva ni escucha
humana. La tolerancia del test de posición es 0.05 s; no mide sincronización
física ni prueba cada estado posible de decoder/red. Overlay y offset ajustable
siguen pendientes. La primera corrida cubrió sólo single; la corrida final
incluyó single y mapped sin repetir cambios de código.

Reproducción en una raíz temporal NUEVA (no usar el state del usuario):

```bash
ffmpeg -f lavfi -i testsrc2=size=320x240:rate=30 -t 3 -c:v libx264 -pix_fmt yuv420p /tmp/r05-generated.mp4
npx --prefix laboratory-ui vite build laboratory-ui/tests/r05_harness --outDir /tmp/r05-video-ui
PYTHONPATH=src:tests:../harmonic-shaper-dev/src .venv/bin/python tests/r03_http_fixture.py --root /tmp/r05-new-session --ui /tmp/r05-video-ui --synthetic-video /tmp/r05-generated.mp4 --port 8879
# En otra terminal, desde laboratory-ui:
LAB_R05_VIDEO_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/resonatorSourceVideo.spec.ts
```

Detener el servidor propio con Ctrl+C al terminar. Sin --synthetic-video, las
fixtures anteriores conservan los bytes no decodificables de sus tests de API.

## R05: desfase visual explícito — 2026-10-01

PlaybackSettings agrega video_offset_s finito entre −10/+10 s, default cero,
portable en el preset. UI aplica el valor al reloj de video sin cambiar fuente,
PCM, features ni proyección de audio. El reloj se limita al crop y congela el
punto desplazado del final al entrar en cola (un offset negativo no hace seeks
avanzando durante la cola). Cambiar offset provoca una corrección explícita de
posición, sin reiniciar audio ni renderizar.

Cuatro tests de API pasan, con límites y rechazo de no finitos; dos tests del
reloj cubren signos, límites y cola. La primera prueba Chrome del export falló
porque el test parseaba el textarea antes de recibir la respuesta asíncrona;
se corrigió esperando un valor no vacío. Resultado final y build registrados
al finalizar la corrida. No se modifica ningún default sonoro ni se mide latencia
física/aceptación humana.

Corrida final: cuatro tests Playwright pasan (9.7 s): relojes y HTTP/Chrome
single/mapped, offsets positivos/negativos, export/import con valor persistido
sin autoplay y src de audio estable al ajustar offset. Build TypeScript/Vite
pasa. MP4 generado, API y workers reales; servidor temporal apagado.

## R05: snapshot de pose para overlay — 2026-10-01

API source-pose entrega sólo el tracking de la persona congelada y crop R05,
con ausencia explícita, estados/confianza y coordenadas/unidades/dimensiones.
Carga generación verificada, rechaza manifest/payload alterados y vuelve a
verificar hashes al terminar. No contiene rutas locales ni IDs de streams.
Índice temporal efímero; no copia video/tracking ni ejecuta inferencia.

Primera corrida: 10 tests pasan y uno falla por expectativa incorrecta de la
fixture (cuadros sin ninguna persona, no joints individuales missing). Corregido
para verificar tres filas con person_present=false y joints vacíos. La UI de
overlay y su selección por soporte/edad siguen pendientes, así como prueba visual
corporal. No se interpreta coordenada world como imagen ni pose como verdad 3D.

Corrida final: 15 tests source_binding/API pasan (24.14 s), incluyendo source-pose
para single/paired, crop exacto, filas de ausencia, clock ordenado, metadatos de
coordenadas y rechazo de payload alterado. Son datos sintéticos; no prueban UI
del overlay ni precisión de pose.

## R05: overlay visible de pose congelada — 2026-10-01

ModelProjectionPanel carga pose explícitamente y superpone joints observados y
conexiones entre joints observados sobre el video. Selección por binary search
de última fila no futura respecto del currentTime del video; edad máxima
configurable >0..5 s, default .1 s. Rechaza ausencia, fila vieja, world/unit o
3D incompatibles; oculta durante seek. Diagnóstico visible sin sustitución,
interpolación o nuevas inferencias. Checkbox y edad quedan en preset portable.

Build TypeScript/Vite, test de selección temporal (incluye backward seek y
rechazo de world) y dos recorridos HTTP/Chrome single/mapped pasan (10.5 s).
Chrome comprueba 17 joints de fixture observada, ausencia explícita sin dibujo,
gap inducido al reducir edad y ocultar/mostrar; también mantiene pruebas de
video/audio/offset/export/import. Generación MP4 y pose sintéticas, API/worker
reales. Servidor propio apagado. No implica precisión corporal, latencia física,
escucha ni aceptación humana. Matriz de estado actualizada; modalidades R05
restantes y pruebas físicas/humanas siguen pendientes.

Cuatro tests API pasan (9.14 s), incluyendo defaults normalizados, rechazo de
edad cero/negativa/no finita/fuera de rango y conservación de checkbox/edad.

## R05: interrupciones durante promoción — 2026-10-01

Worker reverifica inputs y salidas después de mover los archivos/directorios a
su destino y antes de publicar manifest completo. En paired verifica otra vez
cada brazo y sus manifests; en single compara todos los PCM contra hashes ya
verificados antes de moverlos. Rechaza destinos existentes en vez de sobrescribir.
La publicación completa sigue siendo un único manifest atómico; mover varios
archivos no es una transacción multiartefacto.

Nuevas pruebas matan un proceso real después de cada una de las tres promociones,
en single/paired (seis cortes): writer lock rechaza duplicado, estado sigue
running mientras el worker vive, restauración da interrupted sin relanzar,
proyección/descargas rechazadas y restos diagnósticos preservados. Cuatro pruebas
mutan input o PCM durante promoción y exigen failed sin inventario completo.
Dos comprueban destino existente preservado; dos inyectan OSError en segunda
promoción y comprueban estado failed con primera salida preservada. Corrida
inicial worker/service: 24 tests pasan (8.93 s); resultado final ampliado abajo.

Esto cubre muerte de proceso y errores de promoción, no caída del host/pérdida de
energía ni sistema de archivos adversarial. No se recupera/publica automáticamente
una corrida incompleta ni se elimina su evidencia. Verificación de descarga
continúa protegiendo contra cambios posteriores; no se promete una transacción
contra escritores externos concurrentes.

Corrida final ampliada: 32 tests worker/service/API pasan (17.78 s), incluyendo
nuevos destinos existentes y errores IO, servicio real, cancelación y contratos
API. No se iniciaron servicios de audio ni se usaron datos corporales.

## R05: modulación de portadoras como opción separada — 2026-10-01

parameter_render admite frequency_modulation opcional (depth/smoothing_s).
Mantiene el camino fijo por defecto y omite None del manifest/config: las
preparaciones previas sin la opción conservan su forma. El camino opcional usa
factor común normalizado/recortado y suavizado con una one-pole causal, fase
acumulada muestra a muestra sin reiniciar y la misma envolvente de amplitud.
Ratios instantáneos conservados, alias máximo validado contra Nyquist. Expiry y
missing restablecen target de frecuencia cero; su transición es instrumento.
UI checkbox + controles y botones serie f1/2/armónica; no cambia cantidad de voces.
Preset y manifests explicitan la opción; cuadratura persiste fases efectivas.

11 tests render/mecanismos pasan (1.38 s): analítico inicial, fase al reactivarse,
partición/repetición exactas, prefijo causal, contratos/alias y persistencia.
29 tests API/worker pasan (16.42 s). Chrome HTTP real agrega un recorrido que
configura depth .4/smoothing .02 + seis ratios f1/2, exporta/importa, ejecuta
worker, descarga PCM verificado y proyecta sus seis voces (4.7 s total).
Build TypeScript/Vite pasa. Servidor temporal propio apagado; medios sintéticos,
sin audio físico/escucha humana. No se mide latencia ni aceptación de esta opción.

Pendientes: audificación acelerada, transposición de relaciones temporales
corporales con estimador explícito, banco de modalidades y comparación perceptual
con niveles/latencias medidos. Esta opción no los da por implementados.

## R05 auditoría conjunta y núcleo R06 — 2026-10-01

94 tests del conjunto R05 pasan (35.17 s): núcleo/excitación/render/PCM,
verificación/worker/service/mecanismos/cuadratura/proyección/reader/preview y
API/source_binding. No es una nueva escucha ni prueba de hardware.

Se inicia rama feat/r06-activation-bank apilada sobre R05 en el mismo workspace
de desarrollo. Banco R06 sintético con cuatro calendarios sobre medio fijo,
dosis y cantidad iguales, cero inicial y métricas sobre todas las muestras.
Tres tests pasan y se ejecuta CLI con reference.json. Incluye seed, hashes y
Python/NumPy/SciPy; rechaza colisiones y exceso de trace. Durante desarrollo se
eliminó numerador racional redundante al ordenar la grilla; condición racional
usa muestra entera. No se atribuye resultado a privilegio phi/HIT. Integración
worker/API/UI/presets/verificador y banco/protocolo ampliados pendientes.

## R06: worker, service y verificador — 2026-10-01

Se agregan ActivationService/activation_worker/activation_artifacts. Request
validado antes de encolar, cálculo en proceso propio, flock y commit running→
complete sólo tras verificación/promoción/rehash. Error conserva failed sin
inventario output; restauración de proceso muerto queda interrupted sin relanzar.
Destinos existentes no se sobrescriben. Descarga valida hashes/contracts y no
sirve resultados incompletos. Verificador compara settings/reloj/dosis/calendario,
soporte de trace, inventario/tipos y finitud, con rehash final; no recalcula todas
las métricas ni prueba autenticidad frente a hashes reescritos.

Primeras dos corridas fallaron sólo en repetición inmediata: manifest complete
aparecía antes de salir el proceso. Test espera el handle real antes de lanzar
su segundo worker, conservando el límite de un proceso activo. Los otros casos
pasaron. Corrida final registra resultado abajo. Pruebas incluyen proceso real
muerto tras promoción, writer duplicado, restauración sin descarga, request
alterado y cancelación real de una corrida larga con request preservado.
No se arrancan audio, cámaras ni servicios del usuario; fixtures sintéticas.
API/UI/presets, bancos/observables HIT y protocolos físicos/humanos pendientes.

Corrida final: 13 tests R06 pasan (3.64 s): banco, verificador, worker y service.
Handles hijos propios terminados por wait/kill/cancel y servicios de test cerrados.

## R06: API y mesa web portable — 2026-10-01

API configura/inicia/lista/report/cancela y descarga artefactos verificados R06.
Lifecycle se cierra con la app. Config esquema1 normalizada y calendarios
validados antes de encolar; import no lanza. UI expone todos los parámetros del
medio y calendario/cálculo, presets JSON, jobs/cancelación, tabla de métricas y
selector/slider de trace. worker_active impide lanzar durante salida del worker
cuando manifest ya está completo. No modifica instrumento live ni requiere pose.

16 tests R06 pasan (5.89 s), incluidos tres HTTP con subprocess reales:
config/repetición/restauración/hashes, inválidos sin encolar y cancelación propia.
Build TypeScript/Vite pasa. Primer build encontró nullable inicial de settings;
se corrigió con guard explícito. Primer Chrome no encontraba topología por nombre
accesible combinado con opciones; se agregaron aria-labels explícitos.

Recorrido HTTP/Chrome final pasa (4.8 s): sample_rate8000, span/cola .1 s, seed43,
intensidad .7, bloque317/stride64, topología ring/acoplamiento2, export/import sin
run, dos workers y results byte-idénticos verificados, tabla de cuatro condiciones,
selector de trace y restauración tras reload. Harness aislado r06_harness sobre
API real sin mocks; servidor propio apagado. Fixtures sintéticas, no escucha ni
hardware ni prueba completa de todas las combinaciones de controles.

Regresión del app compartido: cuatro tests API R05 pasan (9.38 s) después de
integrar R06. No se amplía con ello evidencia de escucha o hardware.

## R06: contraste de medios con entrada idéntica — 2026-10-01

medium_controls opcional (1–4 medios) permite modificar damping/coupling/grafo,
preservando f1/ratios/sample_rate; misma ventana/eventos/dosis/cero inicial.
Default omitido por serializer para conservar formato anterior. Cada control
incluye condiciones raw y diferencias de métricas control menos base. Verificador
valida inventario/config de controles, reloj/calendarios/dosis/trace y deltas;
no rerenderiza las métricas. UI checkbox, JSON editable de medios, preset,
tabla de contraste y selector de medio para trace; no modifica sonido live.

21 tests R06 pasan (6.93 s): identidad reproduce base exacta, mismo calendario/
dosis, controles no idénticos y diferencias declaradas, incompatibles rechazados,
verificador rechaza config/calendario/delta/inventario alterados aun con hash
reescrito. API/worker/cancelación/restauración existentes pasan. Referencia CLI
anterior verificada como complete: compatibilidad de formato, no reproducción
científica entre versiones/entornos.

Chrome HTTP real final pasa (4.9 s): damping8/coupling4 sobre medio base ring2,
export/import, dos resultados byte-idénticos, cuatro filas de contraste y
selección de trace del control. Build pasa. Primera corrida Chrome no resolvía
label implícito del textarea de controles; se agregaron aria-labels explícitos
a JSON fields y se repitió sobre el mismo servidor, luego apagado.
Sin cuerpos, audio/hardware o escucha humana. Variaciones de medio son controles
de modelo, no evidencia de privilegio phi/HIT ni eficiencia fisiológica.

## R06: surrogates de intervalos — 2026-10-01

interval_shuffle bool opcional, default false/omitido, agrega permutación de
inter-event gaps por calendario mediante stream SeedSequence(seed,606,index).
Preserva multiset digital de gaps, count/dose, primero/último y reloj, sin cambiar
random original ni condicionar permutaciones a diferencia. Uniforme puede quedar
idéntico. Se aplica también a medios de control con los mismos calendarios.
No preserva espectro o estructura temporal superior; una semilla no da p-value.

Corrida inicial: 22 tests R06 pasan (6.91 s). Chrome HTTP real pasa (6.0 s):
checkbox/export/import, ocho filas de calendario/contraste de medio, dos workers
con results byte-idénticos, trace de phi_interval_shuffle y reload. Build pasa.
Servidor propio apagado; sin escucha/cuerpos/hardware. Corrida final ampliada con
verificador de surrogates y bool estricto registrada abajo.

Corrida final: 24 tests R06 pasan (7.16 s), incluidos rechazos de eventos/inventario
surrogate alterados aun con hashes reescritos y interval_shuffle no booleano.

## R06: banco de semillas congeladas — 2026-10-01

Settings agrega replicate_seeds opcional 1..8, únicas/dentro de rango/distintas
de principal, omitido por defecto. Probe valida calendarios de todas antes de
calcular. Conserva cada report con configuración/eventos/métricas/medios; resumen
poblacional descriptivo sobre principal+adicionales, por medio/calendario/métrica.
Cap agregado144000 puntos. Verificador reconstruye inventario de semillas,
valida cada report hijo y recalcula agregados desde sus métricas guardadas; no
rerenderiza esas métricas ni las convierte en contraste científico.

29 tests R06 pasan (9.39 s): semillas/repetición/constantes deterministas,
contratos/cap agregado, rechazo de seed/summary/clock hijo alterados aunque se
actualice hash, y lifecycle/API existentes. Chrome HTTP real pasa (6.8 s):
principal43/adicional44, ocho condiciones y medio de control, export/import,
dos results byte-idénticos verificados, selección semilla44 con tablas/traces
consistentes, resumen y reload. Build pasa. Servidor propio apagado.
No audio físico, cuerpos ni aceptación humana; un banco de semillas no es una
población de participantes ni distribución nula. No calcula p-values.

Referencia CLI R06 anterior sigue verificándose complete: compatibilidad de
lectura/formato sin afirmar reproducción numérica universal entre versiones.

## R06: diagnóstico de colisión en semilla adicional — 2026-10-01

Se verificó un caso real de cuantización (sr8000/span .1/count8): semilla25
colisiona en random, mientras principal17 es válida. Error ahora identifica
calendario, semilla y muestras repetidas; no fusiona impulsos ni cambia dosis.
Pruebas de API config/start exigen422 sin ningún job/carpeta y prueba de core
exige que no se instancie el kernel ni se cree output. No hay retries automáticos
que seleccionen otra semilla. Resultado de suite completa registrado abajo.
No se cambia comportamiento de calendarios válidos ni formatos/presets/sonido.

31 tests R06 pasan (8.81 s), incluidos nuevos rechazos antes de render/encolado.
No se necesitó nueva corrida Chrome para este cambio de diagnóstico de backend.


### Recorrido de aplicación completa con cache corporal — 2026-10-02

fullLaboratoryNetwork.spec.ts pasó en Chrome (14,6s total), usando bundle de
producción, FastAPI/WebSocket, LaboratoryRuntime y VideoLibrary reales en estado
local aislado. Sin route mocks ni UI ensamblada por partes. CacheCPU del minuto
existente confirmó cache_hit; sin copiar video ni recalcular tracking.

Desde UI: abrir ruta, persona por defecto, elección explícita, avance del video,
pausa/seek5s, diagnóstico de calibración requerida, medición con hombros/caderas,
aplicar08–11, seis targets afinados no nulos por modelo, guardar/recuperar preset
portable, cambio de cuerpo descarta escala incluso al volver, y seek al final con
loop conserva avance de video. Sin excepciones JavaScript. Preset guardado no
incluye source/persona/calibración. Datos/artefactos/capturas quedan locales.

Fixture usa ControlRecorder: targets reales del runtime, **sin sintetizar ni abrir
salida física**. Informa audio no disponible y no publica VoiceFrame ficticio.
No valida figura/audio live ni R24; el recorrido WAV/figura del comparador está
verificado por separado. No escucha/aceptación humana. Fixtures no abren cámara.

Se registró además el minuto en biblioteca de desarrollo (media.json), reutilizando
cache válido y backendCPU confirmado. Se corrigió sólo la preparación local, no
archivos/workspaces cotidianos. Abrir desde selector Videos de la biblioteca.
Primer intento local de registro falló por venv/checkpoint ausentes en HarMoCAP-lab;
se usó el mismo fallback al venv/modelo de HarMoCAP que contempla el launcher,
con código de HarMoCAP-lab explícito. Cache previo y configuración conservados.

### Exportación de comparación con video y figura (desarrollo)

`tests/test_lab_video_export.py` verifica fórmula de seis voces independiente,
interpolación gain/fase cropped, no figura ficticia en silencio, encoding real de
fixture sintético MKV/MP4, PCM float32 exacto al decodificar MKV, frame inventory,
worker/restart/cancelación/corrupción y API. `comparisonExportNetwork.spec.ts`
requiere LAB_AB_API_URL, LAB_AB_JOB, LAB_COMPONENT_TEST_URL y API/Vite proxy locales:
Chrome opera controles reales, guarda configuración, hace POST real, observa
finalización, descarga MP4 y verifica avance de video; no mocks del API/encoder.
Audio muted: no escucha humana. Comparador A/B anterior sigue probado aparte.

Se exportó localmente el segmento privado60s y se conserva receipt sólo bajo
laboratory-dev. No se publican video/tracking/receipts corporales. La verificación
cubre reloj lógico y fidelidad PCM MKV, no calidad perceptual ni sincronía física.

Resultado: 32 tests de export/evaluación/PCM/API pasan (14,13s); tras añadir
cancelación durante encoding y recuperación no confirmada, 6 tests del módulo
export pasan (4,93s). Chrome export con API/media reales:1test16,7s; regresión A/B
con cinco versiones reales:1test3,9s. Build TypeScript/Vite pasa. Export60s MKV
final:600frames verificados por ffprobe,2880000samples@48kHz y comparación
float32 exacta con el WAV al decodificar. Receipt local
`comparison-export-validation.json`, sin escucha humana ni sincronía física.

### R12 · Banco descriptivo de mediciones y tareas

22tests R12/neuro-regresión/API pasan (2,33s): integral y media analíticas con
ventanas recortadas, clocks afines, soporte propio/común, null/gaps/exclusiones/
colas sin rellenar, units/calibración/orden/finite, manifest/recompute/restart/
retry/corrupción/histórico y EVAL binding con rechazo hash/slot/ventanas diferentes.
Fallo antes de manifest deja staging diagnóstico y permite reintento; overflow de
inputs finitos se rechaza, no certifica Infinity. Build TypeScript/Vite pasa.

Chrome con API local real y datos sintéticos explícitos pasa: controles gap
hacen aparecer/desaparecer soporte, configuración portable se descarga, guardar
con respuesta perdida + recarga + recuperación repite idéntico request y produce
un único registro, abrir/exportar manifest funciona. API sin mocks (salvo pérdida
de respuesta inyectada después de POST aceptado). No hardware ni fisiología de
Nicolás/Annie, no escucha/percepción/sincronía física ni prueba de eficiencia/HIT.
Protocolos/datos de esta prueba aislados del store cotidiano y videos privados.

### R13 · Forecasts reservados, adaptación y controles

44tests R13/R12/evaluación/API pasan (13,02s),11específicos R13 pasan (2,17s).
Controles: cambiar objetivo test final no altera modelos/predicciones previas;
normalización/base/coefs train-only; rango completo hace coincidir ridge completo/
subespacio; gaps y reservas/embargo no se cruzan; prefix-only/pooled conservan
baselines y puntúan igual soporte, shuffle sólo en targets train; nulos sin soporte;
repeat/recompute exacto, corrupción/histórico/defaults archivados y no overwrite.
Worker propio/restart/cancel y snapshot EVAL también verificados.

Chrome API real/worker: control/config portable y repetición con hashes iguales
pasan (3,5s). Producción real sin mock de componentes: investigación no se pide al
inicio, se carga al abrir pestaña; nueve predictores/controles con prefix-only30 y
shuffle puntúan149objetivos comunes (2,9s). Regresión UI corporal:cacheCPU, slot
derecho exacto, video/pausa/seek/loop/calibración/presets cuatro modelos/seis targets
pasa (9,6s). Primer intento de esa regresión falló por pasar ID abreviado1 en lugar
de slot-1-generation-1; se corrigió entrada del test, no tracking o selección.
Fixture control_targets_only: no mide audio hardware ni escucha humana.

Comparación corporal local within_take:seis velocidades T/s, train0..25s/test30..60s,
embargo5s, historia2/H3/componentes3/z-score train;891objetivos comunes, ambos runs
recomputados y hashes de request/result/traces idénticos. Receipt sólo local
r13-body-validation.json. No transferencia entre sujetos/tareas ni beneficio/HIT
verificados. No copia/retracking de original ni medios/tracking publicados.
Build TypeScript/Vite pasa; split~292kB inicial/~215kB investigación sin aumentar
límite de warning. UI/node fixtures propios aislados, sin cambios audio live/defaults.
## Seek asíncrono del video — 2026-10-01

El seguidor consume el epoch cuando solicita el seek, sin esperar que el decoder
lo termine. Antes, con `seeking=true` y reloj de tracking avanzando, `seeked`
podía volver a buscar otra posición del mismo epoch y repetir el ciclo. El nuevo
test simula ese comportamiento asíncrono y verifica un único seek seguido de
corrección suave de velocidad. No modifica selección de persona ni tracking.

Tres pruebas Playwright del seguidor y build TypeScript/Vite pasan. Interfaz local
recompilada; servicios de Nicolás no reiniciados. La reproducción con el video
corporal y la aceptación visual siguen pendientes: estos tests usan un elemento
simulado, no prueban por sí solos el recorrido completo ni la causa única del
problema reportado.


### Integración de las entregas publicadas en main — 2026-10-02

Se integraron las 50 PRs publicadas de este desarrollo (#28–#30, #37–#76,
#78–#84), las cinco de Shaper (#2–#6) y el baseline HarMoCAP #1.
La reconciliación del follow-up #39 conserva todos los tests y añade su evidencia
a la bitácora; el código final del seguidor ya coincidía con el acumulado.

598 pruebas Python del laboratorio y research pasan (114,44 s); 19 de Shaper
(laboratorio, offline y recuperación) pasan (1,79 s). Build TypeScript/Vite pasa.
Se preservaron originales, datos locales, configuraciones y cachés; antes del
arranque se respaldó la base SQLite cotidiana. Weaver/Shaper cotidianos tienen
venvs propios con versiones de sus dependencias fijadas a las de los entornos
verificados de desarrollo. No se copió ningún video.

Arranque cotidiano confirmado en 8765/8085: Shaper 48 kHz/256 samples, R24
Analog Stereo vía JACK/PipeWire; enlaces efectivos de ambos canales a R24
verificados con pw-link. Video de archivo reabierto con cache_hit=true y selección
local restaurada. El preset recuperado requiere calibración, indicada en el
diagnóstico: no se reemplaza silenciosamente. Estas comprobaciones no acreditan
escucha, calidad perceptual ni aceptación de Nicolás/Annie.

El follow-up de Oliva #36 (2767df1) pasa 18 tests en su base y 18 al importar
Weaver actual; revisión publicada en la PR con observaciones de trazabilidad y
digest histórico no reproducido. Su código permanece separado, al igual que el
prototipo OSC todavía no publicado (#77).


### Contrato OSC opt-in por slot (#77) — 2026-10-02

Se implementa ObservationEvent v2 con captura/recepción en dominios separados,
IDs originales y canales exclusivamente del slot actualizado. Estados held y
invalid no generan muestras observadas en el consumidor de referencia.
Tombstone/expiración conservan watermark; cambios de stream/contrato/calibración
invalidan historia. Metadata malformada, varios slots en un único payload, NaN
y versiones/relojes falsamente etiquetados se rechazan. Payload inválido no
reemplaza el estado ni envenena la secuencia aceptada. Streams retirados se
recuerdan hasta 64 por sesión, límite declarado.

29 pruebas seleccionadas de driver/consumidor, engine y pads E2E pasan (69,06 s).
Tras añadir la regresión de captura tardía que no reemplaza la base de derivada,
21 pruebas específicas del driver pasan (0,93 s). Export JSON de eventos preserva
IDs, clocks y causas de invalidación. La interfaz legacy continúa siendo el
default de los launchers y el laboratorio cotidiano no se reinicia ni modifica.

OSC_OBSERVATIONS documenta compatibilidad y adopción pendiente: ingreso parcial
al motor/launchers, identidad de su contrato instalado frente al del productor y
traza de ambos relojes sin confundirlos con el reloj operativo del engine.
No se declara #77 completa. Fixtures sintéticos; sin datos privados, sincronía
física ni escucha/aceptación humana acreditadas.


### Ingreso OSC parcial en engine y launcher opt-in — 2026-10-02

El engine incorpora ingest_driver_observation: valida todos los canales del slot
contra su manifest instalado, mantiene gates/rangos y conserva watermark e IDs
del productor separados de stream/contrato/secuencia internos del adapter.
Los envelopes y snapshots explicitan los relojes; held/invalid no renuevan una
captura válida. Las trazas conservan el evento completo y el reloj operativo del
engine aparte. Recibir otro slot o un tick no remuestrea inputs utilizables; las
transiciones de salida pueden avanzar sin recalcular historia corporal.
Cambiar identidad/calibración reinicia la historia de derivada/fase/peaks incluso
si se perdió la invalidación previa. El launcher de rehearsal acepta
--harmocap-events v2; legacy sigue siendo default y se registra en run_config.

86 tests seleccionados engine/transforms/pads E2E/driver pasan (66,29 s).
27 de engine/derivadas/harness pasan tras el cambio final de etiquetas de reloj
(1,82 s). La integración con dos personas usa bundles OSC reales sintéticos,
tanto en modo legacy como v2; demuestra la diferencia de resampling y la
expiración sin renovar captura. No hardware ni escucha en esa prueba.
El laboratorio cotidiano sigue en main, sin reinicio/cambio de preset, y su
API confirma audio running a 48 kHz. No se infiere aceptación humana.

Pendiente explícito: selección del reloj de captura para transforms temporales
genéricos, compatibilidad entre múltiples inputs/derivados y resets por gaps.
Por ahora esos transforms conservan su reloj operativo; el consumidor research
SlotObservationHistory usa el reloj productor. El opt-in no certifica velocidades
físicas ni equivalencia científica del replay histórico. #77 permanece abierta.

## OSC v2: reloj de captura para derivadas — 2026-10-02

Opt-in derivative.clock=source_capture con identidad por cuadro, alineación de
inputs, warming por gap/epoch y diagnóstico en snapshot/Stage. Engine permanece
default; seis voces, ratios, fases y presets aceptados no se modifican.

83 pruebas pasan (1.51 s): captura, ingreso parcial, registry/derived scenes,
panic, transforms temporales/radiales y Patchbay registry. Incluyen dos slots
del mismo cuadro, entrega parcial desalineada, posterior alineación y vencimiento
del hold sin nuevas parejas. Chrome Stage/API real: guardar source_capture, gap
350 ms, recargar, recuperar configuración y regresar a engine; 1 test pasa
(1.9 s). node --check y git diff --check pasan. Fixture aislado puerto 8897
apagado al terminar; no reinicio del laboratorio cotidiano ni escucha nueva.

Pendientes: metadata de captura por aggregators, relojes de los demás transforms
y evidencia de sincronía física. No se afirma velocidad métrica ni validación HIT.

## OSC v2: procedencia de captura en señales derivadas — 2026-10-02

Aggregators transmiten frame/identidad/timestamp del productor únicamente para
inputs completos observed alineados, incluyendo predicados. Cadenas y bin_2d
conservan procedencia; fixed_hz no inventa un sample nuevo para la derivada.
Combinar frames, relojes o cohortes parciales mantiene el cálculo numérico legacy
sin afirmar una captura común. No cambia configuración/defaults de audio.

91 pruebas pasan (1.52 s), incluidas ocho nuevas de aggregators: cadena→derivada,
repetición fixed_hz, frames/streams/timestamps distintos, held/legacy, predicados
y subconjunto seleccionado; motor con dos personas entregadas por separado,
alineación posterior y tick repetido. git diff --check pasa. Sin hardware/medios
privados ni escucha nueva. Pendientes: otros transforms y sincronía entre
productores; no se afirma equivalencia científica ni velocidad métrica.

## R11: archivo recuperable de controles SNR — 2026-10-02

SNRService publica request/result/manifest por staging; identidad de configuración
permite retry/restart sin duplicados. API/listado/artifacts y controles web de
guardado/reapertura, pendiente congelado sessionStorage y recuperación explícita.
Procedencia de módulos importados/entorno separada de equivalencia numérica:
estructura/support/config exactos, floats rel/abs1e-12; flags de implementación/
entorno distintos no bloquean recomputación equivalente. integrity_only no se
presenta como recomputación. No adquiere hardware ni altera audio/defaults.

18 tests R11 núcleo/raw/SNR/runner/API pasan (1.46 s; deprecación AnyIO sin fallo).
Cinco del archivo pasan tras precisar hashes de módulos importados (0.23 s).
Chrome UI/API real: POST aceptado/respuesta perdida, reload/retry idéntico, registro
único y reapertura restaura amplitud/resultados/config (1 test,2.2 s). Build
TypeScript/Vite pasa. Fixture aislado8898 detenido; laboratorio cotidiano intacto.
Sólo componentes sintéticos conocidos, no EEG, SNR físico ni escucha humana.
Dependencias de hardware/formatos reales/sync física permanecen en README R11/#25.

## R11: importación CSV declarada — 2026-10-02

Contrato/API/UI con metadata y mapeo explícitos, selección de columnas/delimitador/
preamble/unidad temporal/tokens faltantes; export de mapping/procedencia y entrega
al guardado nativo. Conserva amplitudes/unidades/cero/null/gaps y digest UTF-8;
no unwrapping de contadores, inferencia de placa, filtrado ni escala automática.
Archivo original y mapeo no se archivan con Stream; límite documentado en README.

17 tests import/API pasan (1.48 s; warning AnyIO sin fallo) tras limitar expansión
a16MiB; 13 controles importer pasan (0.24 s) incluyendo prueba adicional de
expansión por64 canales faltantes. Build TypeScript/Vite pasa. Chrome UI/API real
(1 test,2.1 s) verifica BOM+CRLF→hash exacto,0/null/.008, export de mapping en
procedencia, convertir→guardar→reabrir y rechazo NaN sin resultado viejo. Fixture
aislado8899 detenido; datos sintéticos, sin audio/hardware ni cambios cotidianos.
No se certifica un formato OpenBCI real, acquisition clock físico ni EEG/SNR.

## R06: controles explícitos de fase de excitación — 2026-10-02

Extensión opt-in del render experimental para rotar impulsos complejos por voz,
con cero inicial, eventos/magnitudes/L2/portadoras/medio preservados. phase_controls
cruza medios/semillas/surrogates, añade tablas/deltas y resumen por fase; UI/presets/
verificador conservan compatibilidad con campo omitido. No fase corporal inferida.

48 tests R06/resonadores/render/API pasan (7.87s; deprecación AnyIO sin fallo).
Siete nuevos: cero exacto, norma aislada invariante y mezcla diferente, particiones,
cruces/resúmenes, vector inválido/budget y corrupción de fases/dosis/deltas aun con
hash rehecho. Chrome API/UI/worker real: dos resultados byte-idénticos, preset
export/import sin corrida implícita, tabla/trace por fase/medio/semilla (5.8s).
Build pasa. Fixture8900 detenido; no audio/hardware/medios privados ni escucha nueva.
Fases acopladas pueden cambiar norma interna; no es energía física. Espectro,
hipótesis HIT específica y protocolo físico/humano permanecen pendientes.

## R06: sondas espectrales opcionales — 2026-10-03

Coeficiente Fourier medio rectangular de indicador unitario de eventos y mezcla
sobre todas las muestras, con frecuencias/ventana configurables. Clocks antes/
después del paso declarados, soporte exacto y memoria por bloques; budget agregado
incluye fases/medios/semillas. No PSD, watts, suma de energía ni transferencia.
Campo omitido preserva formato; habilitar conserva métricas/audio/trace anteriores.

58 tests R06/resonadores/render/API pasan (8.05s; AnyIO deprecación sin fallo).
Incluyen diez de sondas: DC/seno conocidos, ventanas/particiones, cruces, frecuencia/
soporte/coherencia alterados rechazados, gaps/duplicados/no finitos y budgets.
Chrome UI/API/workers: dos resultados byte-idénticos, preset y tabla espectral
siguen fase/medio/semilla sobre800 muestras de cola (1test,5.9s). Build pasa.
CLI reference_spectral.json ejecutado y verify pasa; números descriptivos en README.
Fixture8901 detenido; no hardware/audio cotidiano/medios privados ni escucha nueva.
No control de espectro igualado ni validación HIT; dependencias permanecen explícitas.

## R07: lectura histórica y recálculo explícito — 2026-10-03

Las lecturas del banco transiente comprueban integridad, binding del request y
soporte sin rerender. La API/UI informa código/entorno coincidente o distinto y
ofrece recálculo separado; compara estructura exacta y floats con rel1e-12/abs1e-15.
El recálculo no sobrescribe el registro y sigue rechazando diferencias numéricas.

23 tests de membrana/núcleo de controles/runner/servicio/API pasan (3.93s).
La prueba API ampliada pasa (1.51s): lectura y recálculo diferenciados, resultado
sin sobrescritura. Build TypeScript/Vite pasa. Chrome HTTP real verifica lectura
de procedencia histórica simulada, recálculo y conservación de bytes de resultado
y manifest (1 test). Fixture aislado8902; datos sintéticos, sin hardware ni audio.
Recuperación de atributos reservados y ensayo físico/humano siguen pendientes.

## R07: decodificación de atributos reservados — 2026-10-03

Dataset de figuras RMS verificadas de PCM R05, separado de etiquetas del decoder.
Reservas temporal/toma/grupo, embargo y detección de PCM/ventana repetidos. Mismo
medio/grilla; modelos full/shape/magnitude, media train y controles label-shuffle
comparten soporte test. Normalización/coefs train-only, MSE por atributo/unidad².
API/UI/preset portable, snapshots sin copiar PCM, staging, reapertura/recompute.

63 pruebas pertinentes R07/backend/API pasan (8.90s). Tras precisar binding de
etiquetas/inventarios y origen temporal de PCM distintos,20 pruebas del nuevo
núcleo/archivo/API pasan (1.86s), incluyendo rehash de target alterado. Cubren confusión con magnitud,
atributo espacial a magnitud constante, zero/multiatributo, train-only, reservas,
integridad/tolerancias/repetición y reapertura aun sin fuentes originales.
Entre renders de una toma, el embargo usa el origen R05 verificado y no índices
de muestras relativos como si compartieran un cero. Origen ausente se rechaza
para esa comparación; casos de un mismo PCM conservan su reloj común.
Build TypeScript/Vite pasa. Chrome HTTP real (3.6s): seis figuras de PCM sintético,
preset sin casos, dos resultados byte-idénticos, tabla de siete lecturas,
recálculo, reload y rechazo de reserva inválida sin registro nuevo.

Fixture8903 detenido. Control de ganancia muestra recuperación desde RMS completo/
magnitud y resultado nulo desde shape (valores en README R07). Sólo control de
canal sintético; faltan atributos corporales/tomas independientes, medios físicos,
aceptación humana y controles científicos más amplios. Audio/defaults intactos.

## R07: etiquetas de features verificadas — 2026-10-03

Catálogo y agregado ligado a EVAL exacto del PCM. Window=origen R05+índices,
sin etiquetar colas; métodos mean/rms/std/peak_abs y límites de observaciones/
cobertura/gap configurables. Unidades y soporte observado común, deduplicación,
causas y procedencia explícitas. Perfil portable y etiquetas recalculadas al
congelar casos; edición manual elimina el claim de cálculo verificado.

31 tests de labels/readout/archivos/API/adapter corporal pasan (11.36s), incluyendo
estadísticas conocidas, missing/gaps/bordes, unidades, vinculación EVAL/PCM,
targets modificados rechazados y cola sin etiqueta corporal. Build pasa.
Chrome HTTP real (7.1s): seis figuras de EVAL con poses sintéticas, catálogo,
perfil/targets/unidades/coverage, respuesta demorada con contexto inmóvil,
export portable sin casos, congelación con procedencia, figuras byte-idénticas,
edición manual y reload. Fixture8904 detenido; defaults/sonido cotidiano intactos.
Una prueba posterior precisa módulo/NumPy del agregador en el resumen; no cambia
el cálculo. No cuerpo real ni aceptación humana verificados en este corte.
Las evaluaciones corporales locales existentes se identificaron para reutilizar;
no se reprocesó tracking ni se inventó identidad/calibración.

## R07: primera corrida corporal local del readout — 2026-10-03

Recorrido real EVAL archivado → candidato R05 → PCM → diez figuras R07 →
etiquetas verificadas → readout congelado. Cinco ventanas de entrenamiento y
cinco reservadas de dos segundos, fijadas antes del ajuste, con embargo temporal.
Dos features de velocidad, agregadas por media, comparten 60 observaciones
válidas por ventana; holds deduplicados. Calibración existente conservada,
sin recomputar tracking ni copiar videos. Repetición desde el dataset congelado
y verificación explícita de ambos resultados pasan; result.json byte-idéntico.

Artefactos y resultados corporales quedan exclusivamente en el directorio local
`laboratory-dev/research/r07-body-checks/` bajo el data root. No se publican los
valores, medios, identidades ni hashes privados. Un cuerpo/toma; la reserva
temporal no equivale a sujetos o tomas independientes. Etiquetas derivadas del
mismo movimiento que origina el PCM: recuperación no demuestra HIT ni un
mecanismo biológico. Sí verifica el recorrido técnico con datos corporales.
Síntesis R05 experimental; audio cotidiano, defaults y servicios preservados.
Escucha y aceptación humana de este recorrido siguen pendientes.

## Sai/Oliva: integración del banco Fourier — 2026-10-03

Commits de #36 (`eda50d2`, `2767df1`) y #97 (`3734d50`) incorporados conservando
autoría en una rama sobre #96; sin cambios al runtime/UI/modelos productivos.
34 tests del bridge pasan contra Weaver actual (18.90s): espectros individuales,
espectro cruzado complejo compartido, soporte común de tres condiciones,
contraejemplos, carácter offline y procedencia de módulos realmente importados.
El comando completo `PYTHONPATH=src:. .venv/bin/python -m
research.laboratory.sai_bridge.run` termina correctamente. Los tres ejemplos
acoplados reproducen las cifras redondeadas del informe: residuo independiente
.549/.533/.316, soporte común 471/466/471; MAE de I compartido respecto al
original .427/.394/.408. Los seis módulos declarados provienen del `src/` actual.
JSON sintético local: `/tmp/weaver-sai-fourier-integrated-20261003.json`.
Integración publicada en #98, apilada sobre #96; sin merge automático.

El I implementado normaliza direcciones y usa historia temporal acotada;
preservar estadísticas Fourier globales de segundo orden no exige preservar esa
traza no lineal. El residuo distingue el ejemplo acoplado y no se promueve a
objetivo universal. El informe conserva resultados sin distinción y límites.
No se exige equivalencia de hashes con el entorno de Oliva; el digest contiene
metadatos. No se valida HIT, eficiencia corporal ni aceptación perceptual.

## R11: original CSV y mapeo archivados — 2026-10-03

Archivo separado del Stream nativo: source.csv byte-exacto, Request con texto/
metadata/map, resultado y manifest. ID por contenido, staging oculto, recuperación
idempotente y lecturas de integridad sin conversión implícita. Recálculo explícito
compara resultado sin sobrescribir ni bloquear por diferencias del entorno.
UI guardar/listar/abrir/descargar/recalcular; no autoenvío al recargar ni copia
grande en sessionStorage. Native Stream y audio/defaults permanecen compatibles.

26 pruebas importer/archive/API pasan (2.19s): BOM/CRLF/bytes exactos, unidades,
null/cero/gaps, restart/retry, integridad, binding, código histórico y guardado
interrumpido oculto con reintento válido. Comando:
`PYTHONPATH=src:tests .venv/bin/python -m pytest -q tests/research/test_neuro_csv.py tests/research/test_neuro_csv_archive.py tests/test_lab_neuro_api.py`.
Build TypeScript/Vite pasa. Chrome real (3.5s), HTTP en fixture8905: conversión,
publicación seguida de 503 simulado, listado/reintento sin duplicado, reload,
reapertura, descarga original byte-exacta y recálculo. Fixture detenido después.
Sólo CSV sintético; no adquisición real, hardware ni sincronización física.

## Sai–Oliva: banco Fourier configurable desde la web — 2026-10-03

Wrapper nuevo en src/ y panel web, sin modificar el bridge reservado a Oliva.
Muestras/Hz/semillas configurables y preset JSON portable; tres escenarios del
aporte #97. Worker propio, una corrida activa por instancia, cancelación, restore,
artifact allowlist y procedencia de módulos realmente importados. Loader lazy
desde checkout en namespace propio, sin alterar sys.path ni tests/research.
Lectura completa verifica hashes, configuración, inventario y soporte; no rerun
implícito ni afirmación de autenticidad numérica para archivos rehasheados.

11 pruebas service/API pasan (21.00s); prueba adicional de cancelación real pasa
(0.36s). Incluyen dos workers con resultados byte-idénticos, reopen sin nuevo
worker, corrupción, presupuestos, soporte modificado y request alterado durante
cálculo. Build TypeScript/Vite pasa. Chrome HTTP real (21.5s): dos bancos con
dos semillas, comparación byte-idéntica, escenario estático sin soporte, selectors,
reload, recuperación y preset portable sin iniciar nueva corrida al importar.
Selectors tienen nombres accesibles estables. Fixture8908 detenido después. Banco sintético, torso .26/modelo fijo; no Fourier corporal,
HIT, aceptación humana ni cambios al sonido cotidiano. Oliva tiene encomendada
la extensión corporal según NEXT_ITERATION.md.

## R06: espectros individuales conservados por circular shifts — 2026-10-03

Campo opcional por puerto, cero/común/diferenciado; nuevos reportes de calendarios,
dosis, checks FFT completos y métricas/traces/deltas con igual medio y cero inicial.
No altera condiciones originales ni serialización al omitir el campo. Cruces con
medios/fases/semillas/permutaciones, presupuestos, validators y configuración web.
Conservación periódica de entrada no impone invariancia de respuesta finita.

56 tests pertinentes R06 pasan (39 bank/service/API/shifts +17 phases/spectrum),
incluyendo cero idéntico, FFT odd/even, DC, espectro cruzado común, contraejemplo
periódico, cruces completos, campos corruptos/rehasheados y bounds antes de render.
Build pasa. Chrome real (5.1s): preset portable, dos bancos con resultados
byte-idénticos, tabla 3 controles×4 calendarios y selección de traza desplazada.
CLI de referencia +verify pasan; observaciones sintéticas en README R06.
Fixture8909 detenido; audio/servicios cotidianos/defaults preservados.
No controles corporales, aceptación perceptual ni confirmación HIT.

## Integración de la pila #86–101 — 2026-10-03

Suite conjunta de laboratorio/research: **726 passed**, sin skips, 157.41s.
Se corrigieron dos imports de fixtures que dependían del orden de colección.
Las pruebas que usan PCM/captura de Shaper requieren su checkout explícito en
PYTHONPATH además de SHAPER_DIR; no se instala ni inicia un servicio de audio.

```bash
SHAPER_DIR=/home/nicolas/Projects/harmonic-shaper-dev PYTHONPATH=src:tests:/home/nicolas/Projects/harmonic-shaper-dev/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_lab_*.py tests/research/test_*.py --maxfail=5
```

Observaciones/driver HarMoCAP, escenas de ingreso/derivadas y transform derivative:
45 pruebas adicionales pasan (2.22s). No nuevas modificaciones de audio/UI;
evidencia de build y Chrome de #101 sigue válida. No escucha/latencia física nueva.
Shaper seleccionado `00893ad`: fuentes productivas iguales a main `f8bfe07`,
diferencia sólo en test_shaper_contract.py. Weaver main sigue `cc5fb57`; la pila
abierta no está instalada en el laboratorio cotidiano. HarMoCAP main `25fda8d`,
workspace original con cambios preservados, sin checkout/reset/retracking.

IMPLEMENTATION_STATUS.md actualiza el resumen vigente R01–R13 y distingue
entregas existentes de pendientes: LAB-09 aún no exporta skeleton/figura ni
consulta recovery in-flight de Shaper; R01/R13 requieren ampliación de modelos/
reservas; hardware, participantes y aceptación quedan explícitos. No se marca
completo el roadmap a partir de estas pruebas.

## LAB-09: recuperación consultable sin segundo writer — 2026-10-03

Nuevo Shaper anuncia pollable_jobs y conserva recibos/lease del writer real.
Weaver congela ID antes de HTTP y consulta tras respuesta perdida; restore/acción
explícita conserva ID. 404 confirmado permite POST idempotente; 5xx/transporte/
timeout no relanzan otro ID. Ruta legacy y su retry por hashes siguen compatibles.
No nuevo audio/UI/defaults ni instalación sobre servicios cotidianos.

18 tests Shaper capture/recovery/jobs pasan (1.08s); 56 Weaver captura/poll/cámara/
journal/export/input pasan (5.78s). Prueba integrada adicional con Shaper API real,
PCM sintético y respuesta POST perdida pasa (.44s): una sola ejecución/prefijo.
Incluye live lock visto desde otra instancia, restart, job muerto interrumpido,
identidad distinta rechazada y restore de receipt Weaver sin POST. No hardware.
No build/browser nuevo requerido: UI no cambió. Overlays/prefijos/sincronía física
siguen pendientes; no se declara terminado LAB-09 ni aceptación humana.

## LAB-09: esqueleto observado en exportación — 2026-10-03

42 pruebas de skeleton/export/timeline pasan (6.37 s), incluidas exportaciones
reales FFmpeg completas y recuperadas con preview AAC: PCM del MKV idéntico,
poses observadas dibujadas, omisión ante cambio de época y captura parcial
conservada. Unidades/proyección, identidad, secuencia de cámara, selección, held,
confianza, aspect y letterbox tienen pruebas pertinentes. Datos sintéticos.

Build TypeScript/Vite pasa. Chrome: un test de controles reales de CapturePanel
(1.5 s, red simulada) confirma defaults apagados y payloads de export completo
y recuperado, sin iniciar captura. No demuestra adquisición ni sincronía física.
Servidor de prueba detenido al terminar; servicios cotidianos/R24 preservados.
Sin escucha ni aceptación humana nuevas. Figura armónica exportada pendiente.

## LAB-09: figura desde bloques PCM efectivos — 2026-10-03

47 pruebas figure/skeleton/export/timeline pasan (7.31 s). Un corte posterior
añade una prueba integrada con Shaper real: seis voces generadas sin dispositivo
se capturan y se leen con el reloj/fases efectivos (las seis pruebas del módulo
figure pasan en 1.36 s). Renders FFmpeg completos y recuperados conservan PCM
exacto y muestran seis voces en el panel MP4. Se cubren corte final de callback,
rampas, fases, cambio de bloque, silencio confirmado, ausencia/NaN de telemetría
y capturas históricas sin datos de osciladores. Datos exclusivamente sintéticos.

Build TypeScript/Vite pasa. Chrome, red simulada: controles de esqueleto y
figura, estilo JSON y frecuencia de ventana llegan a exportación de prefijo.
Sin dispositivo R24 ni servicios cotidianos modificados. Sin aceptación humana
ni medición de sincronía física. El resultado es una figura pre-shape/limiter,
no un cymatic observado ni una prueba de HIT.

## LAB-09: ajustes portables sin acciones implícitas — 2026-10-03

10 pruebas capture-profiles pasan (1.13 s): restart SQLite, import entre
bibliotecas, instrumento/revisiones/eventos intactos, validate sin persistencia,
HTTP descarga/404 y rechazo atómico de versión, campos de fuente/calibración,
recovered_prefix, geometría impar y NaN. Seis pruebas existentes de contratos y
SessionStore pasan (.18 s). Sin dispositivos ni datos corporales.

Chrome: guardar/recargar/aplicar JSON, rechazo sin cambio de controles y acciones
limitadas a perfiles; payloads de esqueleto/figura conservados. Red simulada: no
demuestra adquisición. Build TypeScript/Vite pasa. No nuevos defaults del
instrumento ni aceptación humana; la configuración no inicia grabación.

## R01: familias de pronóstico sintético y EVAL — 2026-10-03

27 pruebas grassmann/families/body pasan (5.18 s); una prueba corporal adicional
verifica las seis familias y reset de gaps (las siete del módulo families pasan,
.82 s). Cubre q=1 equivalente al ridge anterior, tendencia conocida, causalidad
incluso cuando se altera el target ya pronosticado, rotación global, repetición
byte-idéntica, soporte común y selección inválida/métodos incompatibles.

Tres bancos sintéticos congelados y comando reproduce_families.py ejecutados:
soporte y resúmenes numéricos reproducidos con tolerancias declaradas. Hay casos
de mejora y de empeoramiento por retardos; no selección post hoc de defaults.
Build TypeScript/Vite pasa; Chrome: controles sintéticos/tabla y controles
corporales/JSON/payload pasan (red simulada). El mock sintético se acotó a R01
para que acciones de otros paneles no alteraran su inventario artificial.

Defaults y síntesis cotidiana sin cambios; sin datos privados ni escucha nueva.
Predicción específica de HIT y validación en tomas/cuerpos reservados pendientes.

## Bridge Fourier corporal de Oliva integrado — 2026-10-03

PR #107 head f424981 incorporada sobre #108 por cherry-pick con autoría
preservada. Sin cambios a sus cinco archivos, a runtime/síntesis o a instalación
cotidiana. 58 tests test_sai_bridge_*.py pasan en 27.68 s. Comando completo
`PYTHONPATH=src:. .venv/bin/python -m research.laboratory.sai_bridge.body_fourier`
ejecutado con BLAS/OMP a un thread; resultado sintético local, no publicado.

Nueve productores efectivos provienen del checkout integrado. Retención
upper_body 800/910; one_scalar 128/128. Residuo colectivo original/shared del
ejemplo coupled cercano a cero (shared seed 7: .001911); independiente
.357087/.377547/.435354 para seeds 7/19/41, soporte común 231/205/231.
Esto coincide numéricamente con el informe recibido sin exigir igualdad de
digests entre entornos. El control escalar compartido/independiente coincide.

Precisión de alcance del informe: 55–94% bajo fases independientes corresponde
al segmento 7–9 (.549585/.707677/.940500). El segmento 8–10 da
1.060721/1.105046/1.116235 (106–112%); las fases compartidas en ambos segmentos
dan 7.9–14.0%. No resumir el rango 55–94% como máximo de ambos antebrazos.
Se registra aquí sin modificar el archivo reservado del aporte ni bloquear
la incorporación; la conclusión cualitativa se conserva.

Espectros conservados no implican geometría articulada conservada: el informe
y los tests muestran desvíos en brazos rígidos y cambios de I incluso bajo
fases compartidas. Diagnóstico es desviación de longitudes congeladas, no
puntaje anatómico ni evidencia de intención/HIT/coupling causal/eficiencia.
Sin datos humanos privados, escucha ni aceptación nuevas. Servicio/UI corporal
y contraste geométrico restringido quedan pendientes concretos.

## Fourier corporal: consumidor worker/API/UI — 2026-10-03

Cinco tests del nuevo servicio verifican freeze por identidad, held como inválido,
preparación sin worker/runtime mutado, escala requerida/muestreo/preset inválidos,
worker real repetido con idéntico snapshot, restore e integridad, cancelación de
proceso propio e inicio concurrente rechazado. Fixtures sintéticas del bridge.
Build TypeScript/Vite pasa; Chrome (red simulada) pasa en 1.4 s: selección
explícita, escala inicialmente ausente, preparar/correr/abrir y Sin soporte; no
requests al instrumento ni audio. Los 58 tests del bridge se reutilizan del
corte anterior, dado que sus archivos permanecen intactos.

Se corrigió representación tuple/list al verificar configuración serializada.
La prueba de repetición usa un preset congelado: IDs nuevos son nuevas entradas,
no evidencia de una diferencia numérica. Sin datos reales privados publicados,
R24 ni servicios cotidianos modificados. Recorrido web con tracking corporal real, sincronía física, escucha y aceptación
siguen pendientes explícitos; la verificación backend posterior se registra abajo.


## Fourier corporal: soporte sobre tracking real — 2026-10-03

Verificación local del backend con un segmento corporal privado de biblioteca:
selección manual previa de persona y escala de la misma generación, manifest y
frames del cache verificados, backend CPU identificado. Sin copiar video,
recalcular tracking, publicar datos privados ni modificar servicios cotidianos.

Con brazos/muñecas y mínimo de 64 muestras, la preparación no retuvo bloques:
invalidaciones de articulaciones fragmentaban el soporte. La corrida terminó
sin comparaciones, sin presentar ausencia de soporte como resultado cero.
Con codos y el mismo mínimo hubo un bloque válido; con brazos/muñecas y mínimo
explícito de 32 hubo dos. Ambos ajustes produjeron soporte colectivo común y
resultados byte-idénticos al repetir las entradas congeladas en este entorno.
No se cambió el mínimo por defecto ni se rellenaron gaps o bajaron umbrales.

El consumidor agrega longitudes de bloques descartados por ser cortos y muestra
su máximo en preparación. Respeta identidad y límites del grid del bridge;
no modifica sus archivos ni su política de soporte. Seis tests del servicio
pasan (3.21 s), incluyendo separación por límites explícitos y no mutación de
entradas. Build TypeScript/Vite pasa. La prueba Chrome con red simulada verifica
el nuevo diagnóstico; no constituye un recorrido web con tracking real.

Estos controles comprueban funcionamiento y repetibilidad local; no validan
HIT, intención, eficiencia ni aceptación perceptual humana. Recorrido web real,
escucha y aceptación continúan pendientes.


## Fourier corporal · web de producción y escala por selección — 2026-10-03

Chrome headless recorrió el build de producción con FastAPI, VideoLibrary y
worker reales sobre la generación de cache corporal privada ya verificada.
Instancia aislada, sin abrir dispositivo de audio ni cámara. La generación se
cargó del cache verificado en memoria; no se probó la apertura/probe del video
ni se ejecutó tracking nuevo. Persona/escala de la selección manual previa.

Desde la pestaña Investigación: elegir fuente/persona, configurar intervalo y
canales, preparar, correr, abrir la corrida creada, cambiar descriptor y
exportar/importar ajustes. Preparación retuvo un bloque y el resultado mostró
soporte común colectivo y las tres condiciones con medias presentes. Sin errores
JavaScript ni mutaciones de transporte, fuente, calibración o síntesis. Los
POST de validación de configuración de otros paneles son consultas sin cambios
al instrumento. Entradas, resultados y evidencia del navegador permanecen locales.

Se corrigió conservación silenciosa de escala/procedencia al cambiar fuente o
persona e importar ajustes: se limpian esos campos y se preservan los del método.
Un JSON incompleto bloquea el cambio de selección y conserva el texto editado.
Dos pruebas Chrome con red simulada pasan (1.9 s); build TypeScript/Vite pasa.
El recorrido de producción/API/cache real también pasó con el cambio, incluyendo
importación sin escala anterior y parámetros del método preservados.

Esto cubre el recorrido web del análisis con tracking real congelado; no escucha,
aceptación humana ni adquisición en vivo. La salida de audio desconectada es una
condición de prueba explícita, no evidencia de funcionamiento de la R24. Defaults
sonoros y servicios cotidianos intactos. Sin validación científica de HIT.


## EVAL · presupuesto y continuación entre corridas — 2026-10-03

27 pruebas de evaluación/PCM pasan (16.13 s, sin skips) con Shaper-dev explícito;
tras conservar estado/error anteriores en el manifest, tres pruebas pertinentes
adicionales pasan (2.22 s). Verifican matriz de dos fuentes × dos presets,
reutilización sin nuevo replay ni cambio de mtime de artefactos completos,
paridad de traces/comparaciones frente a matriz fresca, rechazo de entradas/
cache/artefactos/código de replay cambiados antes de escribir manifest, lock,
recálculo de corrida parcial fallida, conservación de error previo, recuperación
tras restart/cancel marker, API y cambio de presupuesto sin mutar request.
Cambios de HEAD/hash global de investigación no bloquean continuación si la
identidad del replay se conserva. Normalización JSON al congelar evita diferencias
int/float de defaults al recuperar una entrada idéntica.

PCM: WAV y estados de osciladores completados permanecen sin reescritura; los
renders restantes con reset/preroll coinciden byte por byte con render fresco.
Audio completo alterado se rechaza antes de mutar el manifest incompleto.
Build TypeScript/Vite pasa. Dos pruebas Chrome aisladas (presupuesto/continuación
y controles/artefactos PCM) pasan; UI usa red simulada, backend usa workers reales.

Verificación privada adicional: cache corporal existente, selección/escala de la
misma generación y presets de referencia de seis voces. Dos segmentos cortos ×
dos presets, tanda de una corrida y continuación de tres. Features, WAV, estados
de osciladores y reportes sobre soporte común coinciden con ejecución completa
nueva en este entorno. No se recalculó tracking, copió video ni abrió dispositivo
de audio. Resultados y entrada corporal permanecen locales; no publicados.

Presupuesto limita corridas enteras, no costo de una corrida. Sin recuperación de
estado a mitad de modelo/PCM ni claim de checkpoint físico. No prueba escucha,
latencia audiovisual física, aceptación humana ni conclusiones científicas.
Defaults sonoros, R24 y servicios cotidianos intactos.


## EVAL · paquetes seleccionados y revisión de contenidos — 2026-10-03

Seis pruebas pertinentes de paquetes/PCM pasan (6.73 s, sin skips): eliminación
de labels/IDs/rutas/persona/calibración del resumen, proyección de medias sobre
soporte original, Request por corrida seleccionada, worker real/repetición ZIP
byte-idéntica, restore/checksum/traversal, preview obsoleta, cambio de trace durante
writer sin ZIP publicado, presupuesto de payload y API con descarga real. PCM incluye WAV/estados
sólo por opción explícita, sin nuevos renders. Dos pruebas Chrome aisladas pasan
(2.5 s): selección/preview/generación/link, preferencias portables sin indices,
respuesta tardía descartada tras edición y regresión de controles/artefactos PCM.
Build TypeScript/Vite pasa; formato posterior de fuente/tests no cambia semántica.

Comprobación adicional del preset con labels/IDs reemplazados: replay de fixture
produce señales y targets idénticos al preset original. No afirma igualdad de
routing diagnostics con IDs reemplazados ni identidad de hashes de traces.

Verificación local adicional con comparación corporal privada completa ya existente:
dos corridas elegidas, ZIP sólo resumen y ZIP con PCM. No incluyen pedidos/traces
cuando no se seleccionan; resumen omite campos privados de fuente/calibración.
Ningún paquete se publicó ni abrió dispositivos; no se copiaron video/tracking.
Los ZIP y resultados permanecen locales. No se certifica anonimato de métricas ni
consentimiento de difusión; escucha/aceptación humana y sincronía física pendientes.
Servicios cotidianos, bridge de Oliva y defaults sonoros intactos.

### R03 · Sensibilidad a un intervalo temporal declarado — 2026-10-03

`test_temporal_match.py`, `test_temporal_controls.py` y `test_coincidence.py`:
34 pruebas pasan (0.86 s). Cubren matching original, soporte discontinuo común,
rango muestreado con coincidencia sensible al offset, ausencia de denominadores,
límites de tamaño/valores, conservación de comparación nominal y worker repetido
con parámetros nuevos congelados. No se estiman incertidumbres desde datos.

Chrome: `coincidencePanel.spec.ts` pasa (1.6 s), validando controles, pasos enteros,
request y configuración portable; `coincidenceNetwork.spec.ts` pasa (3.3 s)
contra fixture HTTP real, worker y harness de producción. Dos corridas de la misma
selección con semiancho 0.05/2 pasos por lado producen `result.json` byte-idéntico,
cinco condiciones y ambas tablas visibles; descarga de features verificada.
Build TypeScript/Vite pasa (1.27 s). Servidores exclusivos de prueba detenidos.
Todo sintético, sin dispositivos, escucha o nuevos datos humanos; defaults de
síntesis/presets intactos y sensibilidad apagada por defecto. Falta medir latencia
física, incertidumbre por evento y recoger marcas humanas independientes.

### R12 · CSV explícito, archivo original y lector común R11 — 2026-10-03

10 pruebas nuevas de physiology_csv pasan (0.97 s): units/calibración, null/gap,
índices/tiempos, trapecios parciales, digest/BOM/CRLF, archivo/restauración/
repetición/corrupción y API real. Regresión neuro_csv/neuro_csv_archive/physiology:
31 pasan inicialmente; la prueba EVAL restante pasó (1.49 s) al declarar
SHAPER_DIR explícito (sin audio). Total 42 pruebas backend aprobadas en esos grupos.
La conversión R11 actual se comparó directamente con la implementación anterior
sobre su fixture existente: salida idéntica, no sólo tolerancia numérica.

Chrome contra API/Vite propios: CSV y recorrido R12 previo pasan (2.4 s).
Después de ampliar el test CSV para editar protocolo durante una inspección,
pasa de nuevo (2.3 s): descarta respuesta obsoleta, sin aplicar datos a otro
contexto. Recorrido verifica bytes originales exactos, conversión temporal,
missing causes, proveedor conservado y análisis nativo. Etiquetas accesibles y
selector de descarga de regresión ajustados para coexistir con imports CSV.
Build TypeScript/Vite final pasa (1.27 s); sin dispositivos ni datos humanos.
El proxy aislado declara origen de prueba; protección del servidor no se modifica.
Servidores propios detenidos. Export real, BLE/RR, calibración/sincronía físicas
y aceptación humana permanecen pendientes. No cambia presets/defaults de audio.

### R01 · Forecast con armónicos declarados — 2026-10-03

Regresión previa: 28 tests de familias/grassmann/body pasan (5.55 s). Suite de
familias ampliada: 16 pasan (1.10 s), incluyendo siete predictores, rotación,
artifacts repetidos, cuerpo con gaps, recuperación de sin/cos conocidos y fallo
con frecuencias incorrectas, clocks/vectores objetivo modificados a horizontes
1/4, y frecuencias no admitidas por muestreo. No hay interpolación de gaps ni
optimización de frecuencias. Default evaluate comparado directamente con la
implementación anterior: rows/metrics idénticos en fixture existente.

Chrome sintético/corporal pasa (2 tests, 3.2 s), con selección de siete métodos,
fundamental/ratios decimales, configuración/request y columna MSE del nuevo método.
Build final pasa (1.21 s). Reproducer de armónicos repite sus condiciones y conserva
resultados idénticos; evidencia pública estrictamente sintética en r01_grassmann.
Con 225 slots comunes: MSE conocido 0.0001395223 e incorrecto 0.4399455 sobre mismos
datos; shuffle 15.8073; blanco estocástico separado 29.5150. Son controles conocidos,
no inferencia sobre HIT/cuerpo/partículas. Frecuencias corporales/ley física y tomas
reservadas siguen pendientes. Servidor propio Vite detenido; sin audio/hardware.

### R01 · Integración corporal privada y diagnóstico de soporte — 2026-10-03

Sobre el EVAL corporal local existente de 60 s, dos workers R01 reales usan seis
velocidades de igual unidad, cuatro familias (incluida fixed_harmonics), componentes
3, ventana 2 s, ridge 0.1, horizonte 6 y frecuencias .35×[1,2,3,4,5,6]. Es configuración
exploratoria fijada antes de correr, no frecuencias corporales descubiertas.
Medio/persona/generación/escala/procedencia coinciden exactamente con la fuente
previamente verificada del cuerpo derecho. No se transfiere calibración. No lee
ni copia video/tracking; usa features congeladas verificadas del EVAL guardado.

Ambos workers completan con soporte común no vacío; las cuatro familias aparecen,
fit_end ≤ origin < target en todos los forecasts y tiempo estimado explícito.
Inputs y todas las trazas de controles/paired tienen hashes idénticos entre esas
dos corridas. Evidencia privada bajo `<data-dir>/private-r01-harmonic-check/`,
fuera de GitHub: no se publican métricas corporales, IDs, hashes o trazas.
Este recorrido se repitió tras añadir los diagnósticos y vuelve a pasar. No abre
audio ni recalcula tracking; no prueba HIT, percepción o generalización entre tomas.

Diagnóstico web/manifests separa elegibilidad por origen (geometría/ventana/límite
de muestreo/objetivo fuera de segmento/commit) de objetivos puntuados; informa
error absoluto medio/máximo del tiempo objetivo estimado frente al observado.
Es error del reloj de features, no medición de latencia física. Suite de familias
ampliada: 17 pasan (1.14 s), incluyendo inventarios exhaustivos y ausencia de score
con alias temporal; reloj irregular da error explícito. Chrome del resultado pasa
(2.5 s) y build pasa (1.21 s). Vite propio detenido. Defaults/audio conservados.

### R11/R12 · Timestamps ISO explícitos y origen portable — 2026-10-03

30 tests previos de CSV/archivos R11/R12 pasan (1.11 s). 12 nuevos de sensor_csv_iso
pasan (1.02 s): offset equivalente, microsegundos, cambio de día/leap day, origen
posterior rechazado, ausencia de zona/fechas inválidas/leap second/precisión extra
rechazadas, versión explícita/no autodetección, archive/restore/raw bytes y API
real. Valores/unidades y Clock de metadatos permanecen declarados.

Chrome R12 ISO + regresión nativa pasan (2.8 s); R12 ampliado pasa (1.9 s) verificando
export/import portable sin transportar origen. Chrome R11 numérico/API/nativo pasa
con montaje aislado de NeuroPanel: incluye pérdida de respuesta, archivo/restauración,
recompute y uso nativo; selector cambia ISO→numérico conservando mapeo anterior.
El intento inicial de usar shell completo con runtime mínimo no llegó a la pantalla
Investigación; no se atribuye ese intento a evidencia del recorrido live. El panel
real y servicios HTTP fueron verificados sin dispositivos; build pasa (1.31 s).
Servidores API/Vite de prueba detenidos, sólo fixtures sintéticos. No nuevas mediciones
humanas, reloj físico sincronizado ni aceptación perceptual; no cambios de síntesis.

### Shell completo con video privado y cache existente — 2026-10-03

Chrome sobre el build de producción, LaboratoryRuntime y VideoLibrary reales:
video avanza durante la corrida R01 con armónicos declarados y al reseleccionar
la misma Persona explícita; resultados y diagnósticos visibles; seis targets,
al menos uno activo; cero errores JavaScript. Tracking existente verificado, sin
reprocesarlo ni copiar video. Audio reemplazado por registro de controles: no
abre dispositivos ni acredita escucha humana. Evidencia corporal sólo local.

Fixture reutilizable: `tests/laboratory_ui_fixture.py` admite
`--frozen-evaluation-request <request.json> --frozen-cache-root <data-dir>`
y `--source-index 0`, además de `--root <directorio-nuevo> --ui laboratory-ui/dist`
y `--checkpoint <checkpoint-local>`. Ejecutar con `PYTHONPATH=src:tests` usando
el Python del proyecto. Conserva la persona explícita del request; no traslada
calibración. Reproduce el medio completo desde start_s, sin recortar en end_s.
Sirve el build y los servicios reales con controles sin audio; Ctrl+C lo detiene.
Los paths e inventarios privados no deben publicarse.

### Integración conjunta hasta #118 — 2026-10-03

Suite completa `tests`: **1070 passed, 4 subtests passed**, sin skips/fallos,
278.80 s. Weaver 5db9a3e; Shaper de desarrollo 516ebde; HarMoCAP lab 27b8fc2
consultado sin modificarlo. Una advertencia de deprecación de Starlette/anyio.

```bash
SHAPER_DIR=/home/nicolas/Projects/harmonic-shaper-dev PYTHONPATH=src:tests:/home/nicolas/Projects/harmonic-shaper-dev/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest -q tests --maxfail=5
```

El primer comando con sólo PYTHONPATH=src falló al recolectar diez módulos por
imports de fixtures. `pyproject.toml` incorpora tests en pythonpath para quitar
esa dependencia manual; el comando básico `PYTHONPATH=src ... pytest --collect-only
-q tests` recolecta las 1070 pruebas (1.82 s). Shaper sigue siendo una dependencia
explícita para las pruebas PCM; no se inicia un servicio ni un dispositivo.

Heads main de AlterMundi verificados: Weaver cc5fb57, Shaper f8bfe07, HarMoCAP
25fda8d. Los origin de estos checkouts leen forks de Nicolás con otros main
históricos (Pads v2); no se confunden con los heads de AlterMundi. Workspaces
originales conservan sus cambios; laboratorio cotidiano permanece en cc5fb57
y Shaper lab en f8bfe07. Sin checkout, merge, reprocess ni cambios de R24.
No acredita escucha, calibración física, resultados HIT ni aceptación humana.

### R11/R12 · Índices de fila opt-in — 2026-10-03

14 pruebas nuevas +48 previas de CSV/archivos/API pasan (62, 2.19 s); suite nueva
ampliada a 15 pasa (0.30 s) con registros multilínea/preámbulo. Verifica numérico/
ISO, Clock/valores intactos, gaps/faltantes, archivo/repetición y rechazo de modo/
versión omitidos, columnas incompatibles, filas vacías, orden temporal inválido,
origen ISO numérico y exceso de presupuesto. No genera timestamps.

Chrome API/paneles reales: dos recorridos nuevos pasan (R11 numérico/R12 ISO),
original UTF-8 intacto, origen/índices/missing/procedencia y preset portable;
volver a columna restaura contrato previo. Dos regresiones existentes de R11/
R12 CSV pasan (3.3 s). Build TypeScript/Vite pasa (1.21 s). Sólo fixtures
sintéticos, sin hardware/datos corporales/audio. No acredita ausencia de muestras
perdidas físicas; procedencia dice device_counter_observed=false. Defaults de
import/audio conservados. Servidores propios detenidos tras estas comprobaciones.

### R08 · Preview original del mapeo de extremos — 2026-10-03

Chrome real sobre RopePanel/API y video sintético: 1 recorrido pasa (3.9 s).
Botón bloqueado sin fuente preparada; lectura opt-in pide media/frame/hash
correctos, imagen PNG cargada y overlay visible. Ocultar retira imagen; retener
respuesta REAL del start mientras se cambia corrida provoca cancelación del
job aceptado al recuperar ID, no muestra imagen obsoleta. Mantiene recorrido
individual/pareado, POST perdidas, coverage, descarga y reapertura sin recálculo.

Build pasa (1.23 s); cinco pruebas existentes de benchmark HTTP/lector/jobs
pasan (2.43 s). Reutiliza decoder/servicios verificados; no nueva inferencia
ni copia de video. Servidores aislados detenidos. Fixtures sintéticos, sin
medios corporales/audio/dispositivos. Falta revisión manual corporal; esto
verifica UI y contratos, no calidad de tracking/ground truth ni escucha.

### R09 · Triangulación pareada declarada — 2026-10-03

26 core/HTTP/regresiones pasan (2.16 s): trayectoria métrica conocida/repetición,
rotación mundo→cámara, tiempo/incertidumbre/held/ausencia/paralaje/reproyección,
puntos al infinito/detrás de cámara, matrices/clock/orden/dimensiones/presupuesto
inválidos, API y configuración que rechaza campos de calibración. Salida siempre
inferred o missing, sin coordenadas cero sustitutas ni confianza 3D fabricada.

CLI de control ejecuta/repite cuatro condiciones y guarda inputs/result/summary.
Evidencia pública es sintética: known error3D~7.1e-15m; wrong_pairing obtiene
0.484m de error pese a reproyección<0.6px. Offset/paralaje dejan missing; nulos
no se convierten en cero. Esto no mide calibración ni exactitud física.

Chrome panel/API reales pasa (1.7s): carga explícita de ejemplo, reconstrucción/
figura/diagnóstico, exclusión por umbral, preset sin fuentes y sin cálculo al
importar, export íntegro y uso/guardado como stream declarado R09. Build pasa
(1.24s). Servidores propios detenidos; sin datos privados/dispositivos/audio.
El corte siguiente añade writer/worker propios, documentado abajo.
Calibración/correspondencias/relojes físicos, undistorsión/adquisición e IMUs siguen
pendientes; pipeline no prueba HIT, cuerpo 3D real ni aceptación humana.


### R09 · Workers y recuperación de cálculos — 2026-10-03

4 tests worker/HTTP pasan (2.05s) tras verificar vínculo del stream a fuente/slot/
marco/calibración e inferred/missing: freeze, recibos/restart, repetición/recálculo,
corrupción y cancelación de procesos propios sin matar ajenos. Antes, 33 tests
incluyendo core y regresiones lifecycle/API R03/R04 pasaron (5.97s).
Chrome: 2 tests pasan (4.0s total) sobre panel/API/workers reales. Preview previo
conservado; nuevo recorrido pierde deliberadamente respuesta de POST ya aceptado,
recarga conservando IndexedDB sin enviar, recupera misma clave/cuerpo y un único ID,
abre entradas completas, descarga resultado, verifica y repite explícitamente;
otra recarga no calcula. Build pasa (1.23s). No dispositivos, datos corporales,
tracking, síntesis ni escucha humana. Calibración/sincronía físicas siguen pendientes.


### R09 · Edición durante apertura y seguimiento tras recarga — 2026-10-03

Chrome panel/API/worker reales: 2 tests pasan (10.4s). Respuesta de artifact real
retenida mientras se edita source_id: apertura se descarta y edición permanece;
nueva apertura explícita restaura inputs. Corrida sintética de 14400 frames ×3
puntos (43200 pares) iniciada antes de reload: inventario permite retomar seguimiento
y cancelar el hijo vivo, terminal cancelled. Intento IndexedDB inválido conserva
opción de descarte, recuperación deshabilitada, nuevo inicio habilitado después,
sin POST automático. Recuperación/presets/preview anteriores pasan. Build pasa
(1.35s). Backend no modificado; evidencia de #122 conservada. No dispositivos,
medios corporales ni escucha/sincronización física.


### R09 · Procedencia multivista en conversiones/comparación — 2026-10-03

15 backend/HTTP/regresiones pasan (3.74s): worker real, origen exacto, stream sin
mutación, recuperación tras restart sin reads de fuente/recalcular, mismatch de
manifest, procedencia declarada rechazada, binding del stream, cambio durante
publicación conserva conversión previa, clock/conversion/comparison compatibles.
Chrome: 2 tests pasan (10.6s), incluido POST de conversión aceptado con respuesta
abortada, reintento con mismo ID/manifest/clave, origen y stream exactos en artifact,
selección por IDs en comparador, admitir inferidos explícitamente y control identidad
5/5 soportados/error0. Recorridos anteriores conservados. Build pasa (1.34s).
Comparar un stream consigo mismo prueba recorrido, no referencia independiente ni
exactitud 3D. No escucha, datos corporales, cámaras, tracking ni calibración física.


### R10 · Archivo opcional de borradores — 2026-10-03

Chrome con IndexedDB y API reales pasa: conserva/dedup snapshot declarado, cierra
pestaña y abre otra con sessionStorage vacío; inventario persiste, sin player/media
ni POST automático. Export idéntico byte a byte, restore mantiene pendiente previo,
guardado explícito del trace ligado a protocolo sintético real retorna artifact;
corrupción local detectada, borrado conserva el registro del servidor. Test no
reproduce estímulos ni simula exposición humana. Build pasa (1.26s), bundle inicial
cotidiano mantiene tamaño; archivos sólo bajo investigación. Backend/player sin
cambios. Participantes, escucha/niveles/sincronía y sesiones largas siguen pendientes.


### R05 · Recorrido audiovisual corporal local — 2026-10-03

Chrome con bundle de producción, runtime/biblioteca/reader/workers reales pasa
(14.9s). Fuente es evaluación/selección corporal ya congeladas, cuerpo elegido
anteriormente, tracking CPU cacheado; fixture nuevo expone EVAL sólo lectura y
bloquea mutadores. Genera R05 pareado para6s dentro de clip60s a8000Hz, seis voces,
resonador positive_delta +mapeo de amplitud y cola0.5s. Ambos brazos decodifican PCM
muted/video original, figura6voces, overlay con joints observados y timestamp no
futuro; reproducción avanza frames reales, pausas/seeks/offset y final con cola
siguen reloj nominal. Soporte válido de ambos brazos coincide y es no vacío.
0 errores JS; fixture retorna control_targets_only, sin R24/audio device/cámara.

No video/cache/EVAL copiados, pose ni EVAL recalculadas, calib trasladada ni nueva
identidad inferida. Nuevos inputs/PCM/evidencia quedan en directorio privado local;
ningún dato o resultado numérico corporal se publica. Test genérico reutilizable:
`resonatorBodyNetwork.spec.ts` y flag --read-frozen-evaluation del fixture.
No cambios productivos ni motivo para repetir build/suite backend ya válidos.
Esto acredita decodificación/integración y reloj software, no escucha/aceptación,
latencias/sincronía físicas, precisión del tracking, comparación científica de
mecanismos ni generalización. Esas dependencias siguen pendientes.


### R04 · Escala congelada, faltantes y repetición corporal — 2026-10-03

Dos Chrome pasan (15.4s), producción/biblioteca/readers/workers reales. Evaluación
preexistente calibrada comparte fuente/persona/cache/segmento con selección anterior;
usa su escala aparente/procedencia archivadas sin aplicarlas al runtime. Dos corridas
locales de60s repiten result.json exactamente bajo entradas/env congelados. UI export/
import de parámetros+endpoints conserva selección y no inicia; ruido de velocidades
0.02/seed17 explícito. Seis condiciones mantienen clocks, filas inválidas/warmup
como missing, y resumen sobre soporte común observado no vacío.0 errores JS;
API state conserva calibration=null. Fixture separado de EVAL sin escala: UI bloquea
y API rechaza, sin nuevo job ni transferencia de calibración.

Inputs/traces/resultados corporales siguen locales, EVAL/cache sólo lectura, sin
copia del video, nuevo tracking, audio o calibración. Test reutilizable no contiene
IDs/rutas ni estadísticas corporales. Backend/defaults sin cambios; evidencia build
previa válida. No tarea/ground truth independientes, ruido de cámara medido,
eficiencia/intención/HIT, exactitud corporal, escucha ni generalización acreditadas.


### Arranque · selección explícita de pila — 2026-10-03

9 pruebas de scripts pasan (0.14s), con executables inertes/npm stub, sin servicios:
--describe no build/install/exec, defaults cotidianos, seis overrides env inválidos
rechazados pese a fallback disponible, paths/args con espacios, overrides CLI y
SHAPER_DIR efectivo, perfil dev con peer/datos separados. bash -n pasa. Describe
real en Legion resuelve Weaver-dev, Shaper-dev516ebde, HarMoCAP-lab27b8fc2 y entorno/
modelo existentes sin iniciarlos. No import/readiness de dependencias, R24/cámara,
CUDA, escucha ni aceptación física verificadas por este comando. No build/UI/backend
modificados; evidencia anterior conservada. No instalación/merge/migración cotidiana.

### Arranque real · diagnóstico sin audio y perfil único — 2026-10-03

La pila de desarrollo completa (Weaver, Shaper propio y bundle de producción)
arrancó en puertos/datos temporales explícitos. UI, /api/state y presets respondieron
200. En --no-audio Shaper mantiene 503 para voces efectivas; Weaver conserva los
ACK de control sin consultar esa telemetría ni afirmar revisión aplicada al audio.
La web muestra un aviso específico, sin error 503 ni botón de recuperación engañoso;
voice_frame=null, telemetry_valid=false, applied_revision=-1, seis voces del preset
y diagnóstico audio_status=disabled. Chrome: 1 test pasa (1.2s), cero errores JS.
Ctrl+C terminó los dos procesos propios; listeners cerrados comprobados. No se
abrió dispositivo, cámara, tracking ni datos corporales.

23 tests de audio/runtime/parser/wrappers pasan (1.89s): modo explícito conserva
ACK y liberación propia, no produce telemetría falsa, fallos reales de control
siguen visibles y --no-audio + --external-shaper se rechaza antes de iniciar.
El wrapper previo start-laboratory-dev.sh queda como único perfil; el nombre nuevo
start-laboratory-development.sh delega en él. Misma selección/datos, puertos
8875/8185 originales, overrides CLI prevalecen. bash -n, imports --check y resolución
--describe pasan contra los checkouts locales. Build final: 91 módulos, 1.28s.

Se conserva el modo sonoro/defaults y el estado cotidiano. Esta evidencia verifica
readiness sin audio y UI/control; no salida R24, latencia física, inferencia HarMoCAP,
CUDA, escucha ni aceptación humana. La pila sigue sin merge/instalación cotidiana.

### R13 · Control no lineal cuadrático reservado — 2026-10-03

16 tests pasan (2.84s) contra Shaper explícito para la fixture EVAL. Productos de
historia train-normalizada y coeficientes/bases/medias quedan congelados: modificar
el último objetivo test no cambia ningún modelo ni predicción previa. Prefijos pooled/
specific y train shuffle mantienen soporte común, excluyen prefijo y no cruzan gaps.
Budget24 coordenadas rechazado antes de worker; soporte vacío devuelve null.
Artefactos repiten/recomputan exactamente en este entorno. Baselines anteriores
siguen iguales cuando el control se activa o desactiva.

Banco público de tres casos ejecutado/repetido/recomputado, evidencia en protocolo
R13: ventaja sólo del positivo cuadrático construido; oscilador sin mejora relevante,
ruido IID peor que media train. No selección de hiperparámetros ni participantes.
Chrome de producción contra API/worker real: 1 test pasa (3.7s), opción portable
export/desactivar/import conserva settings,239 objetivos comunes, resultado repetido
idéntico y cero errores JS. Preset de seis voces, fuente y calibración intactos.
Build91 módulos pasa (1.31s). Servicios propios detenidos; sin hardware/video privado,
audio físico ni cambios al instrumento. No transferencia/HIT/aceptación acreditadas.

### Captura · errores visibles de consulta y reintento — 2026-10-03

Chrome: 1 test pasa (4.4s), bundle de producción con API real sin audio y fallos
de consulta introducidos por routing de prueba. Antes del primer inventario:
«Esperando inventario» e inicio deshabilitado. Tres 503 son visibles; último estado
confirmado se conserva, no se inicia otra operación. Una captura demorada y un
inventario de exportación demorado junto a error rápido mantienen una consulta
en vuelo por grupo, sin ocultar el fallo rápido. Al restaurar HTTP se limpian
alertas y se habilita inicio; cero POST y errores JS. Build91 módulos pasa (1.26s).
Servicios propios cerrados. Backend/PCM/grabación/defaults intactos; no prueba
de disco lleno, captura física, audio R24 ni escucha añadida por este recorrido.

### Comparador · inventario confirmado y fallos visibles — 2026-10-03

Dos tests Chrome pasan (13.0s): captura regresa tras extracción del hook común;
comparador usa bundle de producción con inventarios explícitos de UI partial/running,
503 y demora controlados. Primer inventario pendiente visible y una sola petición
durante demora. Partial2/4 conserva progreso tras fallo; repetir/continuar se
deshabilitan. Running conocido conserva cancelar disponible bajo fallo. Recuperar
el inventario limpia alerta/habilita acciones, sin POST ni errores JS.
No se crearon jobs ni pretendieron reales esos estados de fixture; API y servicios
propios reales sin audio, cerrados al terminar. Build92 módulos pasa (1.28s).
Backend/PCM/traces/player/defaults intactos; evidencia anterior no repetida sin razón.
No escucha, sincronía física ni nuevo resultado corporal/científico acreditados.

### Comparador · perfiles portables de procesamiento — 2026-10-03

30 tests backend pasan (1.98s), comparación/captura/runtime: rechazan fuentes,
persona/calibración, hashes motor/entorno y controles fuera de cotas; validación
no guarda; persistencia al cerrar/reabrir SQLite y portabilidad entre dos estados;
snapshot/calibraciones/último video intactos. API save/load/list/validate sin iniciar
evaluaciones. Cotas control/preroll/presupuesto reutilizadas del contrato Request;
PCM hereda cotas y excluye identidades.

Chrome producción/API/SQLite reales: 1 test pasa (2.0s), guardar/cargar/reabrir,
descargar JSON cerrado y aplicar; respuesta real demorada no sobrescribe ajustes
editados durante la carga. Instrumento/source/calibración intactos; cero POST a
evaluación y errores JS. Build93 módulos pasa (1.31s). Servicios propios detenidos;
sin hardware/tracking/datos corporales. Contrato de ejecución/worker/PCM/defaults
intactos; no escucha/aceptación humana añadida.

### Selección automática · límite corporal de calibración — 2026-10-03

Regresión reproducida antes de corregir: calibrar el cuerpo provisional del prefijo
y finalizar con otro cuerpo automático conservaba la calibración/escala previa.
Ahora limpia calibración, reinicia rutas/historia y reemplaza el modelo escalado
con uno sin escala; diagnóstico calibration_required y targets vacíos al estar
pausado. Control positivo: cuerpo explícito estable conserva calibración/modelo
al finalizar y guarda elección por generación. Medición previa no se borra.

10 tests runtime finales pasan (1.16s); 20 evaluación/paridad/continuación pasan
(12.70s) con Shaper explícito. Modelos/contratos/media también pasaron en el recorrido
de regresión (23 tests,4.11s). UI no cambia, evidencia previa de diagnóstico válida.

Auditoría local privada: medio/cache verificados, slot derecho coincidente con
fuentes congeladas en cinco instantes soportados. Se registra esa elección sólo
en desarrollo para medio/cache/generación coincidentes; perfil cotidiano conserva
su propia selección. Preset/calibraciones/última fuente no cambiaron. Sin copiar
video, recalcular tracking ni iniciar servicios. Sólo evidencia de selección
espacial/missingness; no identidad biométrica, precisión de pose, continuidad
anatomía completa, escucha ni aceptación. Hashes/IDs/posiciones quedan locales.

### Calibración · motivo de descarte visible — 2026-10-03

Runtime agrega calibration_notice sólo cuando la elección automática elimina una
calibración activa. No aparece si no había escala; cuerpo explícito estable sigue
sin aviso. Snapshot conserva motivo hasta calibración exitosa, elección manual,
nueva fuente o cierre. 12 tests runtime pasan (1.19s), incluyendo vida del aviso y
la regresión corporal previa; build TypeScript/Vite93 módulos pasa (1.23s).
Web muestra el motivo junto a escala, como estado y sin nuevo control/restricción.
No modelos/ratios/audio/presets modificados ni nuevas pruebas físicas/escucha.
Sin servicios, datos corporales ni cambios al perfil cotidiano.

### R12 · conservar raw excluido sin integrarlo — 2026-10-03

Regresión reproducida antes del fix: HR/potencia metabólica negativos con causa
explícita eran rechazados pese al contrato de conservar raw/exclusiones.
Ahora el mismo canal debe declarar la exclusión; otro canal no habilita la lectura.
Tests verifican valor/cause archivados, entrada intacta, dos intervalos adyacentes
excluidos, media/trabajo/soporte común independientes del raw inválido, y
reapertura/recomputación del archivo. API inspect/guardar/descargar cubiertos.
NaN/Infinity excluidos siguen rechazados; potencia mecánica negativa sigue válida.

`tests/research/test_physiology.py` y `test_physiology_csv.py`: **29 passed (1.79s)**
con SHAPER_DIR/PYTHONPATH del checkout de desarrollo. CSV sin exclusión conserva
su rechazo de HR negativo. No cambios UI ni nuevo recorrido Chrome requerido;
no servicios/dispositivos, datos privados ni aceptación fisiológica/perceptual.

### R12 · cargas demoradas no reemplazan el protocolo actual — 2026-10-03

`physiologyContextNetwork.spec.ts`: **1 Chrome producción passed (3.2s)** con
fixture LaboratoryRuntime/control recorder, SQLite/servicio CSV/mediciones reales.
Tres respuestas HTTP reales retenidas por el test: carga CSV frente a edición,
inspect nativo frente a aplicación CSV, y apertura nativa frente a aplicación CSV.
Edición/protocolo reciente permanece; inspección/apertura obsoleta no publica
resultado guardable; reintentos sin cambio aplican y muestran media esperada.
State preset/source/calibration sin cambios; cero errores JS. Vínculo EVAL comparte
guard de contexto, sin nueva adquisición/revalidación física de sincronía.

Build TypeScript/Vite **93 módulos, 1.30s**. Fixture aislado detenido; sin dispositivos,
video/pose privados ni aceptación humana. No cambios backend ni defaults musicales.

### R12 · sensibilidad temporal con soporte común — 2026-10-03

`test_physiology_sensitivity.py` + R12/CSV: **41 passed (2.08s)**. Deltas declarados
de offset, rate congelado y segundos comunes; original sin mask mantiene resultados,
intersección exacta, gaps/exclusiones/tails, canal extra con soporte propio, orden,
presupuesto, grillas inválidas, API/binding y archivos/reapertura/recomputación
(incluido rechazo de resultado alterado con hash actualizado).

Receta pública r12_clock ejecutada: dos casos × dos corridas, igualdad de resultados
y verificación de manifest por recomputación. HR lineal: 85/80/75 con soporte común;
gap central: nulos con soporte vacío. CLI sobre request archivado también ejecutado.
No sensores/observaciones humanas ni inferencia de sincronía/eficiencia.

Chrome producción: nuevo banco **1 passed (2.9s)**, más regresión de contexto
**1 passed (3.1s)**. API/SQLite/archivos reales; tabla original/pareada, validación,
guardar/export/import, reapertura tras reload y respuesta demorada frente a edición;
preset/source/calibration intactos, cero errores JS. Build94 módulos **1.29s**.
Fixture detenido y puerto cerrado. Sin nuevos dispositivos/medios privados/escucha.

### Integración completa tras #119–138 — 2026-10-03

Cambios acumulados desde la suite en #118 afectan app, launcher, runtime/calibración,
evaluación y bancos. Nueva suite completa `tests`: **1167 passed, 4 subtests passed**,
sin skips/fallos, **283.12 s**. Weaver `76f4228`, Shaper-dev `516ebde`; documentación
editada durante la corrida, sin modificaciones al código probado.

```sh
SHAPER_DIR=../harmonic-shaper-dev PYTHONPATH=src:tests:../harmonic-shaper-dev/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest -q tests --maxfail=5
```

Resultado incluye contratos/modelos/runtime/múltiples cuerpos/calibración/cache,
launcher/audio-control, integración PCM/EVAL/captura y bancos research existentes.
No es la suite de todo Shaper ni un recorrido nuevo de toda la web; recorridos
Chrome/build pertinentes previos siguen válidos porque sólo cambiaron documentos.
Warning de deprecación Starlette/AnyIO en TestClient, sin fallo funcional observado.

Main remotos consultados: Weaver cc5fb57, Shaper f8bfe07, HarMoCAP25fda8d;
Shaper-dev limpio516ebde y Weaver-lab limpio cc5fb57. Último aporte Ani sigue en
#107 f424981, ya incorporado. Sin merges/instalación cotidiana ni dispositivos/
medios privados/escucha. CONTRIBUTING actualiza base de aportes y dependencia
Shaper vigentes; no exige repetir la suite completa para cada cambio.

### Instrumento cotidiano · modelos/referencias/ruteos actuales — 2026-10-03

Recorrido `fullLaboratoryNetwork.spec.ts` ampliado y ejecutado con bundle actual,
FastAPI/WS, LaboratoryRuntime y VideoLibrary reales: **1 Chrome passed (11.3s)**.
Default percepción CPU actual produce la identidad del cache corporal existente;
apertura confirma cache_hit sin copiar video ni recalcular tracking. Fixture con
fuente congelada usa cache original de sólo lectura: un miss falla antes de
escribir/consumir observaciones nuevas. Audio es ControlRecorder, no DAC.

Desde web: selección explícita del slot indicado, avance del video, pause/seek,
calibración medida, presets08–11 y seis targets afinados/no nulos por modelo.
Colectivo cambia a dos componentes sin reducir voces; referencias pelvis/torso/
fixed/camera y exclusión de muñecas se aplican conservando cuerpo/escala/video.
Peso del ruteo de voz1 a cero hace decaer sólo ese target, otras voces permanecen
activas; volver a .75 recupera target sin pausar. Preset portable guarda componentes/
referencia/joints sin identidad/calibración. Cambio de persona y retorno descartan
escala; seek al final/loop mantiene avance. Cero errores JS.

La repetición del fixture encontró nombres de preset duplicados; el test ahora usa
nombre único para seleccionar el registro que acaba de crear. Corrida final pasa.
Manifest/frames del cache original mantienen SHA previo; IDs, poses y datos del
recorrido permanecen locales. Fixture detenido y puerto cerrado. No producción/
defaults musicales modificados ni rebuild necesario (sólo pruebas/documentos).
No se afirma audio efectivo, fase del DAC, latencia física, precisión anatómica ni
aceptación perceptual. Evidencia de escucha01c previa se conserva separadamente.

### Web · respuesta vieja de preset no reemplaza ediciones nuevas — 2026-10-03

Regresión reproducida con API real: preset aplicado en servidor, HTTP demorado,
Master editado y confirmado después; al liberar respuesta antigua el campo volvía
al valor del preset y revision.current retrocedía. Nuevo guard descarta la respuesta
si generation de ediciones cambió o si trae revisión anterior a la confirmada.
No altera controles/defaults, grafo/runtime, audio ni conflictos de otros clientes.

`presetResponseNetwork.spec.ts`: **3 Chrome passed (3.4s)** en producción real con
API/SQLite, reteniendo respuestas HTTP y suspendiendo snapshots WS posteriores
para que no oculten el bug. Casos: edición confirmada, edición con respuesta pendiente,
segundo preset confirmado. El campo conserva el valor correcto y otra edición
PUT usa revisión válida (+1), sin errores JS. Datos sintéticos, sin dispositivos.
El test compara valor numérico para no confundir `.173` con `0.173`; segundo preset
de control tiene master distinto declarado para distinguir ambas respuestas.

Recorrido corporal fullLaboratoryNetwork con bundle nuevo: **1 passed (11.6s)**,
cuatro modelos/seis targets/calibración/componentes/referencias/ruteos/presets/
cambio de cuerpo/loop; cache hit sin retracking, manifest/frames originales intactos.
Build TypeScript/Vite94 módulos **1.31s**. Ambas fixtures detenidas, puerto cerrado.
Sin datos corporales publicados, R24/escucha nueva ni aceptación humana inferida.

### Fuente · cobertura y errores corresponden al job activo — 2026-10-03

Regresiones reproducidas: GET quality del job anterior demorado podía reemplazar
el informe actual; un HTTP503 viejo aparecía como error de la nueva fuente.
Web ahora asocia el informe a jobId y renderiza sólo si coincide con el activo;
cleanup ignora respuestas/errores del contexto abandonado, incluido unmount.
No cambia porcentajes, causas, selección del cuerpo ni backend de calidad.

`sourceQualityContextNetwork.spec.ts` (dos casos) y recorrido corporal completo:
**3 Chrome passed (19.1s)** con producción/API/WS/VideoLibrary/cache reales.
Primer informe retenido, reapertura crea nuevo job cache hit, segundo informe
visible; liberar éxito/503 anterior conserva segundo informe sin error viejo.
Captions agregadas por el test distinguen respuestas; números de cobertura no
modificados y no se usan como evidencia de precisión anatómica. Fixture congelada
ahora calcula coverage desde frames existentes al precargar job ready, igual que
la biblioteca; evita un quality=null artificial del bootstrap previo.

Bundle nuevo mantiene cuatro modelos/seis targets/controles/ruteos/calibración/
presets/cambios de cuerpo/loop; cero errores JS. Build94 módulos **1.22s**.
Cache original manifest/frames intactos; sin copias ni retracking. Fixtures
detenidas, puerto cerrado, medios/IDs/poses/resultados corporales locales. Sin
defaults/audio modificados, R24 física, escucha ni aceptación nuevas.

### Inventarios web · conservar la consulta más reciente — 2026-10-03

Dos regresiones reproducidas en producción/API/SQLite reales: retener el GET
inicial de presets, guardar uno nuevo y completar su refresh; liberar el GET viejo
ocultaba el preset confirmado. Liberarlo como HTTP503 mostraba un error obsoleto.
Ambos casos pasan tras proteger cada inventario por número de petición:
**2 Chrome passed (2.2s)**. Biblioteca, presets y calibraciones usan el mismo
mecanismo; consultas distintas no se invalidan entre sí. Errores de la petición
vigente siguen propagándose; sólo se descartan respuestas/errores anteriores.
Cleanup invalida lecturas pendientes al desmontar. No cambia backend ni defaults.
Build TypeScript/Vite94 módulos **1.30s**.

El primer recorrido corporal detectó una condición separada: aplicar dos presets
sin esperar confirmación puede rechazar el segundo con conflicto de revisión.
Un segundo recorrido sin modificación pasó; la prueba ahora espera el nombre
confirmado en el placeholder antes de aplicar otro preset, sin sleeps ni reintentos
que oculten el conflicto. Ese solapamiento queda pendiente; la protección de
inventarios no pretende resolver concurrencia de escrituras.

Recorrido corporal con confirmación secuencial explícita: **1 Chrome passed
(11.9s)**; video cache hit, cuatro modelos, seis targets, calibración, componentes,
referencias/joints, ruteos y presets portables, cambio de cuerpo/loop. Cache original
manifest/frames intactos; fixture detenida y puerto cerrado. Sólo targets de
control, sin síntesis/R24/escucha/aceptación nuevas; datos corporales locales.

### Presets · elecciones rápidas con una aplicación en curso — 2026-10-03

Para resolver el conflicto de aplicaciones solapadas registrado en #143, la web
mantiene una sola solicitud apply en curso y una última elección pendiente. Tras
confirmar la primera, la siguiente usa la revisión confirmada, sin GET correctivo
ni retry de escrituras. Una edición posterior descarta la elección anterior;
un error detiene la cola y permanece visible. Presets siguen elegibles mientras
se espera apply y un status muestra la elección pendiente; no se pausa la fuente.

Regresión nueva falla antes (envía las tres elecciones mientras la primera está
retenida) y pasa después (sólo primera y última, revisión final +2, WS posterior
retenido para no encubrir revisión vieja). Casos adicionales: edición confirmada
cancela elección pendiente y HTTP409 explícito no dispara esa elección ni retry.
Se conservan las tres regresiones de HTTP tardío con ediciones confirmadas/
pendientes; segundo preset ahora se confirma tras liberar la primera respuesta,
según el contrato de serialización. **6 Chrome passed (5.8s)** contra API/SQLite
reales; TypeScript/Vite94 módulos **1.35s**. No backend/defaults/audio modificados.

Recorrido corporal completo con bundle nuevo: **1 Chrome passed (11.9s)**;
video cache hit, calibración, cuatro modelos/seis targets, ruteos, referencias/
componentes/joints, preset portable y cambios de cuerpo/loop. Cache original
manifest/frames intactos; fixtures detenidas, puerto cerrado. Targets solamente,
sin abrir R24 ni validar escucha/aceptación humana. Medios/poses/resultados locales.

### R13 · dos recordings corporales congelados, reserva por toma — 2026-10-03

Usadas dos grabaciones ya evaluadas, individual y dúo; selección del cuerpo a la
derecha en dúo conservada del snapshot explícito anterior. Dos segmentos train
no solapados del primer archivo y test del segundo. No copia ni lectura de video,
tracking nuevo, calibración inferida/transferida o identidad biométrica atribuida.
Adapter productivo HeldoutService.freeze/EvaluationService verifica traces y
conserva IDs/unidades/contextos. Seis zone-speed ordenadas; igualdad de configuración
baseline comprobada antes de puntuar. Misma unidad nominal no prueba misma escala
anatómica/perspectiva. Los grupos se declaran sin identidad establecida.

Parámetros fijados antes del score: historia2, horizonte6 muestras, componentes2,
ridge0.1, z-score train-only, shuffle train semilla17 y control cuadrático. Condiciones
prefijo0 y prefijo60, con train+prefijo sólo para modelos adicionales. Pesos/scaler/
base originales congelados. Comparación de ambas condiciones recortada a intersección
de pares (secuencia, origen, objetivo); no compara medias de soportes distintos.
Cada condición ejecutada dos veces con outputs idénticos en este entorno y
recomputación integral de request/result/predictions. Todos los números, features,
IDs/hashes/resultados corporales y receta concreta permanecen sólo locales.

`heldoutFrozenRecordingsNetwork.spec.ts`: **2 Chrome passed (17.2s)** con producción,
import JSON nativo, API y workers reales, descarga y repetición de ambos experiments.
Comparación de modelos/resultados numéricos con ejecución CLI local; requests
almacenados iguales en valores, binding digest→manifest comprobado por separado.
Import JS normaliza float/int de metadata (p.ej.0.0→0); recorrido inicial detectó
únicamente esa diferencia de digest. Comparación recursiva confirmó valores
idénticos y cambios de tipo sólo float/int. No se exige hash CLI=browser; sí igualdad
de outputs al repetir cada request congelado dentro del mismo entorno.

Preset/revisión del instrumento permanecen iguales antes/después del banco;
cero errores JS. Caches seleccionados originales intactos; fixture detenida y
puerto cerrado. Sin modificación productiva/build nuevo necesarios: bundle
verificado de #144 reutilizado. Sin R24, escucha, aceptación ni captura física.
Esta reserva contrasta recordings; no demuestra generalización entre sujetos,
eficiencia/causalidad/HIT, equivalencia de escalas o mejora perceptual.

### R13 · comparador de corridas guardadas sobre soporte común — 2026-10-03

Nuevo núcleo/API/web read-only intersecta pares (secuencia,origen,objetivo) entre
2–6 corridas con iguales inputs/contexto/reserva y settings variables. MSE calculado
desde predicción/target; delta pareado frente a primera para métodos compartidos.
Muestra elegibles/excluidos, soporte explícito, settings y procedencia; descarga
JSON. Sin soporte null, métodos ausentes sin delta. No matching aproximado, refit,
imputación ni transferencia de cuerpo/escala. Hashes verificados antes/después;
comparación registra código/entorno actual separado de inputs históricos.

**23 R13 tests passed (3.52s)**: prefijo con deriva de amplitud revela diferencia
entre media individual/pareada;149 pares,29 excluidos de178. Horizontes1/2 sin
pares; unidades/features/contextos/objetivos diferentes rechazados; IDs acotados,
artefacto alterado rechazado y regresiones originales de train-only/adaptación/
shuffle/workers. Shaper-dev seleccionado explícitamente para la integración PCM;
la deriva de amplitud del control evita una media constante trivial.

**4 Chrome passed (8.6s)** con producción/API/workers reales: comparación prefijos,
soporte vacío, contextos incompatibles (HTTP422 visible, sin tabla), descarga,
cambio de selección invalida tabla; preset/revisión live intactos. Incluye recorrido
R13 productivo anterior. Bundle94 módulos TypeScript/Vite **1.22s**.

Receta pública sintética ejecutada, lectura repetida idéntica, evidencia publicada
sin datos corporales. Nuevo núcleo también reproduce, con tolerancia numérica
1e-12, soporte/scores pareados calculados localmente en #145; ese informe queda
privado. Fixture detenida, puerto cerrado. Sin defaults/audio, dispositivos físicos,
escucha/aceptación nueva ni conclusión de generalización/HIT.

### LAB-09 · sincronía del estímulo en MKV decodificado — 2026-10-03

Se añade la comprobación explícita de sincronía digital pedida por #17: flash en
video y pulso PCM conocidos, medidos tras codificación/mux, no sólo duraciones.
Callbacks con salto10→12s, archivo PCM continuo, timeline/epoch explícitos. Tres
offsets0/+0.1/−0.1: flash0.5/0.4/0.6s y pulso0.5s constante, según PTS FFprobe y
PCM FFmpeg. Source/timeline/PCM originales intactos; PCM exportado idéntico.

**33 capture/export/timeline tests passed (5.03s)**, incluidos tres estímulos,
API/integridad/rangos/cancelación/publicación interrumpida existentes. Sólo warning
de deprecación Starlette/AnyIO. Receta pública ejecutada dos veces por offset,
mediciones iguales; evidencia sintética publicada. Sin cambios de producción,
build/UI/defaults/audio ni servicios/hardware iniciados. Bundle anterior válido.

El control usa20fps (50ms por frame) y PCM48000Hz; posiciones digitales exactas no
miden error de cámara/pose/DAC/pantalla/acústica. No verifica AAC preview, sensación
humana ni identidad con sonido escuchado; la evidencia previa del tap post-limiter
permanece separada. Sin medios/resultados privados ni nuevas inferencias de HIT.

### LAB-09 · AAC preview y decodificador Chrome — 2026-10-03

**38 capture/export/timeline tests passed (6.90s)**, incluidos5 controles nuevos:
AAC64/192/320kbps y offsets±100ms a192kbps. Pico/centro de energía en ventana fija
100ms del transiente conocido, tolerancia2ms; flash con PTS esperado y PCM principal
exacto. Esta tolerancia pertenece a esta fixture, no al error del códec en general.
Receta pública ejecutada dos veces por condición, mediciones iguales y entorno
registrado; sólo video/PCM sintéticos. Warning Starlette/AnyIO ya conocido.

**3 Chrome passed (3.5s)**: decodificación de AAC64/192/320 mediante OfflineAudioContext,
centro/pico dentro de tolerancia, video HTML muted/pause al terminar y flash real
observado con requestVideoFrameCallback/mediaTime0.5s. Página mínima interceptada
por Playwright sirve bytes del MP4 real; no es un recorrido completo del player
productivo. La prueba usa frames presentados durante playback, sin tratar seeked
como confirmación de repaint. Sin AudioContext realtime/salida sonora solicitada.

No cambios de producción/UI/defaults/audio, build nuevo ni servicios iniciados;
bundle anterior sigue válido. Sin medios/datos corporales, R24 física, latencia
acústica/display/cámara, escucha o aceptación humana nuevas. AAC sigue siendo
lossy con padding posible; no reemplaza el MKV exacto ni mide sincronía física.

### EVAL · cambio de cuerpo descarta calibración del segmento — 2026-10-03

Regresión reproducida: cambiar person_id ocultaba la opción de calibración anterior
pero conservaba calibration_id en el POST. El backend ya rechaza ese cruce; UI ahora
limpia sólo el segmento modificado y explica que debe elegirse escala del nuevo
cuerpo. Editar límites temporales no descarta una escala válida; copiar un segmento
del mismo cuerpo conserva su selección. Sin cambios de backend, medidas o defaults.

**2 Chrome passed (2.3s)**; ambos fallan antes en calibration_id viejo (original y
segmento copiado). Bundle productivo/API de fixture, inventarios de fuente/escala
sintéticos y POST EVAL interceptado: comprueba payload/selección, no escala corporal
medida ni una evaluación real. Otra copia queda intacta; selección nueva explícita
y edición de inicio conservan nueva escala. TypeScript/Vite94 módulos **1.31s**.
Fixture detenida; sin datos corporales, síntesis/R24/escucha ni aceptación nuevas.

### R01/R02 · geometría colectiva visible durante exploración — 2026-10-03

UI consume diagnostics.collective existente: base/proyector/amplitudes/residuo/
ángulos, soporte nombrado y JSON. Colores fijos[-1,+1], recorte visual explícito;
no nuevo cálculo ni estimación de posición3D. Dos campos visuales portables,
default off/12 ejes. Baseline no expone geometría, falta de soporte no fabrica matriz.

**44 pruebas backend passed (15.93s)**: runtime, contratos/store, colectivo y
evaluación; edición visual en el mismo instante conserva objeto del modelo,
historial y targets exactos. **4 casos adicionales** rechazan vistas/tamaños
inválidos (suite contratos10 passed0.19s). Warning Starlette/AnyIO existente.

**1 Chrome passed (11.4s)**, recorrido productivo completo sobre cache corporal
privado read-only: cuatro modelos, seis targets afinados, cuerpo/calibración,
fuente en movimiento, proyector recortado8 ejes, pixel contrastado contra valor
observado, base2 columnas independiente de6 voces, save/apply preset conservando
vista/límite, apagado elimina panel; continúa verificando ruteo/persona/loop.
Fixture ControlRecorder, no síntesis ni dispositivo. TypeScript/Vite95 módulos
**1.28s**; recompilación de formato cambia bundle pero no comportamiento.

Cache original SHA verificado sin cambios; fixture detenido/puerto cerrado.
Sin video nuevo, inferencia, datos corporales publicados, R24, escucha o aceptación
humana nuevas. No demuestra HIT/positividad/KP ni resuelve investigación R01/R02.

### R01 · comparación de corridas archivadas — 2026-10-03

API/UI de2–6 corridas con inputs/clock/unidades/transformaciones iguales,
soporte objetivo u origen-objetivo explícito. Cada control/familia común se
puntúa sobre su intersección exacta; conserva orígenes, exclusiones y procedencia.
No refit, aproximación de timestamps, relleno de gaps ni cambios live. Corridas
sin origen archivado tienen rechazo explícito. Valores de request se normalizan
por contrato para resolver rechazo espurio0/0.0; diferencias reales se rechazan.

**49 pruebas R01/backend passed (11.32s)**: comparación nueva, geometría/
predicción/familias y snapshots corporales. Caso nuevo histórico de defaults/
origen ausente verificado en suite comparador **12 passed (3.65s)**. Prueban
lectura sin mutación, errores archivados sobre soporte común, horizontes con/
sin pares, ausencia de familias, inputs/reloj distintos, artefactos alterados,
IDs, cuerpo con gaps, HTTP y request tipado. Warning Starlette/AnyIO existente.

**2 Chrome passed (4.1s)**, bundle productivo/API real y tres corridas sintéticas
archivadas: pares vacíos entre horizontes1/6, objetivos comunes al cambiar soporte,
orígenes diferentes conservados, download JSON, limpieza al cambiar selección,
422 por inputs distintos y preset/revisión live intactos. TypeScript/Vite96 módulos
**1.78s**. Fixture sólo controles, ningún dispositivo; detenido/puerto cerrado.

Receta saved_comparison_controls.py: tres condiciones, cada una ejecutada dos
veces; comparación read-only repetida, controles numéricos y traces idénticos en
el entorno registrado. Evidencia sintética pública en r01_grassmann.
Cuatro corridas corporales históricas existentes comparadas read-only localmente
sobre soporte observado; informe repetido idéntico y hashes originales conservados.
Informe/IDs/resultados corporales quedan locales; ninguna nueva inferencia, toma,
R24, escucha/aceptación humana ni validación HIT/generalización.

### R03 · centros/señales candidatos sobre soporte común — 2026-10-03

Comparador web/API read-only de2–6 corridas R03 completas: mismo corte de marcas,
cuerpo/generación/contexto, cobertura declarada, tolerancia y offset. Intersecta
soportes y usa compare_events sobre todos los candidatos originales, sin repetir
extracción. Preserva scores disponibles y pareados, unidades/umbrales, candidatos
y procedencia. Nuevos manifests añaden resumen de señal/crop/conteo para elegir.

**45 backend/temporal passed (2.26s)**: comparación, worker/archive/lifecycle, API,
matching y sensibilidad temporal. Conservación byte-a-byte de archivos, igualdad
de marcas elegibles pese a cobertura distinta, precisión1/.5 sobre mismos eventos
anotados, soporte disjunto sin score, cambios de matching/coverage rechazados,
artefactos alterados e IDs inválidos. Warning Starlette/AnyIO conocido.

**2 Chrome passed (3.0s)**: bundle/API productivos con tres archivos sintéticos;
soporte0.4s, denominadores iguales y originales distintos, señal/unidad, caso
sin intersección con score null, download JSON, limpieza de selección y estado
live/preset/revisión intactos. TypeScript/Vite97 módulos **1.38s**.

Receta r03_centers/controls.py y evidencia sintética pública: matching repetido
idéntico en dos archivos nuevos por condición. Marcas/señales/identidades son
sintéticas; no cuerpo real, anotaciones humanas, pose nueva, R24/cámara, síntesis
o escucha/aceptación. No ranking causal de centros ni validación Jpsh/HIT.

### Vista Performance — 2026-10-05

Tres pruebas Chrome sobre el bundle productivo, con HTTP/WebSocket sintéticos
interceptados: cambiar de vista conserva la fuente montada y el reloj avanzando
sin escrituras; controles/macros, persona, guardado portable y marca explícita;
persistencia visual y avisos de calibración/audio. TypeScript/Vite build pasa.
No se modificó la sesión de Nicolás. Estas pruebas verifican el recorrido de UI;
la escucha y comodidad de esta vista con movimiento real quedan para su uso.

### Modelos con suavizado HarMoCAP y actividad por voz — 2026-10-05

Replay local del clip actual entre 2–60 s, cinco presets de referencia (sostenido,
local, relacional, angular y colectivo), misma persona/calibración medida y
parámetros de tracking de la sesión. Los cinco produjeron targets activos y cada
una de sus seis voces tuvo actividad. Solicitud, manifest y traces privados en
`~/.local/share/harmonic-weaver/laboratory/checks/models-20261005/`.
Esto descarta silencio total en esa corrida; no verifica escucha, calidad de pose,
clicks ni preferencia perceptual en los otros modelos. La sesión live no se editó.

Se añade resumen por voz al comparador para que el indicador global no esconda
voces apagadas. Prueba sintética con una voz muteada y otras activas contrasta
fracciones/medias/picos con los traces; los informes previos no se modifican.
Verificación de esta ampliación: 40 tests de evaluación/packages/profiles pasan;
TypeScript/Vite build pasa. No se abrieron dispositivos ni se generó escucha.

### Predicción después de perder una articulación — 2026-10-05

Caso sintético reproducido: al recuperar una cadera desplazada tras un cuadro
missing, su velocidad era inválida pero `velocity_error` comparaba contra la
trayectoria anterior al hueco (≈10 longitudes de torso). El ruteo local podía
convertir ese salto de reacquisición en sonido. Se exige soporte continuo por
articulación para errores de posición/predicción; missing/held/omitted reinician
esa historia, sin descartar la de articulaciones todavía observadas. La predicción
vuelve tras reunir historia nueva. El filtro bounded descarta también articulaciones
omitidas, sin rellenarlas al recuperar.

55 tests de filtros/modelos/colectivo/evaluación pasan. Otros 18 tests de recuperación
y runtime pasan, incluida integración local→ruteo: la cadera recuperada no activa
su voz y las voces con soporte válido siguen funcionando. No cambian controles,
ratios, síntesis ni cache. No se atribuye esta corrección al click que Nicolás ya
había dejado de escuchar; no se hizo una nueva escucha ni se reinició su sesión.
Los 8 tests de PCM cross-repo pasan con el checkout Shaper actual añadido a
PYTHONPATH: repetibilidad, paridad de targets/render, bloque causal y procedencia.
