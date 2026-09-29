Permitir cambiar parámetros, modalidades y ruteos mientras la fuente continúa, sin reiniciar Shaper ni hacer un render previo. Un grafo inválido no puede interrumpir la configuración que ya suena.

## Implementación

- Usar los principios de Weaver: rutas declarativas, validación/compilación previa y generación atómica. Estudiar engine/core.py y compiler.py; no crear un segundo patchbay incompatible.
- Registro de plugins con controles/unidades/defaults. Fuentes corporales → transformaciones → mezcla explícita → destinos de voz. Un escritor final por destino; grafo DAG. Resonadores con feedback interno encapsulado, no ciclos arbitrarios.
- Seis voces en el preset inicial; permitir hasta 32 dentro de capacidades de Shaper. Varias señales pueden controlar una voz y una señal muchas voces.
- Parámetros continuos aplicados en tick/bloque siguiente; rampas configurables sin suavizado oculto. Cambios estructurales preparan candidato fuera del audio; migrar estado compatible y precalentar/resetear el resto.
- Compensación/normalización, curvas, deadband, clamp, signo, bypass, mute/solo y macros con rangos explícitos. Mantener pesos originales al aislar una voz.
- Congelar/modificar/fallar un worker no bloquea controles/audio. Validez y latencia por plugin visibles; métodos retrospectivos no se ofrecen como live.
- Seleccionar salida local de Shaper; no introducir sintetizador web alternativo. Reservar un namespace de voces del laboratorio y liberar solamente las propias al cerrar.

## Pruebas / salida

Atomicidad, revisión en conflicto, parámetros inválidos, ciclos/unidades/rutas ambiguas, transiciones sin voces colgadas, desconexión y pérdida de datos. Ejecutar carga y cambios repetidos mientras corre fuente; verificar ausencia de backlog creciente.

Entregar señales/destinos enumerables para UI y fixtures para pruebas headless. La musicalidad y latencia física requieren LAB-08, no se afirman desde mocks.

## Coordinación y referencias

Programa: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Milestone: [Laboratorio corporal — exploración en tiempo real v1](https://github.com/AlterMundi/harmonic-weaver/milestone/1).

Dependencias: [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9).

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

<!-- weaver-lab:LAB-03 -->
