# R01: primer banco sintético de subespacios y predicción

Alcance: verificar observables y controles antes de interpretar geometría corporal.
No es evidencia HIT, física de partículas, intención o eficiencia corporal. El
estimador `CausalSubspace` es el mismo usado por el modelo colectivo del instrumento.
Seis voces y parámetros de síntesis no se modifican por este banco.

La pregunta operacional es si una representación con residuo espacial bajo también
permite predecir el siguiente vector. Se separan: residuo de reconstrucción sobre
un subespacio ajustado sólo al pasado; predicción a un paso con persistencia,
ridge completo y ridge en el subespacio; y ángulos principales entre ventanas.
Los tres predictores comparten instantes válidos dentro de cada control. Entre
controles puede variar el soporte: inspeccionar tiempos en JSONL, no comparar
agregados como si fueran muestras emparejadas automáticamente.

Generadores configurables: mezclas de sinusoides en subespacio fijo, subespacio
rotante y proceso gaussiano AR(1) en subespacio fijo (memoria 0: muestras
independientes). Rangos/ruido/regularización/ventana/semilla son explícitos. Los
controles son trayectoria original, rotación ortogonal global con las mismas
muestras y permutación temporal que conserva los vectores. No son vídeos humanos.

## Operación

Web, pestaña Investigación: editar controles, exportar/importar configuración JSON
y correr banco R01. Se ejecuta en proceso separado, con BLAS/OMP a un thread; no
aplica preset al instrumento. API GET/POST `/api/research/r01`. Archivos locales
`<data-dir>/research/r01/<id>/`: request.json congelado, manifest con identidad de
código/paquetes/configuración/hashes/score y JSONL por control; worker.log. Resultados
completos no se sobrescriben. No hay descarga/API detallada de traces todavía.

CLI desde el checkout elegido, con el mismo Python/extras del laboratorio:

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python -m harmonic_weaver.lab.research.grassmann \
  --request /ruta/configuracion.json --output /ruta/nueva/corrida
```

## Evidencia real del banco (2026-09-30)

[evidence-2026-09-30.json](evidence-2026-09-30.json) contiene configuración, hashes y
scores de una ejecución sintética real, repetida con hashes/metrics idénticos en
esta máquina. Caso estocástico, memoria 0, sin ruido añadido, seis dimensiones y
rango tres: residuo de reconstrucción ≈6e-16; MSE ridge ≈0.581, persistencia ≈1.076;
174 instantes comunes. Rotación global conserva esos scores dentro de precisión
numérica. Este ejemplo muestra que reconstruir un subespacio no equivale a
predicción temporal perfecta. No atribuye leyes a cuerpos ni valida HIT.

Pruebas: invariancia bajo rotación, prefijo causal frente a cambios futuros,
repetibilidad, separación reconstrucción/predicción, worker real/reapertura e
inmutabilidad de resultado. Chrome aislado verifica controles, JSON congelado y
presentación separada de métricas. No escucha ni evaluación corporal/humana.

## Siguientes experimentos y dependencias

1. Integrar entradas de features de corridas #18 con escala, articulaciones,
   calibración y soporte temporal comunes. No importar calibración entre personas.
2. Añadir controles pareados sobre exactamente los mismos tiempos y baselines
   temporales más ricos; análisis de sensibilidad/robustez y comparación reservada.
3. Formular una predicción específica de HIT que difiera de compresión, oscilación
   o autocorrelación genéricas antes de evaluar vídeo. Este banco no la proporciona.
4. Grassmanniano positivo/amplituedro y solitones requieren representación y
   observable propios; no se identifican con una PCA cualquiera. Mantener R01/R06.
5. R02–R13 conservan su agenda; este incremento no los sustituye ni resuelve R01.
