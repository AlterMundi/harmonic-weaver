# Laboratorio corporal: punto de entrada

Estado: primera iteración local disponible; ver [arranque](RUNNING.md),
[validación y límites](VALIDATION.md) y [estado](IMPLEMENTATION_STATUS.md). 2026-09-29.

Para aportar cambios o presets: [fronteras y flujo de contribución](CONTRIBUTING.md).

Coordinación y seguimiento: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Este índice reúne el alcance vigente, las tareas ejecutables y las preguntas que siguen abiertas.

Próxima iteración y colaboración: [integración de Sai y goals complementarios](NEXT_ITERATION.md).

## Qué leer primero

1. [Decisiones vigentes](DECISIONS.md): prioridades acordadas y distinciones que no deben perderse.
2. [Especificación](SPEC.md): experiencia, arquitectura, contratos, algoritmo inicial y aceptación.
3. [Agenda R01–R13](../../research/laboratory/AGENDA.md): hipótesis, experimentos posteriores y fuentes originales de Anni.
4. [Inventario local](BASELINE_INVENTORY.json): procedencia del instrumento previo; hashes no sustituyen su publicación.

El [borrador exploratorio](../LABORATORIO_ROPE_FLOW_PLAN.md) conserva contexto y referencias, pero sus decisiones incompatibles quedaron reemplazadas por la especificación y el registro de decisiones. No usar su antiguo orden de hitos como backlog vigente.

## Dos etapas

Explorar primero: archivo en loop o cámara, controles/ruteos web en caliente, presets portables, seis voces iniciales y figura polifónica. Tracking de archivo persistente y reutilizable. No se exige grabar ni producir un informe para jugar.

Evaluar después: presets seleccionados contra las mismas fuentes, cálculo y síntesis compartidos con live, manifest y comparaciones reproducibles. Los protocolos precisos se desarrollan con el feedback de las primeras sesiones.

- [Laboratorio corporal — exploración en tiempo real v1](https://github.com/AlterMundi/harmonic-weaver/milestone/1).
- [Laboratorio corporal — comparación reproducible de presets](https://github.com/AlterMundi/harmonic-weaver/milestone/2).

## Construcción y dependencias

| Tarea | Entrega | Depende de |
|---|---|---|
| [LAB-00 · #8](https://github.com/AlterMundi/harmonic-weaver/issues/8) | Preservar y reconciliar el instrumento local antes de implementar | — |
| [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9) | Contratos de sesión, presets portables y bitácora ligera | [LAB-00 · #8](https://github.com/AlterMundi/harmonic-weaver/issues/8) |
| [LAB-02 · #10](https://github.com/AlterMundi/harmonic-weaver/issues/10) | Video/cámara y cache persistente de tracking para loops | [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9) |
| [LAB-03 · #11](https://github.com/AlterMundi/harmonic-weaver/issues/11) | Runtime causal y matriz de ruteos modificable en caliente | [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9) |
| [LAB-04 · #12](https://github.com/AlterMundi/harmonic-weaver/issues/12) | Telemetría efectiva de Shaper y Lissajous polifónico nuevo | [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9) |
| [LAB-05 · #13](https://github.com/AlterMundi/harmonic-weaver/issues/13) | Mesa web de exploración, controles completos y presets | [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9) |
| [LAB-06 · #14](https://github.com/AlterMundi/harmonic-weaver/issues/14) | Baselines, interferencia relacional v0 y geometría angular | [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9) |
| [LAB-07 · #15](https://github.com/AlterMundi/harmonic-weaver/issues/15) | Organización colectiva, centros de despliegue e interferencia | [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9), [LAB-06 · #14](https://github.com/AlterMundi/harmonic-weaver/issues/14) |
| [LAB-08 · #16](https://github.com/AlterMundi/harmonic-weaver/issues/16) | Integración del laboratorio, latencia y primeras sesiones | [LAB-02 · #10](https://github.com/AlterMundi/harmonic-weaver/issues/10), [LAB-03 · #11](https://github.com/AlterMundi/harmonic-weaver/issues/11), [LAB-04 · #12](https://github.com/AlterMundi/harmonic-weaver/issues/12), [LAB-05 · #13](https://github.com/AlterMundi/harmonic-weaver/issues/13), [LAB-06 · #14](https://github.com/AlterMundi/harmonic-weaver/issues/14), [LAB-07 · #15](https://github.com/AlterMundi/harmonic-weaver/issues/15) |
| [LAB-09 · #17](https://github.com/AlterMundi/harmonic-weaver/issues/17) | Captura opcional de fragmentos video + audio y configuración | [LAB-02 · #10](https://github.com/AlterMundi/harmonic-weaver/issues/10), [LAB-03 · #11](https://github.com/AlterMundi/harmonic-weaver/issues/11), [LAB-04 · #12](https://github.com/AlterMundi/harmonic-weaver/issues/12), [LAB-05 · #13](https://github.com/AlterMundi/harmonic-weaver/issues/13) |
| [EVAL · #18](https://github.com/AlterMundi/harmonic-weaver/issues/18) | Corridas reproducibles de presets × fuentes y resultados publicables | [LAB-08 · #16](https://github.com/AlterMundi/harmonic-weaver/issues/16) |

[LAB-00 · #8](https://github.com/AlterMundi/harmonic-weaver/issues/8) preserva/reconcilia el baseline antes de integrar. Con los contratos y fixtures de [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9), fuentes, runtime, telemetría/figura, UI y algoritmos admiten trabajo paralelo. LAB-07 añade organización colectiva y centros variables; la investigación puede empezar antes, pero la integración respeta las dependencias.

[LAB-09 · #17](https://github.com/AlterMundi/harmonic-weaver/issues/17) es captura opcional y no bloquea las primeras sesiones de [LAB-08 · #16](https://github.com/AlterMundi/harmonic-weaver/issues/16). La validación comparativa comienza después del feedback, no condiciona la operación cotidiana.

No hay colaboradores asignados automáticamente. Cada tarea declara fronteras y aceptación; los cambios necesarios en HarMoCAP/Shaper se publican en sus repos y se enlazan desde la tarea de Weaver. La implementación y su evidencia se siguen en IMPLEMENTATION_STATUS y VALIDATION.

## Investigación conservada

| Agenda | Seguimiento |
|---|---|
| R01, R06 | [RES-THEORY · #19](https://github.com/AlterMundi/harmonic-weaver/issues/19) — HIT, Grassmannianos y activación: restricciones, ondas y predicciones distinguibles |
| R02, R03 | [RES-ORGANIZATION · #20](https://github.com/AlterMundi/harmonic-weaver/issues/20) — Organización colectiva y Jpsh!: de candidatos cinemáticos a evidencia |
| R05 | [RES-SONIFICATION · #21](https://github.com/AlterMundi/harmonic-weaver/issues/21) — Sonificar relaciones: mapeos, resonadores y respuesta al Jpsh! |
| R07 | [RES-CYMATICS · #22](https://github.com/AlterMundi/harmonic-weaver/issues/22) — Cuerpo → sonido → geometría: información preservada y medios cimáticos |
| R08, R09 | [RES-CAPTURE · #23](https://github.com/AlterMundi/harmonic-weaver/issues/23) — Cuerda, 3D y captura adicional para estudiar el despliegue |
| R10 | [RES-PERCEPTION · #24](https://github.com/AlterMundi/harmonic-weaver/issues/24) — Placer, belleza y legibilidad para practicantes y observadores |
| R11 | [RES-NEURO · #25](https://github.com/AlterMundi/harmonic-weaver/issues/25) — OpenBCI, sincronización y SNR en experiencia audiovisual |
| R12 | [RES-ENERGY · #26](https://github.com/AlterMundi/harmonic-weaver/issues/26) — Movimiento, trabajo y costo energético: ¿se relacionan belleza y eficiencia? |
| R13 | [RES-TRANSFER · #27](https://github.com/AlterMundi/harmonic-weaver/issues/27) — Transferencia, entrenamiento y persona–prótesis: horizonte de la propuesta |
| R04 | [#6 · Interferencia entre estados corporales](https://github.com/AlterMundi/harmonic-weaver/issues/6), existente; LAB-06/07 agregan operacionalizaciones sin cerrar la hipótesis. |

Estas preguntas tienen seguimiento propio sin prometer implementarlas todas en el primer milestone. Un resultado nulo, límites de medición o desacuerdo entre métodos se documentan; la entrega del instrumento no depende de demostrar HIT.

## Continuar desde otra sesión

- Empezar por la issue y sus dependencias; las referencias de código del inventario pueden no existir aún en main.
- Preservar cambios del workspace y revisar las instrucciones del repo afectado. No subir videos, pesos ni todos los artefactos untracked.
- Registrar decisiones nuevas con fecha y enlazarlas a la agenda; no reescribir las propuestas originales.
- Publicar cambios de contratos con fixtures compartidos antes de integrar consumidores en paralelo.

[github-plan.json](github-plan.json) conserva las claves y dependencias; [GITHUB.json](GITHUB.json) registra los números/URLs publicados. Los cuerpos en [issues/](issues/) son el snapshot de publicación; el estado operativo posterior se sigue en GitHub.

Segunda iteración: [comparador reproducible](EVALUATION.md), [arranque y recorrido](RUNNING.md).
