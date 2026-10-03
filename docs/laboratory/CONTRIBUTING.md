# Aportes al laboratorio

La integración está en `feat/laboratory-live` ([PR #30](https://github.com/AlterMundi/harmonic-weaver/pull/30)),
apilada sobre el baseline preservado de PR #29. Hasta integrar esas PRs, una rama
que extienda el laboratorio debe partir de esa integración y declarar ese base.
No copiar cambios por encima del workspace original con modificaciones locales.

Leer SPEC, DECISIONS e IMPLEMENTATION_STATUS antes de tomar una tarea. Registrar
en la issue correspondiente qué módulo se modifica y qué depende de otra PR.
Los contratos viven en `src/harmonic_weaver/lab/contracts.py`; schemas y fixtures
se regeneran con `scripts/export-laboratory-contracts.py`.

## Fronteras útiles para colaborar

- Modelos: `analysis_math.py`, `kinematics.py`, `collective.py`, `models.py`.
  Reciben observaciones con tiempo de fuente y emiten señales con unidad y estado.
  Pruebas mínimas: causalidad, ruido/missingness, identidad, gaps y discontinuidades.
  Un modelo nuevo debe declarar controles, versión y señales; incorporarlo al
  contrato y catálogo explícitamente, sin sustituir versiones desconocidas.
- Ruteo: `routing.py`. Mantener un escritor final por destino y mezclas explícitas;
  no enviar audio desde un algoritmo. PCA y número de voces son independientes.
- Fuentes/cache: `perception_worker.py`, `perception.py`, `cache.py`, `media.py`.
  Cambios en percepción deben invalidar el cache; cambios sonoros no deben hacerlo.
- Síntesis/telemetría: repositorio harmonic-shaper, PR #2. Publicar allí los cambios
  del motor y enlazar su PR desde Weaver. No simular fases en la interfaz.
- Interfaz: consumir los contratos HTTP/WS y estado efectivo; no derivar otra
  implementación de los algoritmos corporales en el navegador.
- Exploración sin código: presets completos con versiones y nombres descriptivos.
  No incluir identidad, calibración de otra fuente ni historia de análisis.

## Evidencia de una contribución

Abrir PR con problema concreto, comportamiento observable y comandos/resultados
de pruebas. Distinguir pruebas sintéticas, ejecución con video real y escucha
humana. Para propuestas de Anni/Oliva, conservar fórmulas y límites interpretativos
en la documentación: una asociación predictiva no establece origen causal,
intención ni eficacia corporal. Las hipótesis y evaluación posterior siguen en
`research/laboratory/AGENDA.md` y milestone 2; no se descartan por quedar fuera de v1.

Comando actual para las pruebas de contratos/modelos/runtime desde el checkout:

```sh
python -m pytest -q tests/test_lab_*.py
```

La primera iteración local está disponible. Consultar VALIDATION e
IMPLEMENTATION_STATUS para distinguir pruebas de software, señal de salida y
aceptación humana pendiente; los medios corporales permanecen fuera del repo.
