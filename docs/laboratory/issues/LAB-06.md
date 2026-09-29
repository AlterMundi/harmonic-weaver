Implementar comparadores causales seleccionables sobre las mismas observaciones: baseline actual, relación local de Anni y evolución de ángulos entre segmentos. Emitir señales independientes de la traducción musical.

## Método

- Congelar comportamiento actual recuperado por LAB-00, incluidos normalización/adaptación y defaults; no corregirlo silenciosamente al compararlo. Agregar posición y velocidad constante como referencias simples.
- Implementar la nota de Anni: vectores padre→hijo normalizados, velocidad relativa, historia estrictamente previa, Δu, Δu/Δt, I/R/A y ángulo firmado. Referencia instantánea e histórica son opciones distintas.
- Cerca del ruido marcar «sin modo»/«sin contribución»; no llamarlo neutral. I y R no son dimensiones independientes en 2D. Estimación de ruido por quietud/calibración elegida, fuera de evaluación.
- Ángulos de segmentos/joints, unwrap y predictor angular. Separar orientación/traslación global de organización interna. Missingness reinicia historia relevante; no derivar dos veces raw frames sin estimador causal configurable.
- Descriptor con ventanas, tau, ruido, referencia, regiones y unidades. Escala corporal calibrada separada del preset; salida no se llama fuerza/potencia física.

## Secuencias de aceptación

Los cuatro ejemplos de Anni, más rotación uniforme, cambio de FPS, ruido, huecos, cambio de persona y transformación global. Realizar trayectorias completas con timestamps; las velocidades instantáneas de la nota no bastan para probar filtros históricos.

Demostrar casos donde los métodos discrepan y reportar el significado exacto de cada señal. Pruebas sintéticas verifican implementación, no eficacia/percepción. Ruteos y UI vienen de LAB-03/05. Enlazar #6 y mantener su investigación abierta.

## Coordinación y referencias

Programa: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Milestone: [Laboratorio corporal — exploración en tiempo real v1](https://github.com/AlterMundi/harmonic-weaver/milestone/1).

Dependencias: [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9).

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

<!-- weaver-lab:LAB-06 -->
