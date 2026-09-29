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

31 tests del laboratorio pasan. Son evidencia de las piezas cubiertas; no
sustituyen el recorrido web, el audio, la cámara ni aceptación humana.

## Siguiente tramo necesario

1. Conectar algoritmos y registro/descriptores; completar predicción retardada y
   scores de centros frente a historia propia, sin fuga de futuro.
2. LAB-03: compilar rutas/unidades antes de aplicar revisiones, runtime a ticks,
   preparación asíncrona, calibración y transporte; liberar voces ante gaps.
3. LAB-04: telemetría efectiva desde AudioEngine de Shaper, en su repo propietario,
   sample index/fases/envolvente/gain real y figura polifónica WebGL.
4. LAB-05: React/TypeScript, selección/upload de video/cámara, progreso/reprocesar,
   transporte, presets, controles/ruteos/macros y diagnóstico de señales.
5. LAB-08: launcher sin terminar procesos ajenos, integración local, pruebas web,
   fuentes reales, medidas de latencia, presets iniciales y recorrido para Nicolás.

Mantener grabación opcional, evaluación formal y sensores fuera de esta entrega.
El goal solo se completa cuando ese recorrido esté funcionando y verificado;
la escucha/aceptación humana que falte se identifica expresamente.
