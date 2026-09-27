---
project: harmonic-weaver
title: MANIFEST — movement-consonance research pack
type: manifest
tags: [research, movement-consonance, laban, harmonic-weaver, harmocap, hit]
date: 2026-09-24
confidence: high
---

# MANIFEST — agent reports: Consonancia del movimiento corporal como control musical

> 2026-09-24 · 5 research subagents en paralelo, división no-solapada.
> Cada agente escribe su reporte crudo directamente en su propio archivo, con su propia sección Sources.

## Framing (lo que todo agente asume)

Contexto del proyecto: la tribu AlterMundi construye el Harmonic Beacon — un sistema
donde cuerpos en movimiento (capturados por cámara con HarMoCAP/YOLO-pose, COCO-17
keypoints) activan una serie armónica (sintetizador aditivo, scsynth, salida binaural
por R24). El modo actual mapea POSICIÓN de muñecas sobre teclados virtuales (bands/
pads) a armónicos.

La investigación sirve al diseño de un NUEVO modo: **consonancia del movimiento**.
Idea central de Nicolás Echániz (co-autor de Harmonic Information Theory, HIT):

- Cada joint del cuerpo se asocia a un armónico de la serie (F0 en pelvis, F1 bajo el
  ombligo, etc. — el mapeo anatómico exacto es parte del diseño).
- El sistema OBSERVA el movimiento: aceleración de cada joint, vectores de dirección,
  continuidad rítmica.
- Si un joint participa "consonantemente" (su energía cinemática es aprovechada 100%
  por el sistema), su armónico suena afinado.
- Si se desafina: frenado por resistencia → desafina hacia grave; acelerado por
  iniciativa propia en disonancia → desafina hacia agudo. Límite: ±50% del salto al
  armónico vecino (serie 40/80/120 Hz: 40 puede ir de 20 a 60; 80 de 60 a 100...).
  Entre modos afinados y desafinados, un cuerpo puede activar todo el continuo de
  frecuencias.
- Snap definible hacia los modos afinados.
- Baseline experimental propuesto: medir la matemática de movimientos que los humanos
  percibimos como consonantes (eficacia + sensualidad — ej. una bailarina, un artista
  marcial), porque esa percepción de placer visual ES la consonancia perceptual.

Audiencia del pack: Nicolás + Mariano (HIT) + agentes de la tribu que implementarán
el modo en harmonic-weaver / HarMoCAP / harmonic-shaper. Profundidad: mapa de estado
del arte + diseño operacional inicial + protocolo de experimentos; NO tratado
exhaustivo. Out of scope: implementación de código (viene después), temas de audio
espacial binaural (ya resueltos en beacon-spatial).

Hecho clave del código existente (para R5): HarMoCAP ya emite 24 features por OSC
incluyendo `laban_weight_proxy`, `laban_time_proxy`, `laban_space_proxy`, `qom`,
`smoothness_l/r`, `symmetry`, `contraction`, `expansion`, `tempo_bpm`, `beat_phase`,
ángulos de 8 joints. El schema declara explícitamente que los proxies Laban son
"operacionalizaciones cinemáticas, no mediciones Laban canónicas".

## Division of labour

| # | File | Focus | Resumen del brief |
|---|---|---|---|
| 1 | `01_laban-movement-analysis.md` | Laban Movement Analysis canónico | Effort (Weight/Time/Space/Flow), Shape, Kinetography/Labanotation; cómo se define y mide "calidad de movimiento"; operacionalizaciones computacionales existentes y su validez; relación Laban↔percepción de fluidez/eficiencia |
| 2 | `02_movement-to-music-systems.md` | Sistemas movimiento→música | Estado del arte de instrumentos/instalaciones con pose tracking (Kinect, MediaPipe, YOLO); taxonomía de mapeos de Wanderley & Hunt (1:1, divergente, convergente, complejo); sonificación de danza; qué estrategias sobreviven en performance real |
| 3 | `03_movement-consonance-math.md` | Matemática de la eficiencia/consonancia del movimiento | Minimum-jerk model (Flash & Hogan), jerk como medida de suavidad, sincronía de fase entre joints, cross-correlación, coupling functions, fluidez perceptual (por qué el movimiento eficiente da placer visual), métricas cuantificables candidatas para "consonancia" |
| 4 | `04_continuous-pitch-expression.md` | Pitch continuo y desafinación expresiva | Pitch-bend/detune/glide en síntesis e instrumentos; mapeo cinemática→desviación de frecuencia en sistemas existentes; series armónicas y desafinación de parciales (just intonation, inharmonicity, stretched tuning); percepción de "afinado vs desafinado" en contextos armónicos |
| 5 | `05_internal-hit-baseline-design.md` | Carril interno: HIT + nuestro código + diseño baseline | Qué significa consonancia en HIT (interferencia, acople estable, intervalo como portador); inventario de features OSC existentes; boceto operacional del modo consonancia (joints→armónicos, detección de aceleración, regla ±50%, snap); protocolo de experimentos con video |

## Confidence legend

| Mark | Significado |
|---|---|
| ✅ | Fuente primaria / peer-reviewed / texto oficial (paper, libro, standard, código del repo) |
| 📊 | Fuente secundaria especializada (survey, tesis, documentación técnica de proyecto) |
| 📰 | Prensa / blog / divulgación |
| ⚠️ | Contestado / draft / no verificado independiente |
| ❓ | Inferencia del agente sin fuente directa — debe verificarse |

## Source tags

[R1] = 01 laban · [R2] = 02 movement-to-music · [R3] = 03 math · [R4] = 04 pitch · [R5] = 05 interno

## State

`closed` — lanzado 2026-09-24, cerrado 2026-09-27. R2 y R3 fueron relanzados una vez:
los agentes originales agotaron su presupuesto de web_search sin escribir archivo
(50 búsquedas exploratorias, 0 escrituras). Los relanzamientos con fuentes semilla
directas + presupuesto duro (12-15 búsquedas) + regla "escribir el archivo temprano,
actualizar seguido" funcionaron: R2 usó 13/15 búsquedas, R3 usó 2/12. Lección para
futuros fan-outs de investigación: dar URLs semilla explícitas y exigir escritura
incremental del archivo desde el primer minuto.

Consolidaciones producidas: SYNTHESIS.md · CROSS_REPORT.md · NARRATED_REPORT.md ·
BIBLIOGRAPHY.md (131 URLs únicas) · README.md · ../INDEX.md.

## Consolidations to produce at close

SYNTHESIS.md · CROSS_REPORT.md · NARRATED_REPORT.md · BIBLIOGRAPHY.md · README.md
