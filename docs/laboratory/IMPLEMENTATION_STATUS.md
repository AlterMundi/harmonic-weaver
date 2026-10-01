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
