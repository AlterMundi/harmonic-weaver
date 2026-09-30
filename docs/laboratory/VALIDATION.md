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
