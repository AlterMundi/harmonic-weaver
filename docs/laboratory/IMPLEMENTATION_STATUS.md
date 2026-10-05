# Estado actual del laboratorio

Actualizado 2026-10-05. Este mapa describe el checkout consolidado; el historial
al final conserva los cortes anteriores. Las menciones históricas de ramas,
carpetas `-dev` y trabajo sin instalar no describen la instalación actual.

## Instalación y evidencia reciente

Una instalación: `~/Projects/harmonic-weaver`, web 8765 y Shaper 8085.
Base consultada: Weaver `bd4a0a8`; cortes recientes agregan el origen Shaper para
R07, diagnóstico por voz, salida/buffer web, continuidad opcional de caderas y
reproductor CUDA acotado sin cache. Heads adyacentes consultados: Shaper `dcebaf8`,
HarMoCAP `25fda8d`. No hay PRs de laboratorio abiertas; permanece la PR histórica
#2 de beat envelope, fuera de estas entregas. Los cambios de backend recientes
cargan en el próximo arranque normal; se conservó la sesión que Nicolás escuchó,
pausada, con su preset y calibración intactos.

[Arranque y recorrido](RUNNING.md) · [pruebas y límites](VALIDATION.md) ·
[comparador](EVALUATION.md) · [tracking y futuras alternativas 3D](TRACKING.md).

Nicolás informó ausencia de clicks en la prueba actual de 20 s. Eso es escucha
real de ese recorrido, no aceptación de todos los modelos ni identificación de
la causa. Replay posterior de cinco referencias con tracking suavizado y escala
medida produjo targets activos en las seis voces de cada modelo, incluido
colectivo. Datos y resultados corporales permanecen privados.

## Entregas disponibles

| Entrega | Disponible en main | Verificación y siguiente dependencia concreta |
|---|---|---|
| LAB-00/01 | Baseline preservado/integrado; contratos, presets portables, revisiones, macros, undo/redo y marcas | Inventario original en BASELINE_INVENTORY; pruebas de contratos/store. Sin medios corporales publicados |
| LAB-02 | Biblioteca, archivo/cámara, cache persistente por contenido, generaciones, forzado/CPU explícitos y loop del prefijo fijo | Pruebas cache/percepción/transporte/API; CUDA intermitente conserva causa abierta en #31 |
| LAB-03/06/07 | Runtime causal, matriz editable, seis voces, modelos baseline/local/relacional/angular/colectivo y centros múltiples | Pruebas modelos/ruteo/replay; recuperación por articulación corregida. Escucha de los otros modelos con filtros actuales pendiente |
| LAB-04/05 | Figura de todos los osciladores efectivos, controles completos, presets y Performance | Pruebas de figura/UI; Performance conserva fuente al alternar. Comodidad con uso corporal nuevo pendiente |
| LAB-08 | Launcher único, errores/recuperación y diagnóstico visible de modelo/audio/calibración | Pruebas de integración y evidencia local previa; latencia física y recorrido humano completo pendientes |
| LAB-09 | Captura opcional PCM/journal/video, export MKV/MP4/preview, figura/esqueleto y recuperación de prefijos | Controles digitales de sincronía y pruebas export/cancelación; cámara/sincronía físicas pendientes |
| EVAL | Núcleo causal compartido, reloj/preroll, PCM offline, presets×segmentos, manifests, soporte común y reproductor | Pruebas de paridad/repetición, resultados privados; nuevo detalle de actividad por voz. No estima eficacia corporal |

Cambios recientes que se pueden probar: Performance, recuperación explícita de
escala desde el inspector, fijar persona automática sin perder calibración,
loop del prefijo, filtro One-Euro nativo, invalidación de predicción tras pérdida
de articulación, diagnóstico por voz/dependencias efectivas y diagnóstico pasivo
de underflows. No cambiaron defaults
sonoros en estos últimos cortes. [Recorrido](RUNNING.md).

## Investigación: herramientas y lo que falta observar

Cada fila enlaza el banco y su protocolo/evidencia, sin sustituirlos por esta tabla.
Los controles sintéticos son pruebas del mecanismo declarado. Reservar muestras,
roles o etiquetas en un contrato no equivale a haber realizado el experimento.

| Línea | Herramienta disponible / entrada | Próxima observación o decisión necesaria |
|---|---|---|
| [R01](../../research/laboratory/r01_grassmann/README.md) | Subespacios/forecasts causales, familias declaradas, controles temporales, horizontes y comparación de corridas | Predicción específica que distinga HIT y tomas reservadas; familias adicionales deben responder a esa pregunta |
| R02 | Organización colectiva live, geometría de base/proyector, retardos e indicadores locales/colectivos | Comparación corporal sobre tomas comunes y calidad de pose; no inferir organización física de PCA |
| [R03](../../research/laboratory/r03_centers/README.md) | Marcas tipadas, candidatos regionales y matching/comparación sobre soporte común | Marcas humanas nuevas, incertidumbre temporal y centros alternativos; precedencia no establece causalidad |
| [R04](../../research/laboratory/r04_relational/README.md) | Interferencia Anni/Sai, banco de controles y snapshots EVAL | Referencia/observable definidos y contrastes en tomas reservadas; no validar HIT con I local |
| [R05](../../research/laboratory/r05_resonators/README.md) | Resonadores configurables y excitación congelada desde EVAL, renders/bancos | Escucha comparada y calibración de niveles/latencia; el medio añade su propia organización |
| [R06](../../research/laboratory/r06_activation/README.md) | Calendarios racional/phi/otras perturbaciones, controles de dosis/espectro/shifts y manifests | Observable discriminante y medio/ensayo físico; el nombre phi no demuestra una ventaja |
| [R07](../../research/laboratory/r07_membrane/README.md) | R05 o EVAL/Shaper PCM→membrana teórica, reducción estéreo explícita, campos/RMS, controles directos y decoder de atributos reservados con recuperación de casos | Primer contraste entre dos archivos corporales distintos ejecutado/repetido; más tomas/personas y adquisición independiente por establecer; actuador/medio/observación calibrados para cymatics físico |
| [R08](../../research/laboratory/r08_rope/README.md) | Lectura de frames, anotación/máscaras, flujo/trayectorias, benchmarks y overlays | Referencias manuales de cuerda en clips reales; cruces 2D no son nudos 3D |
| [R09](../../research/laboratory/r09_spatial/README.md) | Streams espaciales, adapter HarMoCAP, clocks afines, comparación y DLT multivista | Cámaras/sensores, calibración y anchors medidos; profundidad inferida conserva su condición |
| [R10](../../research/laboratory/r10_experience/README.md) | Protocolos, player/transportes, respuestas/pares/análisis y borradores recuperables | Participantes, practicante/observador, exposición y respuestas reales; niveles/sincronía físicos |
| [R11](../../research/laboratory/r11_neuro/README.md) | Streams/CSV archivados, SNR sintético/observaciones y clocks declarados | Inventario OpenBCI, canales/referencia/unidades, adquisición y sincronización medidos |
| [R12](../../research/laboratory/R12_MEASUREMENT_PROTOCOL.md) | Mediciones/tarea, imports CSV y sensibilidad a clocks; potencia medida integrable | Instrumentación/participantes y definición de trabajo útil; HR no se convierte en eficiencia/calorías |
| [R13](../../research/laboratory/R13_TRANSFER_PROTOCOL.md) | Reservas por recording, normalización train-only, adaptación prefijo, controles y comparación pareada | Nuevas personas/tareas, equivalencias funcionales e intervenciones; beneficio/prótesis necesita diseño propio |

[Agenda completa](../../research/laboratory/AGENDA.md) conserva las preguntas del
hilo y sus fuentes. Los aportes #36/#97/#107 están integrados; el territorio del
bridge de Oliva conserva su separación y autoría. No se inicia contacto autónomo.

## Continuación

Diagnóstico CUDA acotado disponible por comando, sin escribir/invalidatear cache:
worker productivo en proceso nuevo, prefijo y dispositivo explícitos, comparación
normal/síncrona, etapa/frame/traceback locales. Además de los prefijos de 240 frames, el minuto actual completo (1.800 cuadros)
y el fragmento histórico de espalda (360 cuadros, normal/síncrono) completaron
en CUDA. Checkpoint/extractor coinciden con los manifests históricos de espalda;
no se reprodujo el error ni se determinó su causa.
CPU cotidiana intacta. Comando y límites en RUNNING/VALIDATION; #31 sigue abierto.

One-Euro incorpora corrección opcional de continuidad de etiquetas de caderas
antes de suavizar. Apagada por defecto, portable y sin mediana/límite añadido;
replay del cache corporal produjo correcciones con las demás articulaciones
idénticas. Puede confundir giros reales: requiere inspección/escucha, no se afirma
exactitud anatómica. Sesión cotidiana y defaults conservados.

Salida/buffer/frecuencia configurables desde el inspector, con pausa obligatoria,
validación previa, recuperación del stream anterior y revisión de configuración.
JACK distingue frecuencia solicitada y efectiva. Ajustes de sesión, separados del
preset portable; requieren el próximo arranque normal de Weaver y Shaper para
cargar las API nuevas. No se modificó la R24 ni se reanudó la fuente en esta entrega.

Prioridad cotidiana: escuchar los otros modelos con tracking suavizado, probar
Performance y reportar fallos concretos. La primera corrida corporal R07 dentro
de una toma, con reserva temporal y targets EVAL explícitos, quedó ejecutada y repetida
el 2026-10-05; resultados privados, receta en el banco R07. El origen EVAL/Shaper
está disponible en web/API y receta local, con labels/offset. Su primera corrida
corporal usa PCM post-Shaper a 48 kHz, con features/targets idénticos a EVAL sin PCM.
Dataset/readout repetidos y contraparte R05 comparada en soporte/medio/muestreo común.
El contraste R07 posterior reserva otro archivo corporal para test, con escala
guardada por fuente/persona y preset común; tres ventanas train y dos test,
repetidas con resultados idénticos. Esto amplía el soporte fuera de un archivo,
pero dos casos test no prueban generalización ni adquisición independiente.
La siguiente evidencia de generalización necesita más tomas/personas independientes;
la escucha humana y el contraste físico no se dan por realizados.
#77 completó su entrega técnica: eventos OSC v2 por slot, relojes separados,
ingreso parcial y consumo sin muestras duplicadas, con selección explícita en
el harness histórico. Los productores adicionales y la sincronía física
permanecen como extensiones de R09; no bloquean esa entrega ni cambian el
transporte PyAV del laboratorio cotidiano.
La causa CUDA y las mediciones físicas siguen abiertas. No se declara terminado
el roadmap ni validadas sus hipótesis al entregar herramientas.

<details>
<summary>Historial de implementación anterior a este mapa</summary>

> 2026-10-04: integración continua en `main` hasta #152, Shaper #7 y HarMoCAP #1.
> Instalación única: `~/Projects/harmonic-weaver`, web 8765 y Shaper 8085.
> Las menciones históricas de pila separada/no instalada quedan superadas.

# Implementación: estado comprobado

2026-09-29. Segunda iteración local y primer comparador disponibles para feedback.
La aceptación anterior de 01c/contraste se conserva; la escucha de realce ×10,
articulación y modelos nuevos sigue pendiente. [Evidencia y límites](VALIDATION.md).

## Estado vigente (auditoría 2026-10-03)

La historia fechada de abajo conserva evidencia de cada corte; sus pendientes
pueden estar resueltos por entregas posteriores. Esta tabla separa software,
instalación cotidiana y trabajo físico/humano pendiente.

Integración backend actual: **1167 tests + 4 subtests passed**, 283.12 s, sobre
Weaver `76f4228` y Shaper-dev `516ebde`. Suite completa sin fallos/skips; evidencia
de contratos/runtime/cache/render/bancos, no de escucha, hardware o hipótesis HIT.
Los recorridos Chrome recientes siguen documentados por entrega en VALIDATION;
no se atribuye esta cifra a toda la UI ni a adquisición física.

| Entrega | Evidencia / alcance actual | Pendiente concreto |
|---|---|---|
| LAB-00–08 | Instrumento, seis voces iniciales, presets, modelos/calibración, múltiples cuerpos, biblioteca/cache y transporte en main hasta #85; experiencia baseline aceptada. #86–89 añaden observaciones parciales y derivadas con reloj de captura | Feedback de modelos/calibración/realce, calidad y latencia físicas; CUDA no se declara reparado; nueva pila aún no instalada |
| Comparador #18 | Motor PCM causal compartido, manifests/features/targets, video/WAV/suma de voces y selector de presets al mismo instante. Recorrido corporal con tres renders y Chrome muted registrado en EVALUATION.md | Escucha y sincronía físicas; familias/métricas científicas adicionales y reservas independientes |
| LAB-09 #17 | Captura PCM/journal/video opt-in, export MKV/MP4/preview web, inventario y recuperación de prefijos con procedencia; #103 + Shaper #7 agregan polling persistido. Nuevas ramas añaden esqueleto observado y figura de todos los osciladores desde bloques PCM en export completa/recuperada, con causas de omisión; perfiles portables capture/export con nombre, SQLite y JSON; estímulo digital flash/PCM medido en MKV decodificado verifica offset y salto del reloj de callbacks | Nueva pila aún no instalada; cámara/sincronía medidas y feedback humano |
| R01 | Subespacios y forecasts causales, controles pareados/horizontes; entradas EVAL congeladas y repetición corporal local. Nuevas ramas añaden tendencia, ridge con retardos completo/subespacio y armónicos declarados con causas de soporte/reloj; controles web/JSON y bancos sintéticos reproducidos | Otras familias y splits/tomas reservados; predicción HIT específica; nueva pila aún no instalada |
| R02 | Modelos local/relacional/angular/colectivo y centros variables en instrumento/EVAL; banco Sai #36/#97 integrado en #98, web sintética #100 y Fourier corporal #107 incorporado y nuevo consumidor biblioteca/worker/API/UI con cobertura/diagnóstico geométrico | Contrastes corporales entre tomas/cuerpos; Contraste geométrico restringido reservado a Oliva; no inferir organización de compresión sola |
| R03 | Marcas tipadas/contexto/época, filtros y snapshots; candidatos causales y contraste temporal con soporte común, barrido declarado de offset global, worker/API/UI | Marcas humanas nuevas y su incertidumbre temporal; centros/regiones alternativos y reservas; coincidencia no demuestra intención |
| R04 | Banco relacional sintético/pose congelada, controles proximal/noise, soporte común y summaries; API/UI y repetición HTTP | Anotación/tarea y otras tomas independientes; ruido de cámara medido |
| R05 | Resonadores/excitación y mapeo, PCM/campos de voces, player/source/offset/overlay causal; referencias y recuperación de publicaciones parciales | Escucha/agencia y niveles/latencias físicas; otras variantes/medios y crash del host |
| R06 | Calendarios/medios/semillas, fases y sondas; #101 añade circular shifts por puerto con potencias conservadas, checks FFT y tabla/traza web | Controles más amplios, observable/hipótesis HIT y ensayo físico/humano; espectro periódico de entrada no fija respuesta finita |
| R07 | Membrana sound-only/campos/RMS y controles de medio/resolución/transientes. #94–96: lectura histórica, readout reservado, labels EVAL; corrida corporal local 5 train +5 test, repetición byte-idéntica | Tomas/cuerpos independientes y controles ampliados; medio físico/calibración/sensores, escucha/aceptación; una toma no prueba generalización |
| R08 | Anotación/segmentación/flow/bancos pareados con soporte, causas/coverage, archivos y UI; recuperación de POST perdida | Calidad manual/ground truth corporal y referencias de cuerda; 2D no certifica topología 3D |
| R09 | Imports/recibos/clocks, comparación/conversiones y presets; DLT de pares declarados con workers recuperables y procedencia conservada en comparador (#121–124) | Adquisición/undistorsión, cámaras/IMUs reales y escala/calibración/sincronización/referencia independientes |
| R10 | Protocolos/condiciones, transporte/player, respuestas/paired analysis/diseños portables; borrador/cierre recuperables y archivo local opcional entre pestañas | Participantes, niveles/sincronía/exposición medidas, sesiones largas y aceptación; datos sintéticos no son experiencia humana |
| R11 | Stream crudo, control SNR conocido archivado (#90), import CSV explícito (#91); #99 conserva original/mapeo/conversión y recuperación web; CSV ISO con origen explícito compartido con R12 | Export/hardware OpenBCI reales, adquisición y sincronía físicas; no índice de placer/estado mental |
| R12 | Mediciones/tarea declaradas, soporte/gaps, integral parcial W→J, vínculo EVAL, archivos, CSV numérico/ISO y configuración portable; #136–138 conservan raw excluido, contexto de cargas y sensibilidad de reloj sobre soporte común con receta pública | Export sensor real y clocks, BLE/RR/adquisición, fuerzas/escala o metabolismo apropiados; no calorías desde HR/pose |
| R13 | Banco nativo/EVAL, splits y normalización train-only, baselines/shuffle y adaptación de prefijo; #130 añade control cuadrático opcional con positivos y negativos sintéticos; reserva corporal entre dos recordings congelados (train-only, prefijo0/60, soporte común), CLI/recomputación y dos recorridos Chrome de import/repeat verificados localmente; worker/API/UI y protocolo | Tomas adicionales/participantes/tareas, mapeos funcionales, validación externa y diseños de intervención/retención |

GitHub main Weaver sigue en `cc5fb57`, Shaper en `f8bfe07` y HarMoCAP en
`25fda8d` (heads remotos consultados nuevamente el 2026-10-03). La pila posterior
a #85 permanece abierta y llega a #138 (`feat/r12-clock-sensitivity`, `76f4228`).
#36/#97 están incorporadas conservando autoría en #98 y #107 en #109, sin mergear
sus ramas históricas. La rama de integración hereda todos esos cortes.
El laboratorio cotidiano `harmonic-weaver-lab` sigue en `cc5fb57`; desarrollo
permanece en `harmonic-weaver-dev`. No se sustituyó el entorno de prueba habitual
ni se publicaron datos privados. Workspaces originales, incluido HarMoCAP con
cambios locales, permanecen preservados.

[Verificación y límites](VALIDATION.md), [arranque/recorridos](RUNNING.md),
[agenda completa R01–R13](../../research/laboratory/AGENDA.md). Las dependencias
científicas/humanas no desaparecen al terminar una herramienta; el roadmap sigue
abierto. LAB-09 conserva integración de la nueva pila y validación física/humana,
y las líneas R01/R13 conservan ampliación de predictores y reservas.

## Publicación

- Segunda iteración: [PR #37](https://github.com/AlterMundi/harmonic-weaver/pull/37),
  rama `feat/laboratory-v2`, apilada sobre #30; sin merge automático.

- Weaver baseline: PR #29; integración: PR #30, apilada sobre #29 e incluye plan #28.
- HarMoCAP baseline: AlterMundi/HarMoCAP#1. Seis fallos por Gradio ausente en la suite
  ampliada fueron declarados; las pruebas específicas de captura pasaron.
- Telemetría/control Shaper: AlterMundi/harmonic-shaper#2, incluido silencio inmediato.
- [Arranque y recorrido](RUNNING.md), [cómo aportar](CONTRIBUTING.md).

## Implementado

LAB-01: contratos versionados, schemas/fixtures, preset portable, configuración
transaccional/revisiones, undo/redo, macros, calibración separada y bitácora ligera.
Aplicar un preset reinicia historia, incluso si conserva el algoritmo.

LAB-02: worker HarMoCAP/PyAV, PTS y rotación, identidad/missingness, cache de archivo
por contenido/modelo/código/percepción, generaciones atómicas, cancelación/fallback,
reapertura y forzado. Biblioteca, upload o ruta local, cámara latest-frame sin
persistencia por defecto. Pausa/seek/loop/source epochs.

LAB-03: catálogo/unidades, curvas/mezclas/clamps/smoothing, escritor único, mute/solo,
seis voces iniciales ampliables a 32. Runtime causal conecta archivos/cámara,
calibración, modelos y salida Shaper con lease de voces propias; libera ante gaps.

LAB-04: Shaper expone sample index, fases y gain/envolvente efectivos antes de
shape/limiter. WebGL dibuja suma compleja de todos los osciladores activos,
componentes opcionales y persistencia. El grosor usa geometría, no depende del
límite de líneas de WebGL. No representa cymatics físico ni PCM postprocesado.

LAB-05: React/TypeScript: transporte/video/esqueleto, fuente/percepción, instrumento,
modelos, ruteos/unidades, macros, figura, presets importar/exportar/guardar/deshacer,
calibraciones, marcas y diagnóstico. Cinco presets iniciales, cada uno con seis voces.

LAB-06/07: baseline preservado; derivadas/predictores locales, I/R/A de Anni,
unwrap/ángulos internos donde COCO-17 los permite; muñecas/tobillos solo orientación
de segmento distal. SVD causal, Procrustes, proyectores/amplitudes/residuo/ángulos;
candidatos regionales simultáneos. Regresión ridge retardada compara región añadida
contra historia propia del destino; selecciona lag en validación temporal pasada y
evalúa nuevas observaciones sin entrenar con ellas. Scores permiten cero o varios
centros; no establecen intención ni causalidad.

## Evidencia

- Suite Weaver completa: **229 tests + 4 subtests**, 117.68 s.
- Laboratorio: **45 tests**, incluidos contratos/cache/PTS/modelos/ruteos/runtime.
- Shaper: **35 tests** de laboratorio/audio/estado, incluidos reconstrucción
  1/6/32 voces, lease, release y revisión consumida por el callback.
- UI: **6 pruebas Playwright**: suma polifónica 1/6/32, grosor geométrico, edición,
  preset, macro continuo y reproducción real con píxeles dibujados en el canvas.
- Cámara física: captura/inferencia produjo frames recientes, sin error del worker;
  cerrada después del smoke. No equivale a una sesión corporal aceptada.
- Fragmento frontal real de 12 s: 359 frames cacheados. Los cinco modelos alcanzaron
  seis voces efectivas, sin errores de runtime; colectivo y propagación alcanzaron
  estado observado. Las medidas iniciales son RTT de control/edad de telemetría,
  no latencia física movimiento→sonido.

Los cuatro fragmentos locales (perfil/espalda/frente/sin soga) suman unos 21 MB.
El original grande permanece en Downloads sin duplicar. Video, frames, screenshots
con cuerpo y tracking privado no se incorporan al repo ni a GitHub.

## Integración comprobada y pendientes humanos

Los cuatro ángulos se reprocesaron/reabrieron y recibieron el mismo preset portable
con calibración nueva. Forzado CPU creó nueva generación; reapertura dio cache hit.
Un error CUDA encontrado no destruyó el cache previo y se recuperó usando CPU;
su causa de bajo nivel sigue abierta y se documenta en VALIDATION.

Salida JACK verificada por captura de los puertos propios: señal durante movimiento
y cero tras pausa. Soak de 600 s, 51 epochs, sin errores; control preparado→bloque
p50 14,45 ms / p95 27,92 ms. No equivale a latencia física ni escucha humana.

Quedan para Nicolás: escucha, sensación al moverse/observar, aceptación y feedback
de interfaz. Los máximos de latencia, precisión de tracking y fallo GPU tienen
límites explícitos; no se declara una validación científica o fisiológica.

Grabación opcional, evaluación formal y sensores siguen en la agenda posterior.

## Segunda iteración

Ediciones compatibles conservan suavizados/historia de expresión; referencias
versionadas sin sobrescritura. Diagnóstico de modelo/ruteo/audio, cobertura por
joint y recuperación CPU explícita con dispositivo efectivo en la identidad de
cache. Comparador web/CLI: presets congelados × segmentos, runtime compartido,
reloj/preroll/reset deterministas, features/targets/métricas y soporte común.
[EVALUATION](EVALUATION.md) documenta operación, reproducibilidad y límites.

CUDA no se declara reparado; se entrega recuperación y evidencia. Sin PCM
offline, nuevos sensores/3D ni validación científica formal. Agenda R01–R13
intacta. Aporte Oliva #36 revisado, pruebas ejecutadas, sin merge.

## Render PCM en desarrollo — 2026-09-30

Rama `feat/laboratory-offline-render` en Weaver y Shaper; no instalada sobre la
sesión local de prueba ni fusionada. Render optional web/CLI, WAV float estéreo,
voice-frames por bloque, hashes del motor, preroll/recorte/cola, repetición y
artefactos locales. Motor compartido sample-for-sample con el callback. Falta
exportación visual de fuente/figura/audio, captura #17 y bancos científicos.

## Reproductor de comparación en desarrollo — 2026-09-30

Reproducción web conjunta fuente/WAV/figura de todas las voces. Reloj del WAV,
play/pausa/seek, interpolación dentro del bloque y recorte, cola y liberación al
cerrar; velocidad y ajuste visual sin alterar manifest. API verifica hashes de
fuente/artefactos y rechaza cambios. No es reloj audiovisual físico ni exportación
renderizada. Sigue en `-dev`, fuera de la sesión corporal de prueba.

## Base de captura post-limitador — 2026-09-30

[Shaper #4](https://github.com/AlterMundi/harmonic-shaper/pull/4), sin merge/aplicación
sobre la sesión de prueba: PCM exacto, writer acotado, start/status/stop, límites
por muestras y fallos explícitos; 32 pruebas hardware-free. [CAPTURE](CAPTURE.md)
detalla contrato/evidencia y pendientes de UI, eventos, video, sincronía y recuperación.
LAB-09 no se declara completo.


2026-09-30 — Incremento de LAB-09: UI/API/colector de audio + journal confirmado,
nonce propio e inicio idempotente con Shaper #4, drenaje final completo y hashes.
22 pruebas Weaver y 33 Shaper; build web pasa. Integración sintética real confirma
PCM exacto. Ver CAPTURE.md para contratos y límites. No completa #17: video/mux,
latencia medida, identidad de código/fuentes y recuperación WAV pendientes. No
instalado sobre el workspace de pruebas; sin captura privada ni aceptación humana.


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

### R08: anotación y lectura de soga (PR #75)

Implementado en rama de desarrollo: curvas manuales por tramos, estados y
causas de invalidez; hash/dimensiones/reloj decodificado; revisiones con
linaje y artefactos verificados; resolución de assets persistidos sin jobs;
API/editor por imagen exacta, cache LRU en memoria (32 MB, cuatro inventarios),
etiquetas de extremos a/b y velocidades px/s sólo en frames consecutivos.
Contratos/API/persistencia/cache probados con videos sintéticos. Recorrido
Chrome con HTTP real verificó dibujo, extremos, oclusión, guardar, recuperar,
rebind y revisión derivada. Ninguna aceptación humana o evidencia física se
infiere de estas pruebas; no modifica síntesis ni defaults del instrumento.

Pendiente: extracción inicial observable/cancelable (aún síncrona), medición
de rendimiento con clips privados, asistencia de segmentación/tracking,
benchmark anotado de blur/oclusiones/cruces y experimento de propagación con
correspondencia/calibración explícita. Ver `research/laboratory/r08_rope/README.md`.
R08 y el roadmap permanecen abiertos; R09 no se cierra por geometría 2D.

R08, avance posterior: preparación y frames web usan jobs temporales con
estado/cancelar/reintentar; hash cooperativo y subprocesos con límite durante
streaming. Chrome verificó cancelación de preparación e imagen con proceso
sintético confirmado vivo/terminado, borrador intacto y reintento. Medición
local de lectura del clip corporal de 60 s: probe 15.8 s, imágenes nuevas
1.2–4.6 s, hits ~0.7 s, sin copias/imágenes persistidas y fuente intacta.
Pendientes: concurrencia UI de fuentes, mejora de latencia inicial,
segmentación asistida y benchmark anotado/aceptación humana. Medir lectura
no valida calidad de pose, extremos, profundidad ni propagación física.

R08 comparador: revisiones congeladas y mismo hash/dimensiones/PTS, cobertura
explícita, distancias muestreadas en píxeles por tramos desconectados;
corridas request/result/manifest persistidas con código/entorno y recálculo.
Pruebas numéricas/API/restauración/tamper y Chrome real de crear/configurar,
24 px conocidos, soporte faltante sin score, reload y descarga de manifest
pasaron. No constituye benchmark corporal ni validación científica de
cuerda; faltan extracción asistida, etiquetas humanas/uncertainty y protocolo.

R08 segmentación asistida inicial: candidatos por distancia RGB/ROI,
regiones 4-conectadas sin cerrar huecos, filtros/límites configurables en
web y overlay de runs separado de curvas humanas. Propuestas persistidas
sólo como JSON request/result/manifest, sin imágenes ni video copiados;
reverify recalcula contra fuente exacta antes de mostrar. Chrome real
verificó parámetros efectivos frente a textarea editado, guardado, recarga,
recomputación, frame incompatible bloqueado y borrador intacto. Núcleo/API/
persistencia probados con datos sintéticos. Esto no valida discriminación
soga/fondo, curvas automáticas ni tracking/propagación; benchmark humano y
algoritmos asistidos adicionales permanecen pendientes.

R08 curvas guiadas: seeds/componente/budgets explícitos, shortest path dentro
de máscara verificada sin unir huecos. Candidatos request/result/manifest
persistidos sobre máscara congelada y manifest de origen; rebind antes de
recuperar. Incorporar→aplicar→guardar son acciones separadas. Cada tramo
conserva run ID/hash y exact/edited; API rechaza geometría modificada declarada
exacta. Chrome real probó edición, reload y original intacto con borrador
editado; contratos/API/artifacts/build pasan. No centroline real ni aceptación
humana inferidos; tracking temporal, incertidumbre y benchmark pendientes.
# R08: recuperación histórica y verificación web (2026-10-02)

Comparaciones y curvas de otra versión permanecen visibles y descargables con
estado `historical_integrity_only`; versiones actuales requieren recálculo.
Curvas históricas no se incorporan como candidatas verificadas actuales.
Chrome real sobre fixture sintético verificó lectura, etiquetas, descargas sin
cambios de bytes, reload y bloqueo por UI/API; una prueba pasó en 1.9 s.
Evidencia detallada: `research/laboratory/r08_rope/README.md`, cortes 40–41.
Pendientes: migración/re-corrida explícita, bundles con dependencias,
seguimiento temporal y evaluación humana de geometría. No se modificó audio.

R08 núcleo temporal inicial (`rope_flow.py`): candidatos ópticos con seeds
explícitos, comprobación ida/vuelta y resets de soporte. Diez tests junto con
anotaciones pasaron (0.32 s). Aún no integrado en UI/decodificador/persistencia;
no constituye tracker de soga validado. README corte 42 detalla configuración,
casos probados, sesgo observado en ruido blanco y dependencias pendientes.

R08 corrida temporal (`rope_flow_run.py`): fuente/clock exactos, 2–120 cuadros,
request/result/manifest JSON, recálculo opcional con video y cancelación antes
de publicación. Diez tests núcleo/corrida sobre MP4 sintético pasaron. CLI y
límites de rendimiento documentados en README corte 43. Jobs/UI/biblioteca de
configuraciones y benchmark humano pendientes; aún no explorador web temporal.

R08 jobs temporales/API: `RopeFlowService` integrado al lifespan y biblioteca,
inicio/consulta/cancelación/inventario/descargas, estados acotados, corridas
persistidas recuperables tras reinicio. Siete pruebas de servicio/API/corrida y
API previa pasaron; incluye proceso vivo detenido y limpieza de parciales.
README corte 44 distingue mocks de worker y decode real, integridad vs recálculo.
UI temporal y aceptación/benchmark humanos pendientes; no cambian defaults.

R08 UI temporal inicial: JSON de todos los controles/rango, seeds separados,
inicio/cancelación, inventario/lectura/descargas y recuperación de configuración.
Dibujo separado de puntos soportados, sin aceptar anotaciones. Chrome real con
HTTP/MP4 sintéticos pasó en 2.3 s; build pasó. README corte 45 detalla límites:
overlay de imagen, presets nombrados, recálculo UI, cancelación web/fallos de red
y benchmark humano pendientes. No cambia experiencia sonora ni defaults.

R08 overlay temporal: puntos candidatos sobre imagen exacta bajo matching
hash/dimensiones/índice/PTS y ready. Chrome verificó desaparición por reset,
regreso al cuadro seed y borrador intacto (1 prueba, 2.9 s); build pasó.
README corte 46. Pendientes recálculo UI, presets nombrados, cancelación web/
fallos de red, rendimiento y benchmark humano; no validación física de soga.

R08 recuperación de consulta: tras pérdida de GET, UI conserva ID, bloquea otro
inicio y retoma mismo job; Chrome verificó un único POST y resultado/borrador
intacto (1 prueba, 2.8 s), build pasó. README corte 47. Pendiente respuesta
perdida del POST inicial sin ID (idempotencia), cancelación web viva y otros
casos de red, además de presets/benchmark/recálculo y rendimiento.

R08 inicio API idempotente: clave opcional y recibo persistido, reutilización
mismo request/job y rechazo de request distinto o incompleto tras restart.
Tres tests servicio/API pasaron. README corte 48: owner único, recibos sin GC;
UI/reintento de POST sin respuesta aún pendientes. Sin cambios de audio.

R08 reintento web conectado: clave/request congelados en RAM, start_unknown
bloquea edición/nuevo inicio, reintento recupera mismo ID. Chrome verificó
respuesta POST perdida tras aceptación, dos envíos iguales y una sola corrida;
validación 4xx libera edición (1 prueba, 2.2 s). Build pasó. README corte 49:
persistencia del intento entre cierres/reload todavía pendiente; también
cancelación web viva, presets, recálculo, rendimiento y benchmark humano.

R08 recibo de pestaña: sessionStorage preserva request/clave pendientes por
fuente/hash antes del POST; remount ofrece retomar explícitamente sin auto-start.
Chrome verificó POST aceptado/respuesta perdida/reload/mismo ID/una corrida y
limpieza de recibo (1 prueba, 2.2 s); build pasó. README corte 50: cierre de
pestaña, recuperación browser de ID conocido y otras dependencias pendientes.

R08 Chrome: ID conocido tras artifact perdido/reload recupera resultado sin
otro POST (1 prueba, 2.4 s); cancelación web de PID confirmado vivo deja inventario
vacío y permite nuevo cálculo real (1 prueba, 2.2 s). README corte 51 distingue
worker lento inyectado de decode/flow reales. Servidores detenidos, código de
producción intacto. Presets/recálculo/rendimiento/benchmark y otros fallos pendientes.

R08 contrato temporal reforzado: estados/puntos/causas, continuidad sin revival,
seeds, thresholds y resets/clock/bounds verificados offline; exactitud numérica
sigue requiriendo video. Siete tests contrato/corrida/servicio/API pasaron.
README corte 52 conserva alcance y pendientes; no evidencia browser nueva.

R08 presets temporales nombrados: contrato estricto sin seeds/fuente/calibración,
persistencia/API/export/import y controles web. Dos tests API (1.39 s) y Chrome
con archivo descargado/importado/aplicación/reload (1 test, 2.2 s) pasaron;
build pasó. README corte 53: seeds actuales no cambian al aplicar parámetros.
Recálculo UI, decoder secuencial y benchmark humano siguen pendientes.

R08 recálculo web: jobs owned/cancelables contra fuente/código/entorno actual,
marca recomputed ligada al manifest original sin reescribir artifacts. Dos
tests backend (1.36 s) y Chrome (1 prueba, 2.6 s) pasaron, build pasó. README
corte 54: evidencia efímera, persistencia/export y browser cancel/red del
recálculo pendientes; decoder secuencial y benchmark humanos siguen abiertos.

R08 evidencia persistida/exportable de recálculos coincidentes: report/manifest
con UTC/código/entorno y vínculo a manifest original, API/historial/descargas web.
Dos tests backend (1.37 s), Chrome (1 prueba, 2.7 s) y build pasaron. README
corte 55: lectura histórica por integridad, sin verificación actual ni custodia
firmada. Browser cancel/red del recálculo, rendimiento y benchmark pendientes.

R08 decoder secuencial inicial: núcleo streaming PNG exacto/cancelable/bounded,
cuatro tests de pixel-parity/source/count/CRC/close/cancel/timeout pasaron.
Cinco cuadros privados autorizados: 11.123 s individual vs 2.699 s secuencia,
igualdad exacta, sin archivos/copias; probe aparte 15.747 s. README corte 56:
una medición local, no realtime. Integración en flow/UI/presets todavía pendiente;
defaults/audio intactos, benchmark humano y demás roadmap abierto.

R08 decoder integrado/configurable: individual_png default, sequential_png
opt-in congelado en request y presets, selector web/JSON; consumo cerrado en
finally y paridad de features. Once tests backend (5.02 s), preset API (0.78 s),
dos recorridos Chrome (4.2 s) y build pasaron. README corte 57 preserva alcance:
medición integrada/VFR/benchmark humanos y demás roadmap pendientes; audio intacto.

R08 VFR/medición integrada: tres tests (3.86 s) verifican relojes variables,
origen no cero, gap/reset y paridad pixel/features/recompute. MP4 de fixture
presenta menos cuadros decodificados que nb_frames; rawvideo independiente
confirma inventario, sin fabricar timestamps. Medición local cinco cuadros:
individual 15.515 s vs secuencia 3.830 s, features idénticos; probe 16.146 s aparte.
README corte 58 preserva controles/limitaciones y privacidad. Sin default nuevo;
benchmark humano, más modalidades y demás roadmap pendientes.

R08 benchmark de extremos: núcleo con mapping seed/etiqueta explícito, seed-input
excluido, shared support/coverage y errores faltantes None. Tres tests pasaron
(0.27 s), distancias/swap/exclusiones/contracts/repetición; README corte 59.
Persistencia/procedencia/API/UI y referencia humana real todavía pendientes;
no métrica de forecasting ni evaluación de curva completa. Audio intacto.

R08 corte 60: benchmark temporal persistido con entradas congeladas, procedencia
declarada y lectura histórica explícita; siete tests cálculo/persistencia pasaron.
Pendientes autenticación de originales por servicio y API/UI; no equivale a
validación física ni aceptación de referencias humanas. Ver README de R08.

R08 corte 61: servicio/API de benchmark resuelve revisiones y flujos verificados,
congela hashes y rechaza cambios durante publicación. Nueve tests incluyendo video
sintético, HTTP, reinicio y conservación de originales pasaron. UI pendiente;
resolución local no equivale a revalidar el video ni la referencia humana.

R08 corte 62: benchmark temporal integrado a web con mapeo explícito, cobertura,
exclusiones, errores, inventario y descargas. Build y Chrome contra API/video
sintético pasaron; calidad de referencias humanas no evaluada. Recuperación de
respuesta POST perdida e idempotencia aún pendientes para este benchmark.

R08 corte 63: recuperación idempotente de benchmarks en servicio/web, recibos
persistentes e intento pendiente en sessionStorage. Nueve tests y build pasaron;
Chrome verificó POST aceptado con respuesta perdida, reload y recuperación sin
duplicación. No coordinación multiproceso ni GC de recibos; cierre de pestaña no
garantiza recuperación. Síntesis y medios privados sin cambios.

R08 corte 64: contexto de semillas/extremos iniciales en benchmark web, ventana y
coordenadas, bloqueo de fuentes/dimensiones incompatibles y semillas inexistentes.
Build y Chrome real pasaron; esquema sin imagen y calidad manual humana pendientes.

R08 corte 65: núcleo de comparación pareada de 2–16 condiciones sobre referencia,
etiquetas y soporte temporal comunes; coberturas individuales y diferencias
firmadas, nulos sin soporte. Seis tests pasaron. Persistencia/API/UI del banco
pareado pendientes; no implica significancia ni aceptación científica.

R08 corte 66: persistencia/verificación del banco pareado con condiciones y
procedencias congeladas, recálculo y lectura histórica diferenciados. Cinco tests
pasaron. Resolución de originales, API/UI pendientes; no valida fuentes humanas.

R08 corte 67: servicio/API pareados resuelven benchmarks verificados, congelan
manifests y rechazan cambio durante publicación. Siete tests hasta HTTP/reinicio
pasaron. UI e idempotencia del banco pendientes; no revalida video ni ciencia.

R08 corte 68: banco pareado en web con selección múltiple, cobertura/error común,
diferencias, JSON, inventario y descargas. Build y Chrome real pasaron; recuperación
idempotente del POST pareado y revisión humana pendientes. Audio sin cambios.

R08 corte 69: recuperación idempotente del banco pareado en servicio/web con
recibos persistentes y sessionStorage. Servicio/HTTP, build y Chrome tras POST
aceptado con respuesta perdida pasaron; único banco. Sin GC/coordinación multiproceso.

R09 primer corte: contrato espacial/relojes estricto para distinguir 2D observado,
3D inferido, unidades/escala, calibración declarada y missing. Dos tests pasaron;
adaptadores/API/UI, evidencia de calibración y benchmark 3D pendientes. No sensores
ni modelos nuevos instalados; ninguna inferencia física/científica verificada.

R09 corte 2: adaptador MotionFrame→stream espacial conserva unidades isotrópicas
frame_height, held, gaps y slots faltantes; rechaza streams/geometrías/relojes
mezclados. Cuatro tests pasaron. API/UI/persistencia y medición real pendientes.

R09 corte 3: API stateless de conversión MotionFrames y validación de streams;
cobertura y tiempos comunes declarados. Cinco tests hasta HTTP pasaron. UI,
persistencia y resolución por fuente autorizada pendientes; contract_only no
verifica hardware/calibración/sincronización ni identidad humana.

R09 corte 4: panel web para importar/editar JSON, slot/reloj explícitos, convertir
2D/validar stream, ver cobertura y exportar. Build y Chrome real contra API pasaron.
Sin persistencia automática ni cambio de live; cache autorizado/presets pendientes.

R09 corte 5: snapshot inclusivo/deep-copy de generación ready en biblioteca,
conversión y ruta source del runtime; no recalcula pose ni lee video. Seis tests
pasaron; source HTTP/UI y verificación de disco pendientes. Procedencia in-memory.

R09 corte 6: inventario HTTP de generaciones completas y controles web para fuente,
rango/slot/reloj. Siete tests hasta source HTTP y build pasaron. Recorrido Chrome
biblioteca pendiente; no verificación de bytes del cache/video actual.

R09 corte 7: Chrome real de fuente de biblioteca pasó contra generación sintética:
slot explícito, rango inclusivo, procedencia, missing y rechazo inválido, sin iniciar
tracking. No prueba tracking real/calidad corporal; persistencia/presets pendientes.

R09 corte 8: runner de conversiones congeladas con recálculo/binding/hash y lectura
histórica explícita. Seis tests pasaron. Servicio/API/UI/procedencia de biblioteca
persistida pendientes; no validación de calibración ni profundidad física.

R09 corte 9: persistencia declarada por servicio/API y controles de guardado/reapertura
web. Diez tests hasta HTTP y build pasaron. Chrome persistencia, procedencia de
biblioteca congelada, idempotencia/presets pendientes; no origen físico autenticado.

R09 corte 10: Chrome real verificó guardado/descarga/reload/reapertura declarada,
una corrida y bytes intactos (1,7 s). Procedencia de biblioteca, idempotencia y
presets pendientes; fixtures sintéticos, sin aceptación humana implícita.

R09 corte 11: persistencia de procedencia resuelta de biblioteca con generación
esperada, rechazos ante cambio/atribución declarada. Diez tests HTTP y build pasaron.
Botón web de fuente en Chrome, idempotencia y presets pendientes; sin rehash de video.

R09 corte 12: Chrome real verificó guardar desde generación y recuperar procedencia
idéntica tras reload, una corrida y cero solicitudes de tracking; fixture sintético.
Idempotencia/presets y validación física siguen pendientes.

R09 corte 13: servicio/API con recibos idempotentes de ambos guardados; recuperación
sin generación activa y rechazo de request distinto/fallo sin relanzar. Cinco tests
pasaron. Uso de claves/recuperación en UI y Chrome pendientes; sin GC/multiproceso.

R09 corte 14: ambos guardados web recuperables con claves/pendientes en sessionStorage.
Build y dos recorridos Chrome con POST aceptado/respuesta perdida/reload pasaron,
una corrida/cuerpo-clave idénticos. Cuota/cierre de pestaña y coordinación limitados.

R09 corte 15: inspector espacial por frame/ejes/centro/escala con estados/unidades y
clipping visibles; sin missing fantasma. Build y Chrome 2D/source + 3D sintético
pasaron. Presets/reproducción y validación de reconstrucción física pendientes.

R09 corte 16: reproducción por timestamps con pausa/seek/loop/velocidad y gap máximo
visible configurable; sin interpolación/autoplay. Build y Chrome de gap/play/final
pasaron. Loop/velocidad específicos y presets pendientes; no sync audiovisual.

R09 corte 17: Chrome con reloj controlado verificó velocidad x2, pausa, seek/loop y
parada exacta del inspector (1,6 s). No evidencia de sync audiovisual/reconstrucción;
presets pendientes.

R09 corte 18: presets portables de vista/playback por API/web, excluyen observaciones,
reloj, fuente/calibración; aplican sin autoplay y rechazan ejes 3D sobre 2D. HTTP y
build pasaron; recorrido Chrome pendiente, junto con validación física.

R09 corte 19: Chrome verificó guardar/exportar/importar/aplicar presets de vista y
rechazo XZ sobre fuente 2D sin fallback (1,6 s). No validación física ni transferencia
de calibración; hardware/experimentos y roadmap siguen pendientes.

R09 corte 20: núcleo de comparación causal de streams con unidades/marco/reloj
comunes, edad/incertidumbre y opt-in inferred/held, cobertura/causas explícitas.
Dos tests pasaron; persistencia/API/UI y calibración/reference físicas pendientes.

R09 corte 21: runner/servicio/API de comparaciones congeladas con recálculo,
inventario/descargas y recuperación. Cinco tests pasaron; web, procedencia resuelta,
idempotencia y referencia física pendientes. Inputs importados declarados.

R09 corte 22: comparación espacial configurable en web con cobertura, error/cause,
guardado/descargas/reapertura. Build y Chrome sintético pasaron. IDs/procedencia,
presets/idempotencia y validación física pendientes.


## Corte 23 · Comparación de conversiones persistidas

`POST /api/research/r09/compare-conversions` recibe reference_id, candidate_id
(IDs de conversión) y settings (labels, edad/incertidumbre máxima, opt-ins).
Resuelve streams de artefactos verificados y congela IDs + SHA256 de cada manifest
como sources en request/result. Revalida fuentes antes y después de publicar;
si cambian elimina únicamente la nueva comparación. La ruta declarada
/comparisons rechaza sources suministrados por cliente. El verificador exige
binding de sources también al leer resultados históricos.

Siete pruebas de núcleo/runner/servicio/HTTP pasaron (1,02 s): error conocido,
causalidad, procedencia, fuentes intactas, rechazo de cambios durante publicación,
exportación/reapertura y rechazo de procedencia declarada como resuelta. Fixture
con incertidumbre .02 por stream usa umbral combinado .04 explícito; defaults
no cambiados. Ningún medio privado ni audio procesado. No autentica calibración,
identidad, sincronización física ni custodia firmada. Pendientes selección por ID
en web, idempotencia y presets de comparación.


## Corte 24 · Selección web de conversiones para comparar

El panel R09 ofrece streams declarados o conversiones guardadas. Actualizar
inventario es explícito; referencia y candidato se eligen sin selección silenciosa.
Con IDs envía settings a compare-conversions y muestra procedencia en el resultado;
los hashes completos permanecen en JSON exportable. No se autentican relojes ni
calibración física. Defaults y síntesis sin cambios.

Build completo pasó. Dos pruebas Chrome contra API real aislada pasaron (1,8 s):
recorrido declarado/exportación/reload y selección de dos conversiones persistidas,
error cero conocido y binding de ambos IDs + hash. Datos sintéticos, sin dispositivos
ni medios privados; servidor de prueba detenido. Pendientes presets e idempotencia
para comparación y validación física de las fuentes.


## Corte 25 · Presets portables de comparación

API comparison-presets y panel permiten guardar, listar, aplicar, exportar e
importar parámetros/etiquetas. No incluyen streams, IDs de conversión, persona,
reloj ni calibración. Aplicar sólo cambia controles, sin seleccionar fuentes o
publicar corridas. Importar valida en servidor (archivo web máximo 64 KiB).
Validación de etiquetas únicas/no vacías ahora pertenece a Settings compartido,
para rechazar presets inválidos antes de comparar. Almacenamiento append-only,
reapertura tras reinicio y exportación sin ID local.

Nueve pruebas backend pasaron (1,19 s), build completo pasó y dos pruebas Chrome
contra API aislada pasaron (2,0 s), incluyendo guardar/aplicar conservando fuentes,
descarga/importación nativa y procedencia de comparación. Sin medios privados ni
dispositivos; servidor detenido. Defaults/síntesis sin cambios. Pendiente
idempotencia de comparación y validación física de relojes/calibración.


## Corte 26 · Recibos persistentes del comparador

Ambas rutas de publicación aceptan idempotency_key (32 hex). Congelan un recibo
con ID y hash de tipo/entrada normalizada antes de ejecutar. Reintentar la misma
entrada devuelve la corrida verificada, también tras reinicio y sin resolver de
nuevo conversiones originales; otra entrada con esa clave se rechaza. Un fallo
con recibo reservado no relanza cálculo: informa corrida no disponible. Fuentes
resueltas siguen verificándose antes/después de publicación inicial; sólo la
nueva carpeta se elimina al fallar. Sin clave, cada llamada sigue siendo nueva.

Once pruebas backend pasaron (1,29 s); después de ampliar el recorrido HTTP,
cinco pruebas de servicio/API pasaron (1,02 s), incluyendo recuperación misma ID,
conflicto de clave, recuperación sin fuentes y fallo sin relanzamiento. No hay
coordinación multiproceso ni GC de recibos. Pendiente usar recibos y recuperación
explícita en web. Audio/defaults intactos, sin dispositivos ni medios privados.


## Corte 27 · Recuperación web de comparación

Antes de POST, web guarda ruta/entrada/clave en sessionStorage; sin capacidad de
persistir no envía. Ante fallo de transporte conserva el pedido congelado y ofrece
Recuperar comparación R09. Recargar restaura sólo el pendiente, nunca reenvía solo.
Mientras hay pendiente bloquea nuevas publicaciones; recuperar usa misma entrada
aunque cambien controles. Respuesta aceptada limpia pendiente antes de lecturas
posteriores; rechazo 4xx lo limpia. Aplica a streams declarados y conversiones por
IDs. No garantiza retención al cerrar pestaña ni coordinación entre pestañas.

Build completo pasó. Dos pruebas Chrome contra API real aislada pasaron (2,3 s):
ambas rutas aceptan POST y pierden respuesta artificialmente, reintento idéntico
recupera sin duplicar; ruta declarada incluye recarga. Además exportación/reapertura,
presets con descarga/importación y procedencia preservadas. Servidores aislados
apagados. Sin dispositivos/medios privados, audio y defaults sin cambios.


## Corte 28 · Ajuste explícito de reloj desde marcas

POST /api/research/r09/clock-fit y panel web reciben nombres de relojes,
evidence_id, incertidumbre declarada y >=3 pares source_time_s/common_time_s
estrictamente crecientes. Ajuste afín por mínimos cuadrados centrado, tasa válida
(0,2], residuos individuales/RMS/máximo e intervalo de marcas. Incertidumbre es
máximo residuo + incertidumbre declarada, NO límite estadístico ni validación
independiente. evidence_id/pares siguen siendo declaraciones no autenticadas.
Resultado exportable incluye entrada completa; no aplica a streams/live ni guarda
corrida. Extrapolación fuera de marcas no validada. Span numérico extremo rechazado.

Cinco pruebas núcleo/API pasaron (1,01 s) para desfase2s/tasa1.001 conocidos,
repetibilidad, perturbación con residuo .02, evidencia ausente, pares insuficientes/
duplicados, tasa inválida y extremos numéricos. Build completo pasó. Pendientes
Chrome de ajuste/exportación, marcas reales con referencia independiente,
validación reservada temporal y persistencia de resultados. Sin dispositivos ni
medios privados; síntesis/defaults intactos. No es evidencia de exactitud física.


## Corte 29 · Marcas reservadas y Chrome de reloj

validation_anchors opcionales se evalúan con reloj ajustado exclusivamente sobre
anchors. Rechaza tiempos compartidos entre conjuntos y orden inválido. Exporta
residuos por marca, máximo reservado (null sin marcas), count y extrapolated
fuera del intervalo de ajuste. No altera tasa/desfase ni incertidumbre empírica;
reservar marcas no autentica su origen ni demuestra independencia física.
Web muestra número/residuo reservado y JSON completo.

Seis pruebas núcleo/API pasaron (1,02 s): perturbaciones reservadas no cambian
fit/uncertainty, residuo .2 conocido, extrapolación identificada y overlap rechazado.
Build pasó. Chrome real con API aislada pasó (1,3 s), repetido después de ampliar
contrato: offset/tasa conocidos, descarga nativa con entrada completa, edición
limpia resultado y evidencia vacía rechazada; no crea comparación. Ese recorrido
Chrome no incluye marcas reservadas no vacías (verificadas por backend).
Servidores detenidos, sólo datos sintéticos, defaults/audio intactos. Pendientes
medición real, validación con marcas independientes y persistencia del ajuste.


## Corte 30 · Persistencia reproducible de ajustes de reloj

clock-fits POST/GET/artifacts y panel guardan request/result/manifest con hashes,
versión Python/código, binding y recomputación. Lecturas históricas son integridad,
no recomputación actual; no autentican marcas ni sincronización. Recibos persistentes
antes de ejecutar recuperan misma ID tras reinicio; conflicto de clave rechazado.
Web guarda pedido/clave antes de POST en sessionStorage y restaura pendiente sin
envío automático, ofrece recuperación explícita y bloquea nuevo guardado mientras
pendiente. Descargas de tres artefactos y reapertura disponibles. No aplica reloj.

Seis pruebas núcleo/runner/servicio/API pasaron (0,89 s, repetidas tras limpieza de
mensajes): repetición, no overwrite, hash alterado, recomputación alterada incluso
con hash reescrito, binding histórico, recibos/reinicio/exportación. Build pasó.
Chrome contra API aislada pasó (1,6 s): ajuste/exportación, pérdida de respuesta
tras aceptación, reload/reintento idéntico, una corrida y reapertura, input inválido
limpia resultado. Servidor detenido, datos sintéticos únicamente, audio intacto.
Pendientes medición real y aplicación explícita con intervalo/uncertainty a streams;
no coordinación multiproceso, GC de recibos ni retención garantizada al cerrar tab.


## Corte 31 · Aplicación explícita de reloj persistido

POST apply-clock recibe fit_id, Stream y allow_extrapolation(false). Resuelve ajuste
verificado, exige source_clock idéntico, rechaza frames fuera del intervalo salvo
opt-in explícito; devuelve índices extrapolados. Reemplaza sólo Clock, conserva
frames/timestamps/estados/coordenadas tipados y previous_clock, calcula tiempos
comunes y congela ID/hash de manifest. Revalida ajuste al final. No modifica live,
no publica conversión ni autentica nombres/evidencia/calibración. Web ofrece ID,
JSON de stream, opt-in y exportación del resultado para inspección/uso explícito.

Ocho pruebas backend pasaron (1,00 s), build pasó y Chrome real contra API aislada
pasó (2,0 s): guardado recuperable/reapertura, rechazo de extrapolación, opt-in,
descarga con frames/reloj original/procedencia preservados. Primera aserción Chrome
falló por defaults null omitidos en fixture; completada fixture tipada y repetida
sin cambios de comportamiento. Servidores detenidos, sólo datos sintéticos,
audio/defaults intactos. Pendientes medición real, persistencia de streams externos
3D/aplicados y validación temporal independiente; aplicar no mejora incertidumbre.


## Corte 32 · Persistencia de streams externos 2D/3D

Input de conversión admite exactamente conversion MotionFrames o stream declarado;
tracking_provenance sólo con MotionFrames resueltos. Se conserva ruta conversions,
inventario, recibos y selección por ID del comparador. Stream conserva contrato,
frames/unidades/estados, exporta coverage y tiempos comunes; input_kind externo
explícito. Binding de stream y tracking_provenance se verifica también en histórico.
Canonical de recibos de MotionFrames mantiene campos previos (sin stream null)
para no invalidar sus claves. Web guardar stream declarado disponible tras validación
(o sobre resultado existente); reabrir conserva visualización 3D y no ofrece guardar
como MotionFrames. No autentica origen ni convierte metadatos importados en
procedencia verificada. Clock evidence_id persiste como declaración del stream.

Once pruebas núcleo/servicio/HTTP pasaron (1,28 s), otras cuatro de recibos/
biblioteca/API existentes pasaron (0,90 s), build pasó. Chrome con API aislada pasó
(1,9 s): guardar externo con respuesta aceptada perdida, reload/recuperación
idéntica y una conversión, reabrir figura inferred hueca, self-comparison excluye
inferred por defecto y opt-in obtiene soporte1/1/error0. Esto es control sintético,
no precisión 3D. Servidor detenido, sin medios privados/sensores, audio intacto.
Pendientes proveedores 3D reales, calibración/sincronización medidas y conservación
server-resolved de procedencia al persistir una aplicación de reloj (copiar JSON
externo conserva reloj, pero no autentica el vínculo a corrida de ajuste).


## Corte 33 · Guardado de aplicación de reloj con fuentes resueltas

POST clock-conversions recibe conversion_id, fit_id, allow_extrapolation(false) e
idempotency_key opcional. Servidor resuelve/verifica originales, congela IDs/hashes,
original_stream y fit_input, recalcula reloj y nuevo stream; revalida fuentes antes/
después de publicar. Conserva contrato/frames/unidades/estados y permite repetir
transformación offline sin originales. Binding de clock_application en histórico;
recomputación actual valida transformación, histórico sólo integridad/binding.
Ruta declared conversions rechaza clock_application suministrada manualmente.
Recibos permiten recuperar misma corrida sin resolver fuentes de nuevo. Cambios
invalidan sólo carpeta nueva. Canonical previo de recibos externos/MotionFrames
excluye nuevo campo null para conservar compatibilidad de claves.

Once pruebas servicio/HTTP/runner/recibos pasaron (1,14 s), incluyendo hashes,
frames preservados, restart/recovery sin fuente, mutación durante publicación y
rechazo de procedencia manual. Sin medios privados/dispositivos/audio. No autentica
mediciones físicas ni nombre del reloj. Pendiente controles web por ambos IDs,
recuperación/Chrome y proveedores/calibración/sincronización reales.


## Corte 34 · Guardado web por IDs de reloj y conversión

Panel selecciona conversión original/ajuste persistidos, inventario de conversiones
se actualiza explícitamente y extrapolación default false. Guardar publica por
clock-conversions, muestra resultado congelado/ID y descarga tres artefactos.
Pedido con clave va a sessionStorage antes de POST, reload restaura sin envío
automático, recuperación explícita conserva selección congelada y bloquea otro
save mientras pendiente. Respuesta aceptada limpia pendiente antes de lecturas.
Rechazos 4xx lo limpian; sin almacenamiento no se envía. Inventario incluye la
nueva conversión; reapertura está en panel general R09. No cambia fuentes/live.

Build completo pasó. Chrome real contra API aislada pasó (1,4 s): selección de
ambos IDs sintéticos, aceptación con respuesta perdida, reload/reintento idéntico,
una nueva conversión (dos totales), descarga nativa con IDs y frames preservados,
clock original offset0/nuevo offset2. Servidor apagado. Sin medios privados ni
hardware, defaults/audio intactos. Retención al cerrar tab/coordinación multipestaña
no garantizadas; exactitud física/calibración/proveedores 3D reales siguen pendientes.


## R10 corte 1 · Protocolo de experiencia declarado

Rama feat/r10-experience-protocol sobre PR #76; mismo workspace dev. Núcleo/API/web
para calendario de condiciones y respuestas tipadas, export portable sin fuentes/
participante. 3 tests y build pasan; Chrome real aislado 1,4s con calendario/export/
respuesta sintética/rechazo fuera de escala. No reproduce ni registra exposición
o respuestas humanas; audio/defaults intactos. Plan completo/pedidos en
research/laboratory/r10_experience/README.md y #24. Persistencia/player/análisis/
fuentes físicas pendientes; R10 sigue abierto.


## Corte 2 · Presets portables persistidos

API /research/r10/presets guarda/lista/exporta name/config versionados con lectura
regular acotada. Config estricto excluye slot, rol, order_index, estímulos, ratings
y trial_id. Exportación sin ID local; append-only, reapertura tras restart. Web guarda
config de preview validada; importa preset completo o config raw exportada (64 KiB),
no aplica automáticamente. Aplicar reemplaza sólo config del protocolo editable,
conserva participante/rol/order/stimuli y limpia preview/respuesta validada sin ejecutar.

Cuatro pruebas núcleo/API pasaron (0,92 s), build completo pasó. Chrome API aislada
pasó (1,7 s): guardar, descargar/importar envelope y raw config, aplicar conservando
selección, limpiar preview y tres presets tras reload. Mantiene pruebas de respuesta
sintética/rechazo fuera de escala. Servidor apagado; no exposición/participación
humanas ni niveles físicos verificados. Defaults del instrumento/audio intactos.
Pendientes protocolos congelados/manifests, resolución de estímulos, player,
exposición observada, respuestas persistentes y análisis sobre soporte común.


## Corte 3 · Protocolos congelados reproducibles

API protocols guarda request/result/manifest con hashes, código/env y binding.
Recomputación actual repite calendario; histórico se identifica sólo integridad.
Recibos persistentes antes de run recuperan misma ID tras restart; otra entrada
con clave igual se rechaza y fallo reservado no relanza. Status complete describe
publicación del artefacto, nunca exposición ni ensayos completados.
Web guarda desde preview validada, persistiendo pedido antes de POST en
sessionStorage; reload restaura pendiente sin envío automático y reintento explícito
usa la misma entrada. Reabre calendario/preguntas/rol/slot/estímulos, inicializa
respuestas null y permite descargar tres artefactos. No guarda respuestas al abrir.

Siete pruebas núcleo/runner/servicio/API pasaron (1,06 s): repetición/no overwrite,
recomputation con hashes reescritos, binding histórico, restart/conflictos/fallo
sin relanzamiento/exportación. Build pasó. Chrome API aislada pasó (1,5 s): cuatro
condiciones/ciclo24 declarado, respuesta aceptada perdida/reload/reintento idéntico,
una copia/reapertura y descarga con orden5/rol/estímulo originales. Servidor apagado.
Sin exposición humana/medios privados/hardware, audio intacto. Pendientes resolver
estímulos por IDs, player/exposición, respuestas persistentes y análisis. No GC,
coordinación multiproceso/tab ni retención garantizada al cerrar pestaña.


## Corte 4 · Estímulos resueltos por IDs R05

POST r05-protocols recibe config/slot/rol/order y stimuli {id,r05_id,arm}, hasta8,
con recibo opcional. Resuelve PCM mono single/excited/mapped por verificador R05 y
original video vía source_binding de evaluación congelada. Congela IDs/hashes de
manifest/input/PCM/medio, evaluación/run/source/person slot, crop fuente y sr/frames.
Calendario toma ventana original seleccionada, excluye tail posterior del ensayo y
usa offset nominal0 (no sincronización física medida). Requiere PCM al menos del
largo del crop; no copia ni decodifica video, no tracking nuevo.

Comprueba fuentes antes/después de publicación; cambios eliminan sólo nuevo
protocolo. Recibo recupera sin resolver otra vez. Inputs y result sources ligados
al protocolo también en lectura histórica; recomputación del calendario no
revalida originales actuales. Ruta declarada protocols rechaza sources manuales.
Nombres/identidad/níveles físicos siguen sin autenticar. No hay exposición humana.

Diez pruebas núcleo/runner/servicio/API pasaron (3,75 s): R05 render real8kHz con
pose sintética, vínculo evaluación/media hashes, selección crop.3–1.5, recuperación
sin fuentes, mutación de PCM durante publicación, API/recibo y procedencia manual
rechazada. Medio original de fixture son bytes b'a', NO video decodificable/Chrome
ni prueba audiovisual. Sin medios privados/hardware/audio device. Pendientes UI/
Chrome de selección por IDs, fixture video real, player/exposición y registros.


## Corte 5 · Vista previa y selección R05 por web

r05-preview resuelve fuentes sin publicar. Selection admite expected_sources; al
publicar compara snapshots completos, rechazando cambios respecto a preview.
Canonical previo de recibos sin expected_sources permanece igual. Web inventario
R05 completo, selector single o excited/mapped según kind, etiquetas y builder
para varios estímulos; selección/config/rol/orden editables en JSON. Guarda sólo
tras preparar y envía hashes esperados. Pedido+clave se conserva antes de POST;
reload/reintento explícito recupera la misma entrada y actualiza inventario general
R10. 4xx limpia pendiente y preview; no aplica de nuevo fuentes silenciosamente.

Once pruebas núcleo/servicio/runner/API pasaron (4,71 s), build pasó. Chrome real
API aislada pasó (1,7 s): inventario/añadir/preparar, cero protocolos antes de save,
respuesta aceptada perdida/reload/reintento idéntico con expected_sources, una copia,
reapertura/calendario y descarga de hashes/crop .3–1.5. Fixture --experience-stimulus
con H264 sintético3s y tracking sintético preparado (no inferido del video), evaluación
real y R05 PCM8kHz; esta prueba NO reproduce audio/video ni verifica sincronía.
Sólo se duplica el medio sintético pequeño en fixture, ningún original privado.
Servidor apagado, audio/defaults intactos. Pendiente player/exposición/mediciones
físicas/respuestas/análisis. Sin garantía de retención al cerrar tab/multipestaña.


## Corte 6 · Media verificada por ensayo y relojes nominales

protocols/{id}/trials/{trial}/media-info reabre protocolo verificado y resuelve
R05/evaluación/video comparando snapshot con publicación. Expone trial, hashes,
duración y audio_support_elapsed_s (null sin soporte/medio habilitado). Reloj:
video_time=source_start+elapsed; audio_time=elapsed+offset; positivo adelanta audio.
Soporte audio intersecta [0,duración] con [0,pcm_frames/sr] desplazado, sin inventar
samples/wrap. Puede incluir tail R05 en condición desacoplada; no confundirlo con
movimiento adicional. Medio cambiado rechazado, ensayo desconocido404 y protocolo
sólo declarado no tiene media resoluble.

Rutas /video y /audio bloquean medio deshabilitado por condición. Video entrega
original verificado sin copiar; audio usa vista float32/Ranges y gain congelado,
PCM autoritativo float64 intacto. Archivos se sirven completos, NO recortados:
metadata define ventana para el player pendiente, no acredita cumplimiento de crop
ni exposición. No hay autoplay ni dispositivo abierto por estos endpoints.

Diez pruebas núcleo/servicio/runner/API pasaron (5,85 s): offset-.5 soporte[.5,1.2],
video clock origen.3, media alterada rechazada, gates video_only/sound_only,
Range44bytes RIFF con gain1, ensayo desconocido404. Fixtures PCM reales con pose
sintética/video bytes b'a'; NO reproducción Chrome ni medición física. Pendientes
player por condiciones/seek/pause/gaps/offset, eventos de exposición y aceptación.
Sin medios privados/hardware/audio ni cambios de defaults del instrumento.


## Corte 7 · Player web por condición

Abrir protocolo congelado con fuentes habilita player por trial. Preparar revalida
media-info y carga sólo medios habilitados, sin autoplay; video siempre muted
(excluye sonido original de cámara). Botones reproducir/pausar y seek nominal en
pausa acotan ventana, sin loop ni avance automático a siguiente ensayo. Clock de
transporte usa performance.now; followers corrigen drift suavemente, no seeks en
cada tick. Audio sólo reproduce dentro de support_elapsed; offset negativo espera
inicio disponible, agotamiento cercano al soporte no reinicia audio. Buffering/error
pausan y requieren reanudación explícita. Tiempo nominal no demuestra exposición.

Cambiar trial/preparar/abrir otro protocolo/unmount detiene medios y descarta
metadata obsoleta. Follower común acepta HTMLMediaElement y pausa un play pendiente
al resolver después de dispose; no toca síntesis Shaper, ratios o fases del instrumento.
Abrir otro protocolo limpia player anterior antes de esperar respuesta. Resultado
histórico sigue identificado por integridad y fuente revalidada al preparar.

Build pasó. Cuatro controles follower pasaron (0,9s); uno de decoder del instrumento
original quedó skipped por falta de fixture específica, no se presenta como ejecutado.
Nuevo Chrome contra API/R05/evaluación/H264 sintéticos pasó (4,4s, repetido tras
limpieza de apertura): cuatro condiciones, sin autoplay, video avanza, seek pausado
.7→video1.0, sound-only sin video, audiovisual, audio espera soporte por offset-.5,
pausa y reload sin player activo. Audio silenciado por test, NO escucha humana,
latencia física o aceptación. Primera corrida falló por formato .7 del slider en test;
corregido a0.7 sin cambiar comportamiento. Servidores detenidos, medios privados
intactos, sin dispositivo audio abierto por backend.

Pendientes eventos persistentes de exposición observada (buffering/seeks/gaps/
completitud), inyección Chrome de fallos/cargas tardías/agotamiento positivo,
respuestas persistentes/análisis y pruebas humanas con niveles/sincronía medidos.


## Corte 8 · Fallos y agotamiento del player

Tres pruebas Chrome del player pasaron juntas (7,5 s), contra API y medios
sintéticos: condiciones y seeks del corte 7; offset positivo +.5 con agotamiento
de audio sin reinicio y fin nominal en 1.2 s; pausa del reloj y ambos medios ante
waiting, sin reanudación automática por canplay; respuesta real de media-info
retenida y liberada después de desmontar el player sin revivir medios.

El evento waiting fue inyectado: verifica su manejo, no una congestión de red real.
Audio silenciado por las pruebas; no acredita escucha, exposición humana, latencia
física o sincronización medida. No se requirieron cambios de producción ni defaults.
El servidor sintético terminó con exit 0; medios corporales y servicios cotidianos
intactos. Pendientes registro persistente de transporte/observaciones, respuestas
y análisis, y ensayos humanos con niveles y sincronización medidos.


## Corte 9 · Contrato de telemetría de transporte

experience_transport.py define snapshots de estado HTMLMediaElement y eventos con
secuencia contigua, reloj monotónico, epochs y posición acotada al ensayo. Rechaza
retroceso sin nuevo epoch, medios incompatibles con condición y valores no finitos.
Resumen determinista cuenta seeks/waiting/errores y fin nominal declarado: NO
calcula duración de exposición interpolando eventos ni equipara fin con completitud.
Hashes e IDs son declaraciones hasta que el servicio futuro los vincule al protocolo.

Dos pruebas pasaron (0,12 s): retroceso/epoch, secuencia/reloj/posición, NaN y medio
deshabilitado; resumen repetible sin métrica de exposición inventada. Es un contrato
aún no conectado al player ni persistido/API/UI. Esos entregables siguen pendientes.
Sin cambios de defaults, sonido, hardware ni medios corporales.


## Corte 10 · Vinculación de transporte al protocolo

bind_protocol verifica artefactos R10 y hash manifest declarado, trial existente,
duración y gates exactos; revalida manifest al terminar. Recupera role/slot, trial
y fuentes congelados, sin tomar identidad ni condición del cliente como evidencia.
No revalida disponibilidad actual de medios ni demuestra exposición. Acepta planes
declarados sin fuentes, identificados por lista vacía, sin inventar media.

Cinco pruebas de transporte y runner pasaron (0,34 s), incluyendo reapertura del
servicio, rechazo de hash/trial/duración/gates contradictorios y artefacto alterado.
Pendientes persistencia con recibos, API, captura de eventos en player y exportación
web. Defaults y experiencia sonora intactos.


## Corte 11 · Registros de transporte persistentes

TransportService guarda trace/binding/manifest locales inmutables en r10-transports,
con ID derivado de contenido, hashes e implementación. Reintentos idénticos después
de restart recuperan el mismo registro sin exigir medios/protocolo originales;
registros nuevos exigen bind_protocol verificado. Lectura valida hashes, identidad
de contenido y trial/gates/duración; resumen se recalcula sólo con código coincidente,
histórico se marca integridad solamente. Exporta tres artefactos; listado omite
registros incompletos/alterados. Publicación incompleta no se relanza silenciosamente.

Cuatro pruebas pasaron (0,32 s inicial; repetidas tras verificación de identidad):
retry/restart, exportación, lectura sin protocolo original, registro nuevo rechazado
sin protocolo, corrupción omitida y traversal rechazado, junto a contrato/binding.
Pendientes API/UI/captura de eventos; sin cambios de sonido/defaults. Hashes no
son custodia firmada; snapshots declarados no prueban exposición humana.


## Corte 12 · API de registros de transporte

POST/GET /api/research/r10/transports publican/listan telemetría declarada;
GET /transports/{id}/artifacts/{name} exporta trace/binding/manifest como attachments.
POST valida contrato y protocolo/trial congelados, retry de contenido idéntico
recupera registro existente. Rutas no abren dispositivo ni exigen protocolo de
evaluación para explorar el instrumento cotidiano.

Nueve pruebas API/contrato/servicio pasaron (2,47 s): creación, retry, exportación
byte a byte después de restart, gates/trial contradictorios y artefactos desconocidos
rechazados. Warning de deprecación Starlette/AnyIO, sin fallo. Pendientes captura y
recuperación web de eventos, respuestas persistentes/análisis y aceptación humana.
No pruebas Chrome nuevas en este corte, no escucha ni sincronía física acreditadas.


## Corte 13 · Captura y guardado explícito desde player

Player captura prepared/play_requested/pause/seek/waiting/media_error/nominal_end,
snapshots cada 250 ms mientras corre y estado HTMLMediaElement. Exportación JSON
local y guardado explícito en pausa, con enlaces trace/binding/manifest. No autoplay
ni protocolo obligatorio para exploración cotidiana. Registro local se reemplaza
al preparar otro ensayo, advertencia visible; máximo 20000 eventos, overflow visible.

Build pasó y tres Chrome pasaron (7,6 s), incluidos registro guardado por API,
trial/seek/play/snapshot/secuencia de trace exportado, gates/offset/buffering/cierre
de cortes previos. Medios sintéticos y audio silenciado; no exposición humana ni
sincronía física. waiting inyectado, no congestión real.

Pendientes congelar y recuperar POST fallido tras reload, inventario web de registros
y conservación de cierre/unmount: closed queda sólo en memoria si no se exporta;
no se afirma durabilidad de eventos posteriores al guardado. Guardar produce snapshot
finito, no actualiza artefacto existente. Sin cambios al instrumento/sonido/defaults.


## Corte 14 · Recuperación web e inventario de transporte

Antes del POST, player congela JSON en sessionStorage. Envió fallido conserva
contenido; no permite guardar otro hasta recuperar el pendiente. Panel independiente
restaura tras reload, retry explícito sin autoplay/player, lista registros y ofrece
attachments. Identidad por contenido evita duplicados; retry no añade snapshots
posteriores. No autoenvío, almacenamiento limitado a la sesión de esa pestaña.

Build y tres Chrome pasaron (7,8 s). API aceptó primer POST y respuesta fue abortada
a propósito; reload restauró pendiente, segundo POST idéntico recuperó un único
registro. También verificadas condiciones/seek/offset/buffering/carga tardía. Audio
silenciado y medios sintéticos; no exposición humana ni sincronía física.

Pendientes gestión explícita de pendiente inválido/rechazado (ahora conserva para
diagnóstico), conservar cierres/unmount posteriores al snapshot, respuestas
persistentes/análisis y ensayo humano. sessionStorage no garantiza recuperación
al cerrar pestaña ni si almacenamiento falla; fallo visible evita enviar sin copia.
No cambios del instrumento/sonido/defaults ni medios privados.


## Corte 15 · Pendientes inválidos recuperables

Panel permite exportar bytes originales del envío pendiente, incluso JSON inválido,
y descartar explícitamente sólo la copia de esa pestaña. No elimina registro ya
aceptado por servidor. Pendiente rechazado sigue disponible para diagnóstico/retry;
no queda bloqueo sin salida. Sin autoenvío ni autodiscard.

Build y cuatro Chrome pasaron (8,3 s): exportación exacta '{broken-json', ausencia
de retry inválido, descarte explícito y reload sin pendiente, más suite del player y
recovery aceptado-respuesta perdida. Medios sintéticos/audio silenciado, sin escucha
humana. Pendientes conservación de cierre y respuestas/análisis; defaults intactos.


## Corte 16 · Respuesta vinculada a preguntas congeladas

experience_response.Request referencia protocolo/hash + Response estricta y
transport_id opcional. resolve verifica protocolo, trial guardado y escala/items,
conserva null; recupera preguntas/role/slot del protocolo. Transporte opcional debe
coincidir en protocolo/hash/trial y trial completo; hash se verifica al terminar.
No exige transporte para declarar una respuesta ni infiere exposición desde fin
nominal. Preguntas configuradas no son escalas científicamente validadas.

Cuatro pruebas response/protocol/transport-service pasaron (0,37 s): null/75,
reapertura, rechazo de escala/item/hash/trial y transporte de otro protocolo/ensayo.
Este corte resuelve/vincula en memoria; persistencia, API/UI de respuestas y análisis
siguen pendientes. Sin datos humanos nuevos ni cambios de sonido/defaults.


## Corte 17 · Respuestas persistentes y API

ResponseService guarda request/result/manifest inmutables bajo r10-responses,
ID por contenido y retry idéntico tras restart. Corrección crea registro nuevo sin
reemplazar ni deduplicar participantes implícitamente. Snapshot conserva preguntas,
escala/trial/role/slot y vínculo opcional de transporte. Lectura valida hashes,
identidad y binding de respuesta/role/slot aun histórica; con código coincidente
recalcula ratings. Reabrir no exige protocolo/media originales; nuevo registro sí.

POST/GET /api/research/r10/responses y GET /responses/{id}/artifacts/{name}.
Ocho pruebas API/servicio/binding pasaron (2,62 s); dos repetidas tras reforzar
binding histórico (0,37 s inicial previo). Retry, corrección, null, exportación
idéntica tras restart, fuente eliminada y corrupción verificadas. Warning AnyIO
de deprecación sin fallos. Pendientes UI/recovery y análisis descriptivo, aceptación
humana y hardware. Datos sintéticos, sin respuestas humanas nuevas ni defaults.


## Corte 18 · Guardado y recuperación web de respuestas

Panel independiente usa respuesta JSON existente y protocolo abierto; apertura
calcula SHA-256 de bytes del manifest recibido, guardado referencia ese hash.
Transport_id opcional explícito. Congela POST en sessionStorage antes de enviar,
retry tras reload sin incorporar ediciones posteriores, listado/exportaciones.
Pendiente inválido/rechazado exportable y descartable localmente; no autoenvío.

Build y cinco Chrome pasaron (9,1 s): respuesta sintética pleasure75/beautynull,
POST aceptado con respuesta abortada, reload, retry idéntico, único registro y
listado; también suite player/transporte. No respuestas humanas ni aceptación.
Snapshots nuevos requieren protocolo abierto; validación stateless sigue separada.
Pendientes análisis descriptivo, cierre duradero de transporte, ensayos humanos
y mediciones físicas. sessionStorage limitado a sesión/pestaña, no backup.
Sin cambios de sonido/defaults ni medios privados.


## Corte 19 · Análisis descriptivo seleccionado

experience_analysis analiza 1–256 IDs de respuestas verificadas, congela snapshots
y hashes, revalida al terminar. Agrupa sólo preguntas/texto/escala idénticos, role y
condición; informa valores, conteo respondido/null, mediana/min/max sin imputación.
Rechaza IDs duplicados y dos correcciones de un mismo protocolo/trial. Registros de
otros protocolos no se consideran participantes independientes por tener otro ID.
API POST /api/research/r10/analysis-preview stateless; no publicación todavía.

Siete pruebas núcleo/API pasaron (2,63 s): mediana50 de0/100, null sin convertir
a cero, corrections rechazadas, roles/escalas separados, repetibilidad y preview
HTTP. Warning AnyIO de deprecación sin fallo. Pendientes web, manifest de análisis
frozen/recovery/exportación y contraste pareado explícito. No hipótesis, causalidad
ni aceptación científica/humana acreditadas; sin defaults ni datos privados nuevos.


## Corte 20 · Selección y tabla descriptiva web

Panel de análisis lista respuestas y exige selección explícita vacía inicialmente.
Preview muestra tabla por preguntas/texto, condición/role y escala: respondidos,
null, mediana/min/max (— sin valores). Exportación JSON incluye snapshots y hashes
de fuentes/límites. Cambiar selección/actualizar invalida preview anterior; tokens
descartan resultados tardíos al desmontar. No participantes inferidos ni autoanálisis.

Build y cinco Chrome pasaron (8,8 s): selección de respuesta sintética, tabla75 y
null como —, descarga real con ID de fuente/null, deselección limpia tabla y
deshabilita análisis; suite player/recovery previa también pasa. Sin aceptación
humana/escucha. Pendientes manifest y publicación/recovery de análisis congelados,
contraste pareado y cierres duraderos. Sin cambios de sonido/defaults.


## Corte 21 · Cálculo puro sobre fuentes congeladas

FrozenInput valida selección/sources ordenados e IDs/hash; calculate trabaja sin
servicio, usando snapshots, identidad de contenido y trial recalculado desde
protocolo. analyze sólo resuelve/verifica fuentes y llama ese mismo núcleo.
Permite recomputar después de eliminar respuestas originales sin inventar fuentes
actuales; hash manifest de fuente sigue referencia, no custodia firmada.

Ocho pruebas núcleo/API pasaron (2,63 s), más dos del núcleo repetidas tras validar
identidad: cálculo idéntico sin original, selección/trial/ratings contradictorios
rechazados. API preservada. Pendientes runner/manifest y guardado/recovery web del
análisis; contraste pareado y aceptación humana siguen abiertos. Defaults intactos.


## Corte 22 · Runner y manifest de análisis congelado

experience_analysis_run publica request/result/manifest en directorio nuevo,
sha256 de entrada/salida, código y entorno Python/metric. Verificador chequea
inventario, regularidad/tamaño, binding selection/sources aun histórico y recálculo
completo sólo si código/entorno coinciden. Histórico dice integridad solamente;
status complete describe artefactos, no roadmap/exposición/validez científica.

Tres pruebas runner/núcleo pasaron (0,40 s), runner repetido tras limpieza import:
resultado igual a preview, recálculo sin original, overwrite prohibido, mediana
alterada con hash actualizado rechazada por recálculo, lectura histórica explícita
y fuentes distintas rechazadas aun con hashes rehechos. Hashes no custodia firmada.
Pendientes servicio/recibos, API y guardar/reabrir web del análisis; pareados y
aceptación humana. Sin defaults/sonido ni datos privados nuevos.


## Corte 23 · Servicio y API de análisis congelados

AnalysisService exige IDs+hashes expected_sources de preview, revalida fuentes
antes/después de publicar. ID por selección/hashes permite retry tras restart sin
fuentes originales; lectura recalcula snapshots. Fallo de publicación elimina sólo
su carpeta nueva, sin tocar respuestas u otros análisis. API POST/GET analyses y
GET analyses/{id}/artifacts/{name}; tres artefactos exportables.

Ocho pruebas servicio/runner/API pasaron (2,70 s): hashes distintos desde preview
rechazados sin publicación, retry mismo ID, exportación idéntica tras restart,
fuente eliminada y paridad preview/resultado guardado. Warning AnyIO sin fallo.
No inyección de fallo durante publicación en este corte; caso queda pendiente
para verificación específica. Pendientes guardar/recovery/reabrir web, pareados y
ensayos humanos. Sonido/defaults y datos privados intactos.


## Corte 24 · Guardar/reabrir análisis en web y fallo de publicación

Panel de análisis frozen guarda selección/hashes de preview, congela pending en
sessionStorage y ofrece retry tras reload sin cambiar contenido. Listado/reapertura
actualizan tablas desde resultado guardado, con etiqueta explícita y attachments.
Pendiente exportable/descartable localmente; no autoenvío/autoanálisis.

Build y cinco Chrome pasaron (9,2 s): POST de análisis aceptado con respuesta perdida,
reload/retry idéntico, único registro, reapertura tabla75/null y suite previa.
Prueba servicio pasó (0,33 s): fallo inyectado después de escribir artifacts limpia
únicamente intento nuevo y preserva bytes del análisis anterior.

Pendientes carreras de reapertura tardía vs edición de selección, contraste pareado,
conservación de cierre y ensayos humanos. Fixtures sintéticos/audio silenciado, sin
aceptación física/científica. Sonido/defaults intactos.


## Corte 25 · Reapertura tardía no pisa nueva selección

Abrir análisis inicia generación en panel padre y limpia vista anterior; callback
sólo aplica si generación sigue vigente. Cambiar selección/actualizar/otro cálculo
invalida apertura pendiente, sin bloquear exploración mientras descarga.

Build y cinco Chrome pasaron (9,4 s): respuesta real del resultado guardado
retenida, checkbox desmarcado durante carga, liberación no revive tabla ni vuelve
a seleccionar respuesta. Recovery/guardado/playback previos pasan. Servidor
sintético detenido; audio silenciado, sin aceptación humana. Pendientes contraste
pareado, cierre duradero y líneas R11–R13; no defaults/sonido modificados.


## Corte 26 · Contrastes pareados explícitos

experience_pairs define pares reference_id/target_id (máximo128), dirección
target−reference, mismo protocolo/hash/questions, estímulo/repetición y condiciones
diferentes. Reutiliza validación frozen de análisis; input exportable recalculable.
Null de cualquier lado produce delta null; resumen mediana de diferencias soportadas
y conteo de pares faltantes, sin imputación. Pueden compartir respuestas: no son
participantes independientes. API POST pairs-preview stateless.

Siete pruebas núcleo/API pasaron (2,64 s):0→75 delta75, inverso−75, null, mismo
input repetible, duplicados/autopar/otro protocolo rechazados y preview HTTP.
Pendientes pruebas específicas repetición/estímulo distintos, UI, manifest/guardar
pareados y mediciones/aceptación humanas. Sin conclusiones científicas ni defaults.


## Corte 27 · Pares configurables en web

Panel de pares lista respuestas, selección explícita reference/target y editor
JSON de múltiples pares; cálculo manual, tabla de ambos valores/diferencia/soporte
y exportación real JSON con input frozen/límites. Editar pares invalida tabla;
resultados tardíos de cálculo no se aplican tras unmount. Sin emparejamiento auto.

Build y seis Chrome pasaron (10,3 s):75→100 delta25, null como unanswered,
dirección/IDs en descarga, edición limpia preview; suite previa pasa. Núcleo pasó
(0,40 s), ahora incluye estímulo/repetición diferentes rechazados. Pendientes
manifest/guardar/recovery de pares, presets de contrastes y cierre duradero.
Fixtures sintéticos/audio silenciado, no aceptación humana. Defaults intactos.


## Corte 28 · Manifest/servicio/API de pares congelados

experience_pairs_run guarda input/result/manifest, hashes/código/entorno y
verificación por recálculo; histórico verifica binding de input sin afirmar cálculo
actual. PairService publica sólo fuentes con hashes coincidentes al preview, revalida
al terminar y limpia carpeta nueva ante fallo. ID por pares+fuentes recupera retry
tras restart sin originales. API POST/GET pairs y GET pairs/{id}/artifacts/{name}.

Ocho pruebas núcleo/runner/servicio/API pasaron (3,24 s): paridad preview, sin
originales, retry/export/listado tras restart, delta alterado con hash actualizado
rechazado, histórico explícito e input distinto rechazado. Warning AnyIO sin fallo.
Pendientes guardar/recovery/reabrir pares desde web, inyección de fallo específica
de PairService, presets de contrastes y cierre duradero. Sin cambios de sonido,
defaults ni datos humanos nuevos; no causalidad/aceptación científica acreditadas.


## Corte 29 · Guardar/recover/reabrir pares desde web

Records compartido para análisis y pares usa recursos, pending keys y selección
propios. Guarda pares+hashes de fuentes de preview, congela envío antes de POST;
retry tras reload no añade ediciones posteriores. Listado/reapertura/attachments,
label de resultado guardado y generación que invalida reapertura ante nueva edición.
No cambia flujo cotidiano ni activa reproducción.

Build y seis Chrome pasaron (10,6 s): pares POST aceptado/respuesta perdida,
reload/retry idéntico, único registro, reopen delta25, edición limpia tabla; también
guardado/recovery/apertura de análisis sigue pasando tras compartir componente.
Fixtures sintéticos/audio silenciado, sin aceptación humana. Pendientes presets
portables de contrastes, fallo específico PairService, cierre duradero y R11–R13.
Servidor de fixture detenido, sonido/defaults intactos.


## Corte 30 · Fallos de publicación y verificación integrada R10

PairService probado con fallo después de escribir y fuente manifest modificada
durante publicación. Ambos rechazan/limpian únicamente nuevo intento y conservan
bytes/listado del análisis válido anterior. No cambio de producción requerido.
Suite completa R10 backend pasó:26 pruebas,7,84 s; contratos/protocols/presets,
fuentes/media clocks, transporte/responses, análisis/pares/manifest/retry y API.
Warning Starlette/AnyIO de deprecación, sin fallo. Alcance sintético, no verificación
humana ni física. RUNNING incorpora recorrido opcional R10.

Pendientes presets portables de contrastes, cierre duradero, tamaño/latencia con
sesiones largas, ensayos humanos/sincronía física, R11–R13 y agenda anterior.
Roadmap permanece abierto; no defaults/sonido cambiados ni medios privados publicados.


## Corte 31 · Diseños portables de contrastes y API

Configuration contiene sólo pares directionales de condiciones (máximo12 únicos).
PairDesignPresets guarda/exporta sin IDs de personas/respuestas/fuentes/calibración.
Aplicación explícita a response_ids verificados junta por protocolo/estímulo/
repetición, muestra pares disponibles y missing por lado; no selecciona respuestas
externas ni calcula/publica automáticamente. Más de128 pares exige reducir selección.
API pair-design-preview y GET/POST pair-design-presets con exportación portable.

Siete pruebas núcleo/API pasaron (2,81 s): diseño reproducible, fuente faltante
explícita, dirección, preset tras restart/export byte idéntico, IDs/calibración
rechazados, contraste duplicado y aplicación HTTP. Warning AnyIO sin fallo.
Pendientes controles/import/apply de diseños en web y cierre duradero; R11–R13
y aceptación humana siguen abiertos. No cambios de sonido/defaults.


## Corte 32 · Diseños portables en web

Panel diseños incluye configuración JSON, save/list/apply/export presets y native
import raw/config wrapper (64KiB). Respuestas elegidas explícitamente, preview
pares disponibles/missing y Usar pares como acción separada; no cálculo/autoplay.
Import/aplicar cambia sólo diseño, conserva selección y limpia preview obsoleto.
Config no contiene IDs/calibración; backend estrictamente valida al guardar/preparar.

Build y siete Chrome pasaron (11,1 s): diseño guardado, export sin IDs, import
wrapped/raw conserva checkbox,1 par+1faltante y aplicación escribe un par; suite
previa completa pasa. Sin respuestas humanas ni sincronía medida. Pendientes cierre
durable, sesiones largas/aceptación física y R11–R13; roadmap sigue abierto.
Servidor sintético detenido, defaults/sonido intactos.


## Corte 33 · Borrador de transporte y cierre recuperable

Cada evento/snapshot conserva borrador sessionStorage acotado a4MiB. Unmount
pausa medios y agrega closed; panel independiente permite guardar/exportar/descartar
borrador sin player ni autoplay/autoPOST. Envío usa pending separado congelado,
no modifica borrador si llegan eventos nuevos; fallo storage visible, memoria sigue.
Preparar nuevo ensayo reemplaza borrador (advertido). Notificación draft sólo lee
storage, no genera GET de inventario en cada snapshot.

Build y ocho Chrome pasaron (12,7 s): player cerrado por editar protocolo, evento
closed conservado, reload sin player, POST explícito idéntico al borrador y artifact
recuperado, sin audio/video revividos. Suite previa pasa. No medición física/humana.

sessionStorage no sobrevive garantía de cerrar pestaña ni crash/quota; reload puede
conservar último snapshot sin closed (cleanup React no garantiza cierre de página).
Para durabilidad, guardar en servidor local o exportar. Pendientes sesiones largas/
latencia/storage, acceptance humana y R11–R13. Sonido/defaults intactos.


## R11 · Corte 1: contrato crudo de importación

neuro_observations preserva unidades/referencia, índices/timestamps originales,
null+causa y anotaciones, reutiliza Clock R09. No filtrado/conversión automática ni
hardware. Dos pruebas sintéticas pasan (0,14 s). Protocolo y fuentes oficiales en
research/laboratory/r11_neuro/README.md. Pendientes API/UI/persistencia/SNR,
inventario/adaptador reales, mediciones y participantes; sin aceptación humana.
Branch feat/r11-neuro-contract continúa encima de R10, mismo workspace dev;
originales/lab cotidianos intactos, sin defaults de audio cambiados.


## R11 · Corte 2: inspección API/web

POST /api/research/r11/inspect valida Stream y devuelve inventario/raw. NeuroPanel
en Investigación permite native JSON import16MiB/editor, inspect explícito y
exportación; tabla unidades/referencia/support/artefactos declarados. Editar limpia
resultado y generaciones descartan respuestas tras unmount. No default hardware,
no normalización/filtrado/SNR ni archivo persistente.

Build y tres pruebas núcleo/API pasaron (0,88 s; warning AnyIO sin fallo), Chrome
real contra fixture API pasó (1,4 s): import/export mantiene0/null/.008/unidad,
gap visible, causa vacía rechazada y tabla inválida no revive. Datos sintéticos,
sin audio/hardware humano. Servidor fixture detenido. Pendientes manifest/servicio,
SNR/control synthetic y unidades/clocks de export real; aceptación física pendiente.


## R11 · Corte 3: persistencia/API

neuro_run publica Stream/request, inventario/result y manifest con hashes/código/
entorno. Recalcula inventory actual, histórico dice integridad sólo y siempre exige
raw/result binding. NeuroService usa identidad por contenido para retry/restart,
listado y attachments; POST/GET observations y artifacts API. No registra dispositivo
ni normaliza/filtra; importación raw explícita conserva metadata y datos.

Cinco pruebas núcleo/runner/API pasaron (1,08 s): retry/restart/export idéntico,
0/null/causas preservadas, inventory alterado con hashes rehechos rechazado,
histórico y rawbinding, traversal/artefacto desconocido. Warning AnyIO sin fallo.
Pendientes guardar/recovery/reabrir web, presupuestos de tamaño/latencia, estimadores
SNR, adaptador/hardware real y sync física. Fixtures sintéticas; sonido intacto.


## R11 · Corte 4: guardado y recuperación web

Investigación → R11 permite guardar el Stream inspeccionado, listar registros y
reabrir inventario/raw, con enlaces a request/result/manifest. Antes del POST se
congela el envío en sessionStorage; si falla la respuesta, un reintento explícito
tras recargar conserva el contenido y reutiliza la identidad del servidor. No se
reenvía automáticamente. El pendiente puede exportarse o descartarse sin borrar
registros del servidor. Si el navegador no puede guardar el pendiente, no envía.
SessionStorage no sustituye un archivo duradero y no garantiza recuperación al
cerrar la pestaña; datos grandes y latencia requieren una evaluación posterior.

Chrome contra API sintética: 1 prueba pasó (2,0 s total, 1,2 s ejecución), incluyendo
POST aceptado con respuesta perdida, recarga, reintento idéntico, registro único,
reapertura y request original con cero/null/unidades/clock/gaps intactos. Cinco
pruebas Python de contrato/runner/API pasaron (1,50 s; deprecación AnyIO sin fallo).
Build TypeScript/Vite pasó. Servidor de prueba detenido, sin hardware ni audio.
Pendientes estimadores/controles SNR, export real, presupuestos de datos, hardware,
adquisición y sincronización física. No cambia sonido, presets ni defaults.


## R11 · Corte 5: control sintético de señal/ruido conocido

neuro_snr y POST /api/research/r11/synthetic-snr generan dos tonos dimensionless
independientes y su suma. La designación señal/ruido es parte del control: no se
estima separación desde EEG ni se interpreta ruido fisiológico. Config estricto
con amplitud/frecuencia/fase/offset por componente, rate/count (2–20000), ventana
[start,stop), gaps y exclusiones explícitos; frecuencias estrictamente bajo Nyquist.
No dispositivos ni cambios de sonido/defaults.

Métrica known_component_mean_square_v1: media cuadrática de cada componente
sobre idénticos índices retenidos, con retiro opcional de media independiente sobre
ese mismo soporte. No ponderación temporal, interpolación, filtro o inferencia de
banda. Cociente en dB = 10(log10(Pseñal)−log10(Pruido)). Conserva componentes,
suma, timestamps, soporte exacto y config. Potencias numéricas cero producen
noise_zero/signal_zero/both_zero y dB null, nunca Infinity; menos de dos muestras
produce insufficient_support. Magnitudes son dimensionless², no watts físicos.
Esta definición con componentes conocidos coincide con el caso documentado en
[referencia SNR MathWorks](https://www.mathworks.com/help/signal/ref/snr.html);
no adopta sus estimadores espectrales ni los aplica al registro de un cuerpo.

NeuroSNRPanel ofrece controles para todos los parámetros, import/export de config
portable y export del resultado completo. Editar invalida resultado; validación
API explícita rechaza configuración inválida. Cambiar el control no cambia las
observaciones crudas ni adquiere hardware. El resultado se descarga localmente;
aún no tiene archivo/manifest de servidor ni verificador de código histórico.

Evidencia: 12 pruebas Python pasaron (1,36 s; AnyIO deprecación sin fallo), build
TypeScript/Vite, dos recorridos Chrome contra API sintética (2,4 s total). Control
analítico amplitudes2:1 da6,0206dB; DC3 cambia potencia2→11 y retiro media devuelve2;
soporte común [10,12,14,16] tras ventana/gaps/exclusiones; ceros/support insuficiente,
frecuencia Nyquist, índices inválidos y NaN rechazados. Chrome verifica export de
resultado, import/export de configuración, ventana/gaps, ruido cero e invalidez sin
tabla anterior. Servidor de prueba detenido. Datos sintéticos, sin escucha humana.
Pendientes manifests/verificación de corridas SNR, controles adicionales, datos
reales/adaptador, inventario hardware, protocolo/estimador sobre señal física y sync.
Roadmap R01–R13 abierto; sin resultados sobre estados mentales o fisiología.


## Alternancia de presets sobre el mismo instante (2026-10-02)

ComparisonPlayer permite elegir entre todos los presets con PCM del mismo
source_index (segmento/persona/crop congelados), conservando posición del WAV y
pausa/reproducción. No incluye otros segmentos aunque provengan del mismo video.
Al cambiar, pausa ambos medios y espera metadata del WAV + sus voice-frames antes
de restaurar el instante y reanudar si estaba reproduciendo. Carga tardía de una
selección anterior se descarta; cambios rápidos mantienen intención/posición
pendientes. Pausar comparación cancela reanudación pendiente, incluso durante
carga. Error de carga deja medios pausados y diagnóstico visible.

La figura suma todas las voces guardadas para el preset elegido; no vuelve a
analizar movimiento ni altera presets/calibración/audio live. Nivel/afinación/fase
provienen del render congelado. No normaliza loudness ni agrega crossfade: cambio
de archivo puede tener interrupción/transiente audible. No confundir alternancia
browser con reproducción física continua o prueba de superioridad de un preset.

Evidencia: build TypeScript/Vite; cuatro pruebas Playwright pasaron (5,2 s): reloj
recortado/todas las voces, controls/render, switching con pause/resume y carga
obsoleta, más recorrido de red real. Para esta última se renderizaron localmente
3 presets × minuto corporal real existente: referencia sostenida, contraste×10 y
contraste×10 con transient_mix0.5. Cada render tiene3600ticks/2880000samples@48kHz,
manifest y artefactos congelados; tracking reutilizado sin copiar video ni cambiar
presets guardados. Slot seleccionado conserva procedencia previa de posición a la
derecha, no identidad biométrica. Chrome usa API real, video/WAV/voice-frames
locales, cambia las tres variantes en pausa a15s y reanuda otra conservando tiempo;
figura WebGL activa. Audio muted: no escucha/aceptación humana ni sincronía física.
Datos/IDs/resultados corporales quedan locales; no se publican como fixtures.

El recorrido de prueba inicialmente falló con relay Playwright de grandes cuerpos;
se verificó usando proxy HTTP local Vite→API y medios originales sin ese relay.
No se cambió el media/render ni se relajaron los checks de posición/pausa/reanudar.
Estos resultados no acreditan rendimiento para cualquier duración/dispositivo.
Carga completa de voice-frames y cambio sin crossfade siguen límites de esta entrega.


## Presets afinados por descriptor corporal (2026-10-02)

Los templates históricos local/relational/angular/collective calculan descriptores
distintos pero usan velocidad zonal para gain; sus diferencias iniciales se
expresaban en detune/fase. Con esas rutas apagadas, elegir otro modelo no hacía
claramente audible su descriptor. Se agregan cuatro presets lab-v3-descriptor-*
(08–11) con gain específico y sin detune/fase. No reescriben templates existentes,
presets guardados ni referencia01c. seed_presets sólo incorpora IDs ausentes.

| Preset | Intensidad antes de master | Unidad/soporte |
|---|---|---|
|08 · Local|5 × error de predicción de posición a velocidad constante, clamp0..0.45|T; derivadas/historia causales, calibración explícita|
|09 · Relacional|gain zonal × (1−I)/2, clamp0..0.45|I del modo previo relativo; sin modo/contribución válida se silencia, oposición no equivale a malo|
|10 · Angular|0.45 × angular_speed/180, clamp0..0.45|deg/s; promedio de magnitudes izquierda/derecha, exige ambos lados observados|
|11 · Colectivo|voces1–3:0.75×abs(amplitud de modo);4:0.75×residuo×velocidad global;5:0.75×cambio/30×velocidad global;6:0.75×velocidad global;clamp0..0.45|modos/speed enT/s,cambio endeg,residuo sin unidad; tres componentes/seis voces|

Ganancias iniciales exploratorias editables en Ruteos: no normalización automática
por fuente ni escalas físicas/metabólicas. Smoothing0.03s, expresión0 y transientes0
para escuchar el descriptor con el carrier sostenido; se pueden ajustar libremente.
Algoritmo y rutas quedan en preset portable como antes, sin cuerpo/video/escala.
Calibración permanece explícita y ligada a fuente/persona; no viaja en el preset. Modelos explica la relación entre
mediciones y ruteo. Colectivo necesita historia/rango suficiente: un modo faltante
queda silencioso; componentes del análisis no fijan número de armónicos.

Nueva señal aditiva zone.N.angular_speed: media(abs(velocidad angular)) bilateral.
Conserva angular_velocity firmado existente. Rotaciones opuestas podían cancelarse
en su promedio firmado; el nuevo observable mide rapidez, no dirección/intención.
Caderas/hombros/rodillas/codos mantienen ángulo interno; tobillos/muñecas describen
orientación distal COCO17, sin manos/pies/ángulos inventados. Missing/held de un lado
no se rellena con el otro. No cambia decisiones antiguas ni output baseline.

Evidencia: 59 tests modelos/routing/colectivo/runtime/API/store/replay pasan
(13,48s; deprecación AnyIO sin fallo), build TypeScript/Vite. Test de rotaciones
opuestas±1rad/s obtiene promedio firmado0 y rapidez57,2958deg/s; pérdida de muñeca
invalida destino. Fixtures por descriptor prueban soporte/ratios/seis voces/sin
modulación; seeding repetido preserva edición y configuración activa.

Se renderizó comparación local de referencia+4 modelos×60s de cacheCPU existente:
3600ticks y2880000samples@48kHz por brazo. Escala aparente de torso medida a5s de
hombros/caderas observados del slot derecho seleccionado previamente, timestamp/
sequence/generación/cachehash/unidad congelados. No metros, identidad ni 3D;
calibración sólo en esa solicitud, sin aplicarla a otro cuerpo/source o sesión live.
Todos los modelos generan audio no nulo y cada una de las seis voces tiene ticks
activos con ratios40.4×1..6 preservados. PCM y voice-frames de la referencia tienen
hashes idénticos a la comparación local anterior. No se copió/reprocesó el video.

Chrome con API/video/WAV/voice-frames reales pasa (1 test,6,1s): alterna los cinco
presets a15s en pausa y reanuda conservando tiempo/video/figura. Audio muted: sin
escucha/aceptación humana ni prueba de niveles/sincronización física. Datos/receipt
locales, servidores de prueba detenidos. Presets incorporados sólo en desarrollo,
configuración activa preservada, workspaces cotidianos intactos. Preguntas de HIT,
eficacia/intención, tracking físico y protocolos perceptuales siguen abiertas.

## Comparador: exportación local audiovisual con todos los osciladores

Implementados renderer raster, encoder FFmpeg, servicio owned con cancelación/
progreso/estado durable y API/web. Configuración portable de exportación, override
visual opcional, MKV PCM conservado o MP4 AAC. Reutiliza fuentes verificadas y
osciladores/PCM congelados, sin tracking nuevo ni cambio de configuración live.
Suma todas las voces y conserva interpolación cropped de gain/fase del replay.
No es PCM post-timbre en XY, ni membrana física. Exporta a1× sin offset del player.

Verificación de streams y cantidad de frames encontró que shortest=1 omitía el
último frame de cola; corregido usando hstack sin ese corte y duración PCM explícita.
Pruebas cubren suma seis voces, fase cropped, silencios sin punto ficticio, MKV
exacto, MP4 AAC, cancelación, restart, rutas API tipadas, descarga y corrupción.
El roadmap conserva render de otros bancos, sensores, escucha/aceptación humana y
validación de sincronía física como pendientes independientes.

## R12 · Banco de mediciones declaradas, tareas y cobertura

Contrato versionado fuente/slot/tarea/restricciones, canales/unidades/método/
incertidumbre/calibración, reloj original afín, samples con causas, intentos/outcome
y soporte común. Integra trapezoidalmente sólo pares adyacentes válidos recortados
al trial; gaps/artefactos/null/extremos sin soporte no se rellenan. Sólo W→J,
parcial si hay pérdida; HR y resultado útil separados, sin inferir calorías ni
ranking/eficiencia/HIT. Hash de soporte propio/común y cobertura por canal/trial.

API/UI/import/export/config portable/guardado/verificación/retry/restart implementados.
Vínculo opcional con EVAL verifica manifest/slot/límites del segmento al guardar;
no crea sincronización ni transferencia de cuerpo/calibración. Publicación desde
staging verificado; una escritura interrumpida no bloquea reintento ni se certifica.
Snapshot pendiente web conserva request congelado ante respuesta perdida.

Protocolo y matriz sensor/proxy/incertidumbre en R12_MEASUREMENT_PROTOCOL.md.
No hardware conectado ni datos fisiológicos humanos; sólo controles de software.
Adquisición BLE, conversiones metabólicas, intervención/participantes, pareado
científico y sincronía física siguen abiertos. R13 aún requiere entrega propia.

## R13 · Banco de transferencia reservada, sin intervención inferida

Contrato/imports/UI/settings portables, reservas temporal/toma/grupo/tarea,
equivalencia funcional/restricciones, snapshot EVAL compartido con R01 (causal/
observado/unique time/units), normalización/basis/coefs train-only. Persistencia,
media train, ridge completo/subespacio en soporte común. Adaptaciones pooled-prefix
o prefix-only con originales congelados y prefijo excluido; control train-target
shuffle. Workers own, cancel/repeat/restart, manifest/outputs verificados y traces
con origin/target/elapsed/errores/model hash. No cal/sonido live alterados.

Lectura certifica integridad, no recomputación; verify(recompute=True) y repetición
se prueban separadamente. Defaults históricos no reescriben el request archivado.
Validación real local within_take y control sintético; no otra persona/tarea ni
aprendizaje o prótesis. Protocolo R13_TRANSFER_PROTOCOL.md conserva etapas P3–P6 de
Anni, nulos/fallos y dependencias. R13 permanece abierto para datos independientes,
más modelos/equivalencias, intervención/retención y colaboración con usuario/device.

Investigación se carga con React.lazy/Suspense al abrir la pestaña: evita sumar
los bancos al bundle cotidiano. Build divide ~292kB inicial/~215kB investigación,
sin modificar controles o lógica de síntesis. Verificación browser producción y
regresión del recorrido corporal se registran en VALIDATION.md.


## Fourier corporal · diagnóstico de bloques cortos

El consumidor de la biblioteca informa las longitudes de bloques descartados
por no alcanzar el mínimo y su máximo, respetando límites de identidad/grid.
UI y servicio verificados con fixtures; backend además ejecutado sobre tracking
corporal privado ya cacheado, con selección/escala explícitas y repetición local
idéntica. No se cambiaron defaults, bridge de Oliva ni servicios cotidianos.
Ver VALIDATION.md para evidencia y límites: recorrido web de producción con cache real verificado (audio desconectado);
aceptación humana pendiente; el banco no valida HIT ni causalidad corporal.


## EVAL #18 · tandas y continuación de matriz congelada

Presupuesto de corridas nuevas por invocación configurable desde web/API/CLI;
default 1024 mantiene la matriz completa admitida. partial distingue presupuesto
agotado de resultado completo. Continuación conserva ID/entradas/corridas enteras
verificadas, recalcula la corrida inacabada desde reset/preroll y reconstruye
soporte común para toda la matriz. Locks, recuperación tras restart/cancelación,
procedencia de continuación y causas previas registrados. No auto-continuación.

Pruebas de API/workers/UI/PCM y contraste local corporal contra ejecución fresca
pasan; evidencia y límites en VALIDATION.md. Contrato y recorrido en EVALUATION.md
y RUNNING.md. No instala/mergea la pila ni acredita escucha/sincronía física,
publicación segura de paquetes seleccionados o resultados científicos.


## EVAL #18 · paquete seleccionable para revisar

UI/API y writer propio permiten resumen sin rutas/nombres/identidad/calibración,
con presets de parámetros conservados y soporte original explícito. Pedidos por
corrida, traces y PCM opt-in; fuentes ajenas, video/tracking y inputs/job metadata
externos no se agregan al ZIP. Preview congelada, presupuesto, cancelación, checksum
al descargar e inventario hasheado; preferencias JSON portables sin selección.

Pruebas backend/workers/API/UI/PCM y exportación corporal local pasan; ver
VALIDATION.md. EVALUATION/RUNNING documentan límites. Resultado listo para revisión
local; compartir externamente no fue realizado ni autorizado por este paquete.
No certifica anonimato, datos públicos reproducibles ni conclusiones científicas.

R03 incorpora un barrido configurable de offset global declarado, separado de
controles temporales: soporte común, denominadores/rangos muestreados, configuración
portable y worker reproducible. La comparación nominal no cambia. Núcleo y
recorrido Chrome/HTTP verificados (VALIDATION); incertidumbre por evento, latencia
medida y marcas humanas independientes siguen pendientes.

R12 ahora importa CSV con mapeo explícito y archivo local del original UTF-8,
metadatos/conversión/manifests; controles web y mapa portable. Usa parser compartido
con R11, cuya salida se conservó. Backend y Chrome/HTTP verificados (VALIDATION).
No adquisición/sensor real, inferencia de escala ni transferencia de calibración.

R01 suma `fixed_harmonics`, configurable en web sintética/corporal: sin/cos + DC,
frecuencias declaradas y reloj pasado, forecast congelado y soporte común. Nuevo
control positivo armónico y banco reproducible de frecuencias incorrectas/shuffle/
blanco estocástico con evidencia pública sintética. Defaults de predicción/audio
conservados. No identifica una restricción HIT física; quedan hipótesis/observables
y tomas independientes (r01_grassmann/README, VALIDATION).

R01 fixed_harmonics verificado también en dos corridas corporales locales de
60 s con la fuente/generación/cuerpo derecho previamente verificados; trazas y
inputs repetibles, sin volver a leer/copiar video/tracking ni abrir audio. Web
muestra causas de soporte y discrepancia del reloj objetivo estimado/observado.
Datos/estadísticas corporales quedan locales; no generalización ni escucha inferida.

R11/R12 incorporan un modo explícito de índices por registro para CSV sin contador:
versión 3, numérico/ISO, procedencia y presets portables. Timestamp real obligatorio,
no descarte/interpolación; device_counter_observed=false advierte que numerar filas
no detecta pérdidas físicas. Backend/API/web verificados (VALIDATION), formatos
anteriores/defaults conservados. Adquisición/exports reales siguen pendientes.

R08 permite ahora mostrar frame original exacto bajo semillas/etiquetas del
benchmark: fuente preparada compatible explícita, opt-in/cancelación y descarte
de contexto antiguo. UI/HTTP con video sintético verificados (VALIDATION). No
correspondencia automática ni nuevas referencias corporales; revisión humana
y ground truth siguen pendientes, sin cambios de síntesis o borrador manual.

R09 agrega adaptador DLT de pares 2D/cámaras K/R/t declarados, clocks/estados
explícitos, controles web/presets/export y visor 3D. Puntos inferidos, missing
con causas y control de correspondencias incorrectas/reproyección engañosa.
Core/API/Chrome/CLI sintéticos pasan. Guarda stream como declarado y ahora también
cálculos completos en workers propios cancelables, con recibos recuperables, entradas
congeladas y descargas. Undistorsión/adquisición/calibración reales e IMUs
siguen pendientes. No profundidad monocular ni cambios de instrumento.


R09 multivista: abrir un resultado en tránsito no pisa inputs editados mientras
llega; una nueva apertura explícita sí los restaura. Inventario retoma seguimiento
de workers activos tras reload y permite cancelación propia. Intentos locales
inválidos pueden descartarse sin envío. Chrome con worker real y build verificados
(VALIDATION); no cambios en síntesis/defaults ni prueba física nueva.


R09 conecta cálculos multivista completos con conversiones/comparador por ID y
manifest esperado. Publicación verifica artefactos, mantiene stream exacto y
origen local hasheado; recuperación idempotente no vuelve a resolver la fuente.
Origen no puede inyectarse por ruta declarada. UI/HTTP/contratos verificados;
no cambios a default de inferidos ni síntesis. Procedencia de cálculo conservada
sin acreditación de calibración física. Ver README R09 y VALIDATION.


R10 incorpora archivo opcional IndexedDB para snapshots de borradores, con
export/restore/delete explícitos, dedup del mismo JSON y checksum al leer. No
reemplaza automáticamente borrador ni pending, no revive player ni envía. Chrome
verifica cierre de pestaña y nueva pestaña, recuperación exacta y posterior guardado
explícito en API real. Límites de almacenamiento y privacidad documentados; ningún
nuevo default/sonido/telemetría ni exposición humana acreditada.


R05 recorrido audiovisual corporal para resonador+mapeo verificado en Chrome sobre
bundle/runtime/biblioteca reales con PCM muted, source/pose/figura de seis voces,
seeks/pausa/offset/cola y soporte común no vacío. Fixture reutilizable lee una EVAL
existente sin mutadores/copia/retracking y guarda nuevos R05 sólo en root separado.
Datos/evidencia corporal permanecen locales. VALIDATION/RUNNING describen alcance;
no escucha, precisión 3D, causalidad ni timing físico acreditados. Sonido/defaults
productivos y workspaces cotidianos intactos.


R04 recorrido corporal congelado con escala aparente/procedencia ya archivadas
verificado en web/reader/workers: dos corridas de60s repetibles, seis condiciones
sobre soporte común y faltantes preservados. Evaluación sin escala rechazada,
calibración runtime sigue null. Escala no se infiere/transfiere; datos y artefactos
quedan locales. Software verificado no sustituye tarea/anotación independiente,
medición de ruido ni validación física/HIT (VALIDATION/README R04).


Arranque de desarrollo explícito disponible: start-laboratory-development.sh usa
Shaper-dev y perfil de datos separado, conservando comando cotidiano. Ambos wrappers
muestran checkout/head/interpreter/modelo y --describe permite revisar sin servicios.
Selecciones explícitas inválidas no caen en otro workspace/modelo. Scripts verificados
con executables inertes y resolución real; R24/readiness/escucha son pendientes físicos.
RUNNING distingue comandos/perfiles; no nueva pila instalada ni merges realizados.

Arranque completo sin audio de la pila dev verificado con datos temporales: web,
estado, presets, ACK de controles y cierre de ambos procesos. Modo --no-audio
explícito en UI/diagnóstico, sin telemetría ficticia ni 503 esperado como fallo;
errores reales de control conservados. No puede deshabilitar un Shaper externo.
Un único perfil start-laboratory-dev.sh conserva puertos 8875/8185 y datos dev;
start-laboratory-development.sh es alias, no una instalación alternativa.
23 pruebas backend/shell y Chrome real de producción pasan; R24, tracking físico
y escucha siguen pendientes. VALIDATION/RUNNING contienen alcance y recorrido.

R13 añade ridge cuadrático opcional (default off), train-only y soporte común con
baselines/adaptación/shuffle; UI/settings portables y positivo sintético conocido.
16 tests, Chrome producción/worker real y banco público de tres condiciones pasan.
El control separa una no linealidad simple de una posible ventaja de descriptor;
no acredita transferencia entre cuerpos/tareas ni HIT. Datos privados y sonido
no modificados. Protocolo/evidencia R13 preservan casos sin mejora y dependencias.

LAB-09: panel de captura ya no oculta fallos de consultas de estado. Inventario
pendiente/fallido se distingue de idle, conserva último estado y bloquea nuevos
pedidos respectivos hasta reconciliar; stop/cancel conocidos no se bloquean.
Una consulta por grupo y recuperación sin operaciones automáticas verificados
en Chrome con HTTP503/demoras controladas. Backend y sonido intactos; validación
física/cámara/R24 y sincronía siguen pendientes.

EVAL #18 comparte consultas confirmadas con captura: inventario pendiente/fallido
visible, progreso anterior conservado, repetir/continuar/iniciar bloqueados hasta
reconciliar y cancelación de corrida conocida disponible. Dos recorridos Chrome
con fallos/demoras e inventarios explícitos verifican acciones sin nuevos jobs.
Motor, resultados, reproductor y sonido no cambian; aceptación física sigue pendiente.

EVAL #18: perfiles de procesamiento con nombre, SQLite y JSON portable implementados.
Controles reloj/preroll/tandas/PCM independientes de selección fuentes/presets/cuerpos/
calibración e identidad renderer. Cargar no inicia ni modifica requests congeladas;
carga demorada no sobrescribe ediciones posteriores. 30 tests backend y Chrome
producción/API pasan. Instrumento/defaults intactos; instalación cotidiana/escucha
y reservas científicas pendientes.

LAB-00–08: corregido traspaso de escala al cambiar automáticamente de persona
entre prefijo y tracking completo. Calibración histórica conservada; nuevo cuerpo
requiere escala propia, mientras cuerpo explícito estable mantiene su medición.
Runtime10/evaluación20 tests pasan. Elección derecha del clip local verificada y
registrada sólo en desarrollo, sin tocar preferencia cotidiana/calibraciones ni
copiar/retrackear medios. Sigue pendiente precisión/escucha/aceptación física.

El descarte automático de una escala activa ahora informa su motivo en web/state.
Aviso temporal, sin bloquear baseline, limpio al recalibrar/seleccionar/cambiar
fuente; selecciones sin escala no producen aviso. Runtime12 tests y build pasan.
Defaults y comportamiento musical intactos; escucha física pendiente.

R12: lecturas raw negativas de HR/potencia metabólica pueden conservarse sólo con
exclusión explícita del mismo canal/muestra. Intervalos afectados no integrados;
sin causa y no finitos rechazados. Potencia mecánica firmada sigue válida.
29 tests R12/CSV pasan, incluyendo API, archivo/reapertura/recomputación y soporte
común. JSON/web actuales permiten declarar la causa; CSV no tiene exclusiones por
fila. Sin cambios de controles/defaults/audio ni datos humanos nuevos.

R12 web: resultados de inspección, reapertura de corridas, vínculo EVAL y carga
CSV archivada comprueban que el protocolo no cambió durante el await. Cambios
posteriores conservados con aviso; repetir aplica normalmente. Chrome producción
con API/archivos reales y respuestas demoradas verifica tres cruces, incluida
ausencia de resultado guardable obsoleto; build pasa. Instrumento/defaults intactos.

R12: banco configurable web/API/CLI de sensibilidad del reloj declarado con
offsets congelados, cobertura original y común entre condiciones/canales, archivo
request/result/manifest idempotente, reapertura/recomputación y configuración
portable. Dos controles sintéticos repetidos (incluido soporte vacío) publicados.
41 tests R12/CSV y dos recorridos Chrome pasan; build94 módulos. Mediciones reales,
calibración/sincronía físicas y eficiencia/aceptación siguen pendientes.

Instrumento web actual: recorrido corporal con cache existente verifica cuatro
presets/modelos afinados, calibración, seis targets, edición de componentes/
referencias/joints y peso de ruteo mientras el video avanza. Peso cero silencia
sólo la voz elegida; recuperación, preset portable y cambio de cuerpo/loop pasan.
Chrome11.3s; fixture no sintetiza ni abre dispositivos y prohíbe retracking.
Cache original intacto, datos privados locales; sonido/aceptación siguen pendientes.

Web: respuesta demorada de aplicar preset ya no reemplaza draft/revisión tras una
edición posterior ni ante una revisión más nueva confirmada. Regresión reproducida;
tres escenarios Chrome con API real/WS retenido pasan, más recorrido corporal
completo11.6s con bundle nuevo. Sin defaults/audio/backend modificados.

Fuente/cobertura web: cada informe queda vinculado al job activo; respuestas y
errores demorados de jobs anteriores ignorados tras cambio/cleanup. Dos regresiones
reproducidas y corregidas; Chrome con cobertura real cacheada y captions de fault
control pasa junto al recorrido corporal completo. Sin tracking/defaults/audio
modificados; cache original intacto, precisión/escucha siguen pendientes.

Inventarios web: lecturas demoradas de biblioteca/presets/calibraciones ya no
reemplazan lecturas más recientes ni muestran errores obsoletos. Dos regresiones
Chrome reproducidas y corregidas con API/SQLite reales; sin defaults/backend/audio
modificados. Pendiente separado identificado: dos aplicaciones de preset que se
solapan pueden producir conflicto de revisión; no se reintenta silenciosamente.

Presets rápidos: resuelto el solapamiento propio de apply registrado en #143;
una solicitud en curso y última elección pendiente, revisión confirmada antes de
la siguiente. Ediciones posteriores descartan elección pendiente; errores visibles
sin retry. Seis pruebas Chrome reales y build pasan; sin defaults/audio modificados.
No representa una cola universal para todas las escrituras ni elimina conflictos
con otras ventanas o controles anteriores a una confirmación de revisión.

R13: comparador web/API read-only de2–6 corridas, mismo input/contexto y settings
variables, sobre pares origen/objetivo idénticos; MSE/deltas/exclusiones/soporte y
JSON local con procedencia.23 pruebas backend y4 Chrome pasan, controles sintéticos
publicados; coincidencia con cálculo corporal privado de #145. Sin datos privados,
refit/defaults/audio/aceptación modificados; reservas independientes siguen pendientes.

LAB-09: control digital AAC preview independiente del MKV exacto, tres bitrates y
offsets±100ms, transiente/PTS decodificados y receta sintética repetida.38 pruebas
capture/export/timeline y3 Chrome (audio offline, frame HTML presentado, muted)
pasan. No equivale a sincronía física/escucha ni cambia defaults o instrumento.

EVAL: cambio de cuerpo en un segmento descarta su calibration_id anterior; otras
copias y ediciones del intervalo conservan sus escalas. Dos regresiones de payload
web reproducidas/corregidas y build pasan. Backend conserva rechazo de calibración
ajena; sin defaults/instrumento/medidas nuevos.

R01/R02: vista live configurable de base/proyector colectivo ya producido por
el núcleo causal. Escala de color fija, ejes/modos explícitos, amplitudes,
residuo, ángulos y JSON observado; explica falta de soporte y baseline.
Preset portable conserva vista/recorte, default apagada. Pruebas de runtime
conservan modelo/historial/targets en edición visual; recorrido Chrome sobre
cache corporal read-only verifica matrices/controles/preset y seis voces.
Es visualización de features de velocidad, no reconstrucción3D ni prueba HIT.

R01: comparación web/API de2–6 corridas guardadas sobre entradas congeladas
idénticas, con selección explícita objetivo u origen/objetivo, soporte por
control/familias comunes, exclusiones/MSE/deltas/JSON y procedencia. 49 pruebas
R01/backend más regresión histórica adicional; dos Chrome nativos y build pasan.
Receta sintética repetida publicada; cuatro corridas corporales históricas
comparadas localmente sin cambios en sus archivos. Request JSON se compara
mediante contratos para evitar rechazo0 frente a0.0. Sin refit/instrumento/
aceptación/HIT; reservas y familias adicionales conservan su agenda.

R03: comparador web/API read-only de señales/centros archivados contra idéntico
corte de marcas y contexto, matching y cobertura declarada. Intersección de
soporte entre condiciones; conserva métricas individuales, denominadores,
umbrales/unidades/candidatos/procedencia. Inventario de nuevas corridas identifica
señal/crop/conteo sin cargar todas las traces.45 pruebas backend/temporal y2 Chrome
pasan, receta sintética repetida pública. No marcas humanas nuevas, tracking,
sonido, offset óptimo, centro causal ni validación Jpsh/HIT.

</details>
