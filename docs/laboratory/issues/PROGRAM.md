El programa une exploración corporal intuitiva con evaluación posterior reproducible. El primer milestone entrega un instrumento que se puede tocar: cámara o video continuo, parámetros/ruteos en caliente, presets portables y Lissajous con todos los armónicos activos. El segundo permitirá comparar conjuntos de presets sobre las mismas fuentes y producir evidencia publicable.

## Decisiones que no deben perderse

- Seis voces iniciales; las tres componentes iniciales de PCA son dimensiones de análisis, no un límite de armónicos.
- Tracking de video una sola vez, cache persistente validada y reprocesamiento forzado. Cámara no se graba por defecto.
- Modelos colectivos y centros de despliegue variables/múltiples forman parte de v1; core fijo es una alternativa, no un supuesto obligatorio.
- Variación transversal no equivale automáticamente a interferencia destructiva. La traducción a afinación/fase/timbre es editable.
- Preservar suma polifónica y rediseñar su aspecto. No reducirla a dos armónicos ni fingir que un Lissajous es una placa cimática.
- Bitácora ligera; guardar presets no obliga a exportar una performance.

## Secuencia y colaboración

1. [LAB-00 · #8](https://github.com/AlterMundi/harmonic-weaver/issues/8) preserva el baseline local que todavía no está en main.
2. [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9) fija contratos, presets y fixtures compartidos.
3. [LAB-02 · #10](https://github.com/AlterMundi/harmonic-weaver/issues/10), [LAB-03 · #11](https://github.com/AlterMundi/harmonic-weaver/issues/11), [LAB-04 · #12](https://github.com/AlterMundi/harmonic-weaver/issues/12) y [LAB-06 · #14](https://github.com/AlterMundi/harmonic-weaver/issues/14) admiten trabajo paralelo; [LAB-05 · #13](https://github.com/AlterMundi/harmonic-weaver/issues/13) puede arrancar con los fixtures.
4. [LAB-07 · #15](https://github.com/AlterMundi/harmonic-weaver/issues/15) agrega organización colectiva/despliegue; [LAB-08 · #16](https://github.com/AlterMundi/harmonic-weaver/issues/16) integra y verifica con sesiones humanas.
5. [LAB-09 · #17](https://github.com/AlterMundi/harmonic-weaver/issues/17) agrega captura opcional sin bloquear las primeras escuchas.
6. [EVAL · #18](https://github.com/AlterMundi/harmonic-weaver/issues/18) coordina el segundo milestone después del feedback inicial.

No asignar colaboradores ni iniciar agentes automáticamente. Una tarea debe declarar archivos/interfaces propios y los cambios esperados en repos adyacentes. Contratos se modifican coordinadamente, no por ramas que inventan formatos incompatibles.

## Investigación abierta

[RES-THEORY · #19](https://github.com/AlterMundi/harmonic-weaver/issues/19), [RES-ORGANIZATION · #20](https://github.com/AlterMundi/harmonic-weaver/issues/20), issue #6, [RES-SONIFICATION · #21](https://github.com/AlterMundi/harmonic-weaver/issues/21), [RES-CYMATICS · #22](https://github.com/AlterMundi/harmonic-weaver/issues/22), [RES-CAPTURE · #23](https://github.com/AlterMundi/harmonic-weaver/issues/23), [RES-PERCEPTION · #24](https://github.com/AlterMundi/harmonic-weaver/issues/24), [RES-NEURO · #25](https://github.com/AlterMundi/harmonic-weaver/issues/25), [RES-ENERGY · #26](https://github.com/AlterMundi/harmonic-weaver/issues/26), [RES-TRANSFER · #27](https://github.com/AlterMundi/harmonic-weaver/issues/27).

La agenda R01–R13 es la memoria del programa. Cada resultado añade una nota fechada con condiciones, evidencia, límites y siguiente pregunta. Cerrar implementación no demuestra una hipótesis; un resultado nulo también completa un experimento.

La polifonía de Bands sigue en #4. No duplicarla ni bloquear este instrumento por su gate de dos personas. La interferencia sigue conectada a #6.

## Coordinación y referencias

Los milestones y sus entregables se coordinan desde esta issue.

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

## Seguimiento de entregas

- [ ] [LAB-00 · #8](https://github.com/AlterMundi/harmonic-weaver/issues/8) — Preservar y reconciliar el instrumento local antes de implementar
- [ ] [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9) — Contratos de sesión, presets portables y bitácora ligera
- [ ] [LAB-02 · #10](https://github.com/AlterMundi/harmonic-weaver/issues/10) — Video/cámara y cache persistente de tracking para loops
- [ ] [LAB-03 · #11](https://github.com/AlterMundi/harmonic-weaver/issues/11) — Runtime causal y matriz de ruteos modificable en caliente
- [ ] [LAB-04 · #12](https://github.com/AlterMundi/harmonic-weaver/issues/12) — Telemetría efectiva de Shaper y Lissajous polifónico nuevo
- [ ] [LAB-05 · #13](https://github.com/AlterMundi/harmonic-weaver/issues/13) — Mesa web de exploración, controles completos y presets
- [ ] [LAB-06 · #14](https://github.com/AlterMundi/harmonic-weaver/issues/14) — Baselines, interferencia relacional v0 y geometría angular
- [ ] [LAB-07 · #15](https://github.com/AlterMundi/harmonic-weaver/issues/15) — Organización colectiva, centros de despliegue e interferencia
- [ ] [LAB-08 · #16](https://github.com/AlterMundi/harmonic-weaver/issues/16) — Integración del laboratorio, latencia y primeras sesiones
- [ ] [LAB-09 · #17](https://github.com/AlterMundi/harmonic-weaver/issues/17) — Captura opcional de fragmentos video + audio y configuración
- [ ] [EVAL · #18](https://github.com/AlterMundi/harmonic-weaver/issues/18) — Corridas reproducibles de presets × fuentes y resultados publicables

<!-- weaver-lab:PROGRAM -->
