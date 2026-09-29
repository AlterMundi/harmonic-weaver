# Implementación: estado comprobado

2026-09-29. El objetivo sigue activo; la primera iteración todavía no está lista.

## Publicado

- Baseline Weaver: PR #29 (`feat/laboratory-baseline`), 184 tests + 4 subtests.
- Dependencia HarMoCAP: AlterMundi/HarMoCAP#1 (`feat/laboratory-capture-baseline`),
  8 tests específicos; seis fallos de suite ampliada por Gradio ausente declarados.
- Integración en curso: PR #30 (`feat/laboratory-live`), apilada sobre #29;
  incorpora el plan #28. Workspace de construcción: checkout `harmonic-weaver-lab`.

## Código y evidencia actual

LAB-01: contratos/schemas/fixtures, persistencia transaccional, revisión/conflictos,
presets independientes de fuente/calibración, undo/redo, macros y API HTTP/WS.

LAB-02: worker real HarMoCAP + PyAV, cache por identidad de contenido/modelo/código,
generaciones atómicas/cancelación/fallback, biblioteca y transporte con epochs.
MP4 VFR sintético pasó por el worker real y tuvo cache hit al reabrir. La prueba
automática de decoder contrasta todos los PTS con ffprobe. LiveCamera aún requiere
recorrido físico e integración con la mesa.

LAB-06/07, piezas matemáticas (aún sin conexión a runtime/UI): derivada causal
por regresión, interferencia I/R/A de Anni con historia estrictamente anterior,
unwrap/predicción angular, coordenadas relativas y missingness por joint;
adaptador del baseline comprobado contra el controlador original sin emitir audio;
subespacio SVD entrenado solo con pasado, proyector/amplitudes/residuo,
Procrustes/ángulos principales, detección de corte degenerado y candidatos de
activación regional simultáneos. No se implementó todavía el estimador retardado
de propagación/centros ni se atribuye causalidad a estos candidatos.

LAB-03/04: matriz preparada con catálogo/unidades, mezclas explícitas, curvas,
clamps, smoothing, mute/solo y seis voces independientes de PCA. Cliente Shaper
con último estado, revisión reconocida y lease de voces propias. Telemetría nativa
publicada en [Shaper PR #2](https://github.com/AlterMundi/harmonic-shaper/pull/2):
sample index, fases y ganancias/envolventes efectivas antes de shape/limiter.
Reconstrucción automática de bloques con 1/6/32 voces; dispositivo físico pendiente.

Modelos conectados a FeatureFrame y ruteos; runtime de archivos/cámara con controles
HTTP, calibración explícita y reinicio de historia ante discontinuidades. La prueba
de integración de runtime usa fuente/audio dobles: pausa, seek, loop, pérdida de
cuerpo y cambio de master. No constituye todavía un recorrido audiovisual real.

42 tests del laboratorio pasan en una corrida, más una prueba nueva de runtime.
Son evidencia de las piezas cubiertas; no
sustituyen el recorrido web, el audio, la cámara ni aceptación humana.

## Siguiente tramo necesario

1. Conectar algoritmos y registro/descriptores; completar predicción retardada y
   scores de centros frente a historia propia, sin fuga de futuro.
2. LAB-03: revisar preparación/intercambio de modelos en caliente y validar runtime
   con fuentes/audio reales; contratos y matriz ya están conectados.
3. LAB-04: construir figura polifónica WebGL sobre telemetría nativa ya publicada.
4. LAB-05: React/TypeScript, selección/upload de video/cámara, progreso/reprocesar,
   transporte, presets, controles/ruteos/macros y diagnóstico de señales.
5. LAB-08: launcher sin terminar procesos ajenos, integración local, pruebas web,
   fuentes reales, medidas de latencia, presets iniciales y recorrido para Nicolás.

Mantener grabación opcional, evaluación formal y sensores fuera de esta entrega.
El goal solo se completa cuando ese recorrido esté funcionando y verificado;
la escucha/aceptación humana que falte se identifica expresamente.
