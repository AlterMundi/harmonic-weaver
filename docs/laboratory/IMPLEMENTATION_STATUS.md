# Implementación: estado comprobado

2026-09-29. Segunda iteración local y primer comparador disponibles para feedback.
La aceptación anterior de 01c/contraste se conserva; la escucha de realce ×10,
articulación y modelos nuevos sigue pendiente. [Evidencia y límites](VALIDATION.md).

## Estado vigente de las ramas de desarrollo (auditoría 2026-09-30)

Los apartados fechados posteriores conservan historia; sus pendientes pueden estar
resueltos por incrementos posteriores. Esta tabla resume el estado actual, sin
confundir rama publicada con instalación, merge ni aceptación humana.

| Entrega | Evidencia / alcance actual | Pendiente real |
|---|---|---|
| LAB-00–08 y v2 | PRs #29/#30/#37/#39; controles, modelos, cache y cuerpo por defecto; experiencia baseline previamente aceptada | Calibración/modelos/realce nuevos y latencia requieren feedback humano; CUDA no se declara reparado |
| Comparador #18 | #40 motor PCM compartido, #41 reproducción fuente/WAV/figura y #54 descarga verificada de features/targets/configuración; repetibilidad local documentada | Ampliar evaluación/paridad/métricas y validación humana; investigación formal no completa |
| LAB-09 #17 | #42–47 colector, export, preview cámara y recovery PCM/journal; #57 prefijo de imágenes y #67 export de prefijos PCM/journal/cámara; preview MP4 opcional con reproducción web verificada | Overlays, cámara física/sincronía medida, recovery in-flight por job polling, recorrido navegador–servidor de prefijos y journal completo |
| R03 técnico | #68 marcas tipadas y snapshot; #69 contraste causal, servicio propio, API/UI, shifts declarados sobre soporte común y browser→HTTP→replay verificado con fixture sintética | Revisión humana, incertidumbre de anotación, centros/regiones alternativos y experimento reservado; no cierre científico |
| R04 técnico | #70 valida datos relacionales; #71 banco sintético y pose congelada, worker/API/UI, controles globales/local proximal, JSON portable y browser HTTP probado | Corrida corporal real requiere evaluación con escala/procedencia explícitas; anotaciones independientes, ruido/emparejamientos y valor de tarea pendientes |
| R05 técnico | #72 núcleo resonadores pasivos/excitación causal, mapeo amplitud con modulación opcional de portadoras/serie f1/2, comparación con soporte común/colas separadas, PCM DOUBLE y manifests verificados, worker/API/UI/presets y cuadratura exacta por voz; proyección/caché/presets y player ligado al clock; video original verificado, offset portable y overlay de pose causal con edad configurable; Chrome HTTP muted con seeks/loops/respuestas demoradas y gaps sobre pose/MP4 sintéticos pasa; interrupciones entre cada promoción y reverificación final cubiertas | Modalidades adicionales, prueba corporal del recorrido audiovisual, durabilidad ante caída del host/corte de energía, niveles/latencias físicas y escucha/agencia humanas pendientes; no equivalente al Shaper aceptado ni cierre científico |
| R06 técnico | Banco CLI sintético: cuatro calendarios, igual dosis/eventos/medio, métricas completas, trace acotado y manifest reproducible; worker/service/verificador con cancelación/restauración y pruebas de proceso real; API/UI completa de parámetros y JSON portable, Chrome real de repetición/tabla/trace/reload y contraste de medios con eventos/dosis/portadoras idénticos; surrogates seeded preservan multiset de intervalos y soporte; banco de semillas explícitas, reports completos y resumen descriptivo | Controles de fase/espectro e hipótesis/protocolo físicos/humanos; no cierre HIT |
| R07 técnico · PR #74 | Membrana sound-only y RMS causal, trayectoria/audio-follow/seek/pause/loop, presets visuales portables; mix R05 single/par verificado; bancos de transferencia/resoluciones y transientes con artifacts/API/UI; Chrome HTTP real de los tres paneles; cancelación running y kill post-publicación reales; 52 pruebas backend/API pasan | Recuperación de atributos en soporte reservado, convergencia física y protocolo/medio/sensores calibrados; escucha/aceptación humana pendientes; no cierre científico |
| R01–R13 | Agenda conservada; banco R01 con controles pareados, horizontes, cancelación y entrada de features congeladas; repetición sintética y corporal local; Sai–Oliva #36 revisado sin merge | Hipótesis HIT específicas y evaluación ampliada; bancos/experimentos R02–R13 y sus dependencias aún pendientes |

Desarrollo permanece en `harmonic-weaver-dev` y `harmonic-shaper-dev`; no sustituye
el workspace `harmonic-weaver-lab` de pruebas ni workspaces originales. PRs listadas
siguen abiertas en GitHub; no se ejecutaron merges. Los datos privados no se publican.

Auditoría posterior a #67: 64 tests Weaver de captura/recuperación/export y 15
Shaper pasan; [alcance y límites](INTEGRATION_AUDIT.md). No equivale a validación
de hardware ni aceptación humana.

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
