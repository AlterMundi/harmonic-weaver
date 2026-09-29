# Implementación: estado comprobado

2026-09-29. Objetivo activo: primera iteración local en integración. La aceptación
humana y escucha no se dieron por realizadas.

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
- Shaper: **7 tests específicos**, reconstrucción 1/6/32 voces, lease, release y API.
- UI: **5 pruebas Playwright**: suma polifónica 1/6/32, grosor geométrico y recorrido
  de edición en navegador, revisión reconocida por Shaper y guardado de preset.
- Cámara física: captura/inferencia produjo frames recientes, sin error del worker;
  cerrada después del smoke. No equivale a una sesión corporal aceptada.
- Fragmento frontal real de 12 s: 359 frames cacheados. Los cinco modelos alcanzaron
  seis voces efectivas, sin errores de runtime; colectivo y propagación alcanzaron
  estado observado. Las medidas iniciales son RTT de control/edad de telemetría,
  no latencia física movimiento→sonido.

Los cuatro fragmentos locales (perfil/espalda/frente/sin soga) suman unos 21 MB.
El original grande permanece en Downloads sin duplicar. Video, frames, screenshots
con cuerpo y tracking privado no se incorporan al repo ni a GitHub.

## Verificación pendiente antes de entregar

1. Completar tracking/reapertura de los otros ángulos, forzado y cambio de fuente;
   recorrido web con figura y video reales, presets/macros y recuperación.
2. Verificar ruta efectiva JACK/PipeWire (ALSA en este host puede producir silencio
   aunque el callback esté activo). Separar medidas de software y físicas.
3. Sesión prolongada y diagnóstico de latencia/jitter/backlog. Documentar límites
   observados y qué queda para escucha/aceptación humana.
4. Actualizar PRs/issues y dejar sesión local lista para probar.

Grabación opcional, evaluación formal y sensores siguen en la agenda posterior.
