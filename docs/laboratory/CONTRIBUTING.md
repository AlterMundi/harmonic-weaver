# Aportes al laboratorio

Estado 2026-10-05: instrumento y bancos integrados en `main`. Una instalación
cotidiana: `~/Projects/harmonic-weaver` con el comando de RUNNING. #29/#30 y las
ramas/workspaces históricos no son una base alternativa de uso. Partir del head
actual; preservar cambios locales antes de actualizar. Integrar trabajo terminado
continuamente, sin acumular PRs pendientes de otra aprobación rutinaria. Las PRs
sirven para colaboración cuando hace falta; no crear instalaciones separadas salvo
indicación de Nicolás. Registrar la base en una contribución permite ubicar el
cambio, no exige igualdad de hashes entre entornos ni nuevas rondas de revisión.

Leer SPEC, DECISIONS e IMPLEMENTATION_STATUS antes de tomar una tarea. Registrar
en la issue correspondiente qué módulo se modifica y qué depende de otra PR.
Los contratos centrales viven en `src/harmonic_weaver/lab/contracts.py`; sus
schemas y fixtures se regeneran con `scripts/export-laboratory-contracts.py`.
Los bancos tienen además requests/manifests tipados en `lab/research/` y evaluación
en `lab/evaluation/`; revisar el consumidor vigente antes de modificar una frontera.

El bridge de Oliva está incorporado conservando autoría (#36/#97 en #98 y #107 en
#109). Mientras continúa su línea geométrica, están reservados
`research/laboratory/sai_bridge/` y `tests/research/test_sai_bridge_*.py`.
Extender consumidores fuera de esos directorios; no bloquear trabajo independiente
esperando otro aporte ni asignar personas/agentes automáticamente.

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
- Síntesis/telemetría: repositorio harmonic-shaper, `main`, incluyendo la
  [PR #7](https://github.com/AlterMundi/harmonic-shaper/pull/7) y controles de salida.
  #2 es la frontera inicial histórica. Publicar cambios del motor allí y enlazar
  su PR desde Weaver. No simular fases en la interfaz.
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

Elegir pruebas por el cambio y el riesgo concreto; reutilizar evidencia válida,
sin exigir repetir la suite completa para cada edición. Para contratos/modelos/
runtime desde el checkout:

```sh
PYTHONPATH=src:tests .venv/bin/python -m pytest -q tests/test_lab_*.py
```

Cuando un cambio requiere verificar toda la integración, con Shaper-dev como
directorio hermano:

```sh
SHAPER_DIR=../harmonic-shaper-dev PYTHONPATH=src:tests:../harmonic-shaper-dev/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest -q tests --maxfail=5
```

Las pruebas PCM requieren el renderer declarado; no sustituirlo por main para
obtener un resultado compatible. Los bancos web nuevos se prueban con una fixture
aislada/API real o con `--no-audio`, sin abrir dispositivos ni datos corporales.
El comando de desarrollo y su alias están documentados en RUNNING; `--describe`
muestra selección, `--check` verifica imports, ninguno acredita hardware/escucha.

El instrumento local está disponible. Consultar VALIDATION e
IMPLEMENTATION_STATUS para distinguir pruebas de software, señal de salida y
aceptación humana pendiente; los medios corporales permanecen fuera del repo.
