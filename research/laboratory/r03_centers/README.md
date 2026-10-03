# R03: comparar señales y centros candidatos

Las señales regionales del instrumento y de EVAL pueden sugerir candidatos de
preparación/despliegue. La coincidencia con marcas humanas no establece intención
ni un centro causal. Esta herramienta compara corridas R03 archivadas, sin volver
a extraer candidatos, recalcular pose o modificar sonido.

En Investigación → R03, correr cada señal/centro contra el mismo corte de marcas.
Después, **Comparar señales o centros R03** permite elegir 2–6 corridas completas.
Se exige el mismo corte/contexto, cuerpo/generación, cobertura declarada de marcas,
tolerancia y offset. Umbrales/refractario/señal pueden variar; sus unidades y la
procedencia se conservan. No se normalizan magnitudes entre señales.

La herramienta intersecta el soporte observado de todas las condiciones. Vuelve
a calcular coincidencias uno-a-uno sólo dentro de esos intervalos, usando el mismo
motor temporal. Conserva además las métricas disponibles de cada corrida, con sus
denominadores originales. Los candidatos pueden tener conteos distintos, pero
las marcas elegibles comparten soporte. Sin soporte hay ausencia de puntuación,
no precisión/recall cero. Los intervalos son semiabiertos y no rellenan gaps.

**Guardar comparación R03** descarga JSON local con soporte, candidatos,
exclusiones, matching, unidades, hashes/procedencia y límites. Cambiar la selección
limpia la tabla. API POST `/api/research/r03/compare` con `{"run_ids":["…","…"]}`.
No elige offset óptimo, centro ganador ni aporta significancia estadística.
Archivos y código histórico permanecen identificados; no exige igualdad de entorno.

## Control reproducible

`controls.py` genera exclusivamente marcas, señales e identidades sintéticas.
Una señal cubre 1 s, otra sólo 0.4 s y una tercera la sección final. Permite
comprobar igualdad de denominadores sobre soporte común y ausencia de score
con intervalos disjuntos. Cada condición se repite en un archivo nuevo; no se
sobrescriben resultados. [Evidencia](evidence-2026-10-03.json).

```bash
cd ~/Projects/harmonic-weaver-dev
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  research/laboratory/r03_centers/controls.py --output /tmp/r03-centers-new
```

45 pruebas backend/temporal y dos Chrome sobre bundle/API reales verifican lectura
sin mutación, matching/cobertura, rechazos de contexto/artefactos y download. Las
pruebas web usan archivos sintéticos y no abren audio ni cámara.

## Dependencias humanas

Se necesitan marcas de preparación/activación/despliegue hechas por personas,
intervalos realmente observados y una declaración de incertidumbre/reacción.
Probar centros/señales alternativas sobre la misma toma, y luego reservar otras
tomas/cuerpos. No inventar marcas ni usar candidatos como su propio ground truth;
elegir umbrales después de ver resultados es exploratorio. El banco no resuelve
Jpsh, HIT, anticipación causal ni eficacia corporal.
