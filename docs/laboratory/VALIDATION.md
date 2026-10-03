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
