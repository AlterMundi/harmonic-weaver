Un video se trackea una vez, se guarda asociado al original y se reutiliza en todos los loops y reaperturas hasta cambiar contenido/modelo/configuración o forzar reprocesamiento. La cámara sigue siendo una fuente causal sin grabación automática.

## Implementación

- Reutilizar HarMoCAP PoseBackend e identidad. Auditar webapp processing: cachear observaciones anteriores a filtros ajustables, con estados y timestamps. No usar el capturador live de último frame para extracción secuencial offline.
- Abrir path local o importar desde navegador. Sidecar `<video>.weaver-cache/` si es escribible; biblioteca configurable como fallback visible y destino de uploads.
- Clave de validez por content hash, extractor, modelo/pesos, configuración de percepción/identidad. Cambiar nombre/path, sonido, ruteos, visualización o filtros posteriores no invalida tracking.
- Manifest de dimensiones, tiempo/PTS, marco, unidad, observación y checksums. Si se usa index/FPS por falta de PTS, declararlo. No hardcodear 16:9.
- Generaciones temporales y publicación atómica. Reprocesar/cancelar/error conserva cache válida anterior. Índice local por hash permite reconocer copias/renames.
- Primera extracción muestra progreso y habilita prefijo procesado. Loop completo espera cache completa; no repetir inferencia por vuelta ni sonificar datos inexistentes.
- Transporte play/pause/seek/loop con reinicio de derivadas al saltar. Elegir persona y cámara desde UI. Cambiar identidad/stream no produce velocidad ficticia.
- Worker independiente y colas live acotadas. Mostrar FPS, drops y edad de muestra; no acumular atraso.

## Pruebas

Video CFR y VFR sintéticos, primera extracción, cache hit sin llamadas al backend, renombre, pesos/config alterados, fuerza, corrupción, cancelación, directorio no escribible, loop y seek. Fixtures de identidad/missingness y cambio de persona. Decodificación completa conserva todos los frames solicitados; live puede descartar solo con diagnóstico explícito.

Entregar adaptador fuente y operaciones de transporte a LAB-05. No almacenar parámetros sonoros dentro de cache ni datos de cámara por defecto.

## Coordinación y referencias

Programa: [PROGRAM · #7](https://github.com/AlterMundi/harmonic-weaver/issues/7). Milestone: [Laboratorio corporal — exploración en tiempo real v1](https://github.com/AlterMundi/harmonic-weaver/milestone/1).

Dependencias: [LAB-01 · #9](https://github.com/AlterMundi/harmonic-weaver/issues/9).

[Especificación](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/SPEC.md) · [Decisiones vigentes](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/DECISIONS.md) · [Agenda R01–R13](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/research/laboratory/AGENDA.md) · [Inventario del baseline](https://github.com/AlterMundi/harmonic-weaver/blob/506afe3e6f43b63252f9b289365d7b33650896b5/docs/laboratory/BASELINE_INVENTORY.json).

<!-- weaver-lab:LAB-02 -->
