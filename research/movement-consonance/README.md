---
project: harmonic-weaver
title: "Investigación — Consonancia del movimiento como control musical"
type: research-index
tags: [research, movement-consonance, index]
date: 2026-09-24
confidence: high
---

# Investigación — Consonancia del movimiento como control musical

> Cómo convertir input de posición/movimiento corporal en interpretación musical, y el diseño de un nuevo modo de harmonic-weaver donde la consonancia (eficiencia/coordinación) del movimiento — no la posición sobre teclados virtuales — gobierna la activación armónica y la desafinación expresiva.

## Qué se investigó

Idea semilla de Nicolás Echániz: cada articulación del cuerpo se asocia a un armónico de la serie (F0 en la pelvis hacia arriba); el sistema observa aceleración, vectores de dirección y continuidad rítmica; el movimiento consonante (energía 100% aprovechada por el sistema) suena afinado; el frenado por resistencia desafina hacia el grave y la aceleración propia desfasada hacia el agudo, con límite de ±50% del salto al armónico vecino y snap configurable. Baseline: medir la matemática de los movimientos que los humanos percibimos como consonantes por su eficacia y sensualidad.

Cinco carriles no-solapados:

1. [R1] Laban Movement Analysis como teoría canónica de la calidad del movimiento (Effort, Shape, Space Harmony, certificación, operacionalizaciones computacionales y sus techos de validez).
2. [R2] Sistemas movimiento→música: taxonomía de mapeos (Hunt–Wanderley–Kirk), 40 años de instrumentos e instalaciones, sonificación de danza, modos de fallo documentados.
3. [R3] Matemática de la consonancia del movimiento: minimum-jerk y sus límites, SPARC/LDLJ, fase relativa y HKB, Kuramoto/PLV/lenguas de Arnold, estética empírica del movimiento, 5 métricas candidatas con fórmulas y patologías.
4. [R4] Pitch continuo y desafinación expresiva: problema theremin, Sethares/Plomp-Levelt, aritmética de cents de la regla ±50%, snap y cuantización, síntesis aditiva con frecuencia por parcial, prior art.
5. [R5] Carril interno: consonancia en HIT, inventario de código de los 4 repos, mapeo anatómico COCO-17→armónicos, regla de detuneo formalizada, protocolo completo del experimento baseline.

## Cuándo / quién

2026-09-24 (lanzamiento) → 2026-09-27 (cierre). Coordinación y consolidación por CompAII; investigación cruda por 5 subagentes paralelos (R2 y R3 relanzados una vez tras agotar presupuesto de búsqueda sin escribir — ver MANIFEST). A pedido de Nicolás Echániz.

## Estado

`closed` — 5 reportes archivados, consolidaciones producidas. Implementación NO comenzada: espera las 6 decisiones de Nicolás (CROSS_REPORT §H).

## Estructura

```
movement-consonance/
├── README.md              ← este índice
├── SYNTHESIS.md           ← destilado de 2 páginas: las 8 cosas que importan
├── CROSS_REPORT.md        ← denso, taggeado [R1..R5], para recuperación por LLM
├── NARRATED_REPORT.md     ← "El cuerpo que afina" — la lectura humana en prosa
├── NARRATED_REPORT.pdf    ← el narrado tipografiado (5 pp)
├── ADDENDUM-f1-2-grid.md  ← 2026-09-27: la regla ±50% aterriza en la serie de f1/2
│                             (enmienda a CROSS_REPORT §A.6/§B/§D/§G/§H tras
│                              aclaraciones de Nicolás: disonancia = desvío
│                              intencional de la inercia; detune = otra nota de
│                              la rejilla, no desafinación)
├── BIBLIOGRAPHY.md        ← 131 URLs únicas deduplicadas, agrupadas por carril
└── agent_reports/
    ├── MANIFEST.md        ← plan de registro, framing, leyenda de confianza
    ├── 01_laban-movement-analysis.md
    ├── 02_movement-to-music-systems.md
    ├── 03_movement-consonance-math.md
    ├── 04_continuous-pitch-expression.md
    └── 05_internal-hit-baseline-design.md
```

## Hallazgos principales

- El modo consonancia ocupa un hueco real y documentado del espacio de diseño: nadie publicó calidad-de-movimiento → desafinación continua de serie armónica; la teoría de mapeos (Hunt–Wanderley–Kirk, >4000 tests) recomienda textualmente derivadas del gesto ligadas a la energía del performer.
- HIT ya contiene la definición: consonancia = acople estable con baja carga correctiva; el detuneo es el registro audible de la carga correctiva por articulación.
- Coordinación motora = phase-locking = consonancia armónica: misma matemática (Kuramoto/PLV/HKB); el snap es un ancho de lengua de Arnold.
- La regla ±50% es psicoacústicamente certera (cae sobre el pico de rugosidad de Sethares) pero el tope completo segrega el parcial en armónicos medios: se recomienda límite por armónico (~±15-70 cents de banda fusional-expresiva).
- El discriminador grave/agudo tiene fórmula simple: potencia mecánica firmada P=⟨a,v⟩ (negativa=frenado→grave; positiva fuera de fase=bombeo→agudo).
- Anclaje Laban legítimo = Choreutics/Space Harmony (metáforas musicales explícitas de Laban), NO Effort (intención no medible desde cámara; α de Krippendorff 0.46).
- El 70% del camino de código ya existe; el hueco crítico es una sola capability de detuneo por voz en el contrato OSC del shaper (el motor ya modula frecuencia con fase continua).
- El experimento baseline (medir la matemática del placer visual) es ejecutable hoy: 12-18 clips en 3 categorías → HarMoCAP jsonl → métricas offline → Spearman contra ratings ciegos 1-7.

## Pendiente

- Las 6 decisiones de diseño de Nicolás (CROSS_REPORT §H): mapeo anatómico, límite por armónico, snap inicial, forma del drive d_j, corpus+consentimientos, destino shaper.
- Verificación en vivo de latencia OSC→audio (estimada 45-55 ms).
- Implementación: capability de detuneo en shaper → script de métricas → corpus+ratings → expander `consonance_body` + escena → prueba con performer.
