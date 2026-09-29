# Implementación: estado comprobado

2026-09-29. Primera iteración local disponible para feedback. La aceptación
humana y escucha siguen pendientes. [Evidencia y límites](VALIDATION.md).

## Publicación

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
