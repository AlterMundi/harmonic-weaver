---
project: harmonic-weaver
title: "SYNTHESIS — Consonancia del movimiento"
type: synthesis
tags: [research, movement-consonance, synthesis]
date: 2026-09-24
confidence: high
---

# SYNTHESIS — Consonancia del movimiento como control musical

> Destilado humano (~2 pp). Detalle en CROSS_REPORT.md (denso) y NARRATED_REPORT.md (prosa). Reportes crudos en agent_reports/.

## Las 8 cosas que importan

1. **La idea es nueva de verdad.** No existe ningún sistema publicado que mapee calidad de movimiento a desafinación continua de una serie armónica. Los vecinos (OtoKin, Adaptun, EyesWeb) validan las piezas por separado; la combinación es territorio inexplorado.

2. **La teoría de mapeos musicales PIDE exactamente esto.** Hunt–Wanderley–Kirk midieron en >4000 tests que los mapeos con derivadas del gesto relacionadas con la energía del performer superan a los teclados-virtuales 1:1 — y lo recomiendan textualmente para la próxima generación de instrumentos. El modo actual (bands/pads) es el piso de esa taxonomía; el modo consonancia es el techo que la literatura anticipa.

3. **HIT ya contiene la definición.** Consonancia = acople estable de dos procesos oscilatorios con baja carga correctiva. El cuerpo es un proceso oscilatorio (cada articulación tiene ciclos de aceleración/frenado + un ritmo global); la serie armónica es el otro. El detuneo es el registro audible de la carga correctiva. La intuición de Nicolás ("energía 100% aprovechada", "placer visual por eficacia") es HIT Cap.8 y Cap.9 aplicado — no una metáfora suelta.

4. **Coordinación corporal ES phase-locking, la misma matemática que la consonancia armónica.** Kuramoto, PLV, lenguas de Arnold, atractores de Kelso a 0°/180°. El parámetro de snap es literalmente un ancho de lengua de Arnold. Y hay evidencia musical directa: en cuartetos de cuerdas, el acople del balanceo corporal predice la bondad percibida de la ejecución.

5. **La regla ±50% de Nicolás es psicoacústicamente certera, con una corrección.** El tope ±f1/2 cae justo sobre el pico de rugosidad de Plomp-Levelt/Sethares (la zona más áspera) — el recorrido afinado→desafinado barre batido→rugosidad→segregación, exactamente el arco expresivo buscado. Corrección: a tope completo los armónicos medios se segregan y se oyen como OTRA nota; la banda "fusional-expresiva" es ~±15-70 cents. Se recomienda límite configurable por armónico. La aritmética (`f' = n·f1·(1+d/2n)`) reproduce los ejemplos de Nicolás exactamente y mosaica el continuo sin huecos.

6. **"Suave = bello" es FALSO como criterio único.** La danza con perfiles de velocidad variados-pero-predecibles se percibe más bella que la uniforme; el virtuosismo incluye explosividad. La consonancia a medir es coordinación + eficiencia + predecibilidad, no suavidad cruda. El discriminador clave es la potencia mecánica firmada P=⟨a,v⟩: negativa = frenado por resistencia (detunea grave), positiva fuera de fase = bombeo disonante (detunea agudo) — la semántica exacta que propuso Nicolás, con fórmula.

7. **El 70% del camino ya está en código.** HarMoCAP da keypoints suavizados + tempo/beat_phase + grabación jsonl; el weaver tiene la arquitectura geometría/activación + transforms de snap (gate/hysteresis, pad_dwell, slew_limiter); el motor del shaper YA modula frecuencia por bloque con fase continua. El hueco crítico es uno: no existe la capability de detuneo por voz en el contrato OSC del shaper (las voces están fijadas a f1·N). Es un trabajo acotado: wire + handler + store + bump de contrato.

8. **El experimento baseline se puede correr esta semana.** Protocolo completo verificado contra los parsers reales: 12-18 clips en 3 categorías (consonante-experto / neutro / disonante-deliberado, mismo performer donde sea posible), captura con `run_realtime.py --source video --record`, script de métricas offline (~200 líneas nuevas), ratings ciegos 1-7 con ≥3 evaluadores, Spearman ρ. Los pesos de la fórmula de consonancia C_j NO se fijan a priori: los calibra el experimento. Eso es literalmente "medirle la matemática al placer visual".

## Estado del landscape

| Dimensión | Estado | Fuente |
|---|---|---|
| Teoría (HIT) | definición lista, traducción operacional propuesta | [R5] |
| Teoría (Laban) | anclaje legítimo = Choreutics/Space Harmony, NO Effort; proxies actuales son práctica estándar honesta | [R1] |
| Precedentes de sistemas | hueco confirmado; OtoKin/EyesWeb validan piezas | [R2] |
| Matemática de métricas | 5 candidatas con fórmulas + patologías cuantificadas (ruido ×30 por derivada a 30fps) | [R3] |
| Psicoacústica del detuneo | regla verificada; curva de Sethares predice el efecto; riesgo de segregación acotado | [R4] |
| Motor de audio | shaper puede (fase continua por bloque); falta capability de contrato | [R5] |
| Weaver | transforms de snap ya existen; geometría nueva `consonance_body` a escribir; gate arp_* del replay a relajar | [R5] |
| Baseline experimental | protocolo ejecutable hoy; comandos verificados | [R5] |

## Checklist mínima (orden sugerido)

1. Nicolás aprueba las 6 decisiones del CROSS_REPORT §H (mapeo anatómico, límite por armónico, snap inicial, forma de d_j, corpus+consentimiento, destino shaper).
2. Capability de detuneo en harmonic-shaper (wire + store + contrato + slew + safety).
3. Script `compute_metrics.py` offline (las 5 métricas + P_j firmada, ventanas HarMoCAP).
4. Corpus de video (12-18 clips, 3 categorías) + ratings ciegos.
5. Correlación Spearman → pesos calibrados de C_j → diseño del expander `consonance_body` + escena.
6. Prueba en vivo con performer real; iterar snap/límites contra percepción.

## Pendiente de verificar

- Todo lo marcado ❓ en CROSS_REPORT (fórmulas de composición, pesos, umbrales θ/h, deadband).
- La latencia OSC→audio estimada (45-55 ms) en el sistema real.
- Si PLV contra 2×beat (octava) es necesario para movimientos a subdivisión.
- El comportamiento del gate `arp_*` con una escena consonance real (no sólo leído en código).
