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

## Comparación sobre tiempos compartidos

Incremento posterior a #48: `paired` usa la intersección de tiempos con los tres
predictores válidos en todos los controles. Conserva conteos elegibles/excluidos,
scores pareados y diferencias MSE por instante frente a original. `paired.jsonl`
conserva los mismos tiempos y resultados de cada control, con hash en manifest.
Sin intersección no hay score (no se presenta cero como éxito). Se mantienen los
agregados individuales originales. La UI muestra pareados por defecto; checkbox
permite ver agregados individuales, sin recalcular ni tocar el instrumento.

Emparejar posiciones del reloj no significa emparejar el mismo vector: el control
de shuffle modifica la observación de ese instante. No es una estimación causal
sobre cuerpos, ni p-value ni intervalo de confianza. La inferencia estadística y
entradas corporales con soporte adecuado permanecen pendientes.

[evidence-paired-2026-09-30.json](evidence-paired-2026-09-30.json) conserva ejecución
real/repetida: subespacio rotante, 240 muestras, dos componentes estimados en seis
dimensiones. 234 tiempos compartidos en los tres controles. Diferencias por
rotación global próximas a cero numérico; en esta configuración subspace ridge
es peor que ridge completo en el original. No se presupone superioridad de la
reducción dimensional. Los resultados son de este generador/configuración y no
validan HIT. Se preserva la evidencia anterior de #48 con su identidad de código.

Pruebas añadidas: soportes artificialmente distintos excluidos antes de puntuar;
intersección vacía devuelve ausencia de score. Chrome verifica conmutación de
vista pareada/individual, y traces/metrics se repiten exactamente en esta máquina.

## Descarga desde la web

La lista de corridas ofrece manifest, configuración y traces declaradas con hash.
API `/api/research/r01/{id}/artifacts/{name}` acepta únicamente request.json,
manifest.json y las cuatro traces conocidas. Configuración/traces requieren status
complete: configuración canonizada coincide con settings del manifest y traces se
verifican por SHA-256. Manifest puede descargarse para diagnóstico de un fallo.
Rechaza symlinks/nombres fuera del contrato; no recibe una ruta arbitraria. Hash
memoizado por fingerprint de archivo se invalida si cambia. HTTP Range/206 permite
leer fragmentos sin cargar toda la trace en memoria. No sube ni publica resultados.

Pruebas adicionales: worker real/reinicio, alteración de request/trace, selección
cerrada de nombres, HTTP Range/206 y enlaces Chrome. 17 research/API/collective tests
más Chrome aislado y build. Sólo fixtures/datos sintéticos; instrumento intacto.

### Cancelación desde la web

Una corrida activa muestra **Cancelar corrida R01**. Se termina y espera sólo
su proceso hijo, sin intervenir en el tracking ni el audio. El manifest queda
`cancelled` y los archivos parciales se conservan para diagnóstico; no se
ofrecen como trazas completas. Si el worker confirmó `complete` antes de
terminar, ese resultado se preserva. Cancelar de nuevo es idempotente.
Cerrar el servicio interrumpe sus workers con estado `interrupted`; no se
atribuye esa interrupción a una acción humana. Tras reiniciar, un worker sin
proceso propio tampoco se presenta como completado ni se intenta matar otro
proceso. No hay reanudación automática de un cálculo parcial.

### Horizonte y origen de predicción

El control web **Horizonte de predicción (pasos)** admite 1–30; a 30 Hz,
12 pasos equivalen a 0.4 s. Default 1 conserva el predictor anterior y no cambia
el instrumento. Ridge ajusta directamente pares separados por ese horizonte,
sin realimentar observaciones intermedias. Base y coeficientes usan únicamente
la ventana que termina en el origen; el vector pronosticado queda congelado
hasta observar su objetivo. La trace registra origen, fin de ajuste, número
de pares y vectores previstos, además del error. Sin suficientes pares o sin
soporte no hay score: no se sustituye por cero.

El residuo geométrico sigue siendo descriptivo del objetivo y usa la ventana
pasada de ese instante. Para horizontes largos esa ventana es posterior al
origen de predicción: no interpretar su residuo como información disponible al
pronosticar. Comparaciones entre horizontes también requieren soporte común.

[Evidencia sintética de horizontes](evidence-horizons-2026-09-30.json): semilla 17,
180 muestras, 1/6/15 pasos, 149 objetivos comunes entre todos los horizontes y
controles. Cada corrida se repitió con hashes de traces idénticos. En el original,
MSE de persistencia: 0.002832/0.088616/0.424002; ridge completo:
0.003613/0.256265/2.268094. Esta configuración empeora a horizontes mayores y
ridge no supera persistencia. No se seleccionó sólo un resultado favorable.
Es una semilla sintética: sin intervalo de confianza, generalización corporal
ni conclusión HIT. La rotación global sirve como control de representación;
shuffle conserva vectores pero cambia la cronología.

Reproducir con el checkout/paquetes de la evidencia, en un directorio nuevo:

```bash
cd ~/Projects/harmonic-weaver-dev
OPENBLAS_NUM_THREADS=1 .venv/bin/python research/laboratory/r01_grassmann/reproduce_horizons.py --output /tmp/r01-horizons-reproduction
```

El script exige identidad del módulo y hashes exactos de entradas/traces;
rechaza diferencias en lugar de declarar una reproducción que no ocurrió.
Los manifests producidos conservan identidad de código y paquetes para
inspeccionar diferencias de entorno. Las configuraciones congeladas también
pueden importarse individualmente en la web desde el campo `settings` de cada
corrida de la evidencia.

### Features corporales desde una comparación congelada

En Investigación, **R01 · Features del comparador** permite elegir comparación
terminada, corrida (preset/fuente), intervalo y 2–16 señales de la misma unidad.
Se muestran persona y unidad de la fuente congelada. Controles independientes:
semilla, componentes, ventana, umbral, ridge, horizonte y gap máximo. Exportar/
importar configuración corporal conserva señales y parámetros, sin transportar
identidad, fuente o calibración. Elegir la fuente sigue siendo explícito.

API POST `/api/research/r01/trace`: `evaluation_id`, `run_index`, `signal_ids`,
`start_s`, `end_s` y esos parámetros. Sólo acepta una corrida completa con trace
verificada y segmento contenido en el intervalo evaluado (máximo 120 s/14400
observaciones). No recibe una ruta arbitraria ni abre video/cámara. Congela un
`input.json` local con señales, valores/causas, timestamps y procedencia: hash de
trace/request/preset, código, fuente, tracking y calibración de la evaluación.
El worker exige el hash del snapshot. Request, input, manifest y traces pueden
descargarse por el contrato de artefactos; siguen siendo datos corporales locales.

El reloj es el timestamp del FeatureFrame, no el control clock. Repeticiones del
mismo frame se excluyen para no premiar mantener el último valor durante ticks
sin nueva observación. Exige lookahead cero y rechaza persona diferente de la
fuente congelada. Faltantes/cambios de soporte o gaps mayores al umbral cortan
segmentos y descartan historia/forecasts pendientes. Sin interpolar, imputar ni
buscar un cuerpo alternativo. Los controles conservan los límites de segmentos;
shuffle sólo permuta dentro de cada segmento válido.

El horizonte cuenta muestras de features; si sus timestamps son irregulares,
**no equivale a una duración constante**. `horizon_elapsed_s` registra la duración
real por objetivo. MSE es promedio por muestra, en unidades originales al cuadrado;
no pondera duración. Rotación ortogonal ocurre en el espacio de señales derivadas,
no implica una rotación física del cuerpo. No mezcla unidades, no aplica escalado
futuro ni infiere que normalización/compresión prueben harmonicidad.

Verificación local del fragmento del dúo: se reutilizaron fuente/tracking y elección
previamente verificada del cuerpo a la derecha. Comparación sin PCM, seis señales
de velocidad, dos componentes y horizonte seis; dos corridas producen hashes de
traces idénticos. Los outputs y el registro `body-research-verification.json` quedan
en el estado privado `laboratory-dev`, fuera del repo/GitHub. No es una nueva
verificación de exactitud de pose, identidad humana, musicalidad o hipótesis HIT.

Pendientes científicos: formular predicciones HIT específicas, controlar el efecto
de señales derivadas/modelos, ampliar familias de predictores, splits reservados,
normalización causal explícita cuando se requiera y evaluación entre cuerpos/tareas.

## Familias adicionales de pronóstico — 2026-10-03

Además de persistencia, ridge completo y ridge de subespacio, se pueden seleccionar
linear_trend, lagged_full_ridge y lagged_subspace_ridge. Los defaults siguen siendo
los tres métodos anteriores. La web ofrece selección y autoregressive_lags (3,
configurable 1–12) tanto en banco sintético como en features EVAL congeladas;
JSON portable conserva ambos. La tabla usa los métodos de cada resultado, no
los controles actuales. Corridas históricas conservan sus columnas anteriores.

Ridge con q retardos ajusta pares (q vectores consecutivos, vector h muestras
después), centra usando sólo esos pares y pronostica desde el último conjunto
de q observaciones. Con q=1 coincide numéricamente con ridge anterior. Tendencia
lineal ajusta cada coordenada contra índice de muestra y extrapola h pasos.
En features irregulares, h cuenta muestras, no segundos: las traces mantienen
horizon_elapsed_s. No hay selección de hiperparámetros usando el resultado.

La elegibilidad exige suficiente pasado para todos los métodos seleccionados;
los scores dentro de cada control comparten targets, y la comparación de controles
intersecta ese soporte. prediction_fit_support registra observaciones/pares por
método, además del origen congelado. Gaps reinician todas las familias.

Ejemplo reproducible sin datos corporales:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python \
  research/laboratory/r01_grassmann/reproduce_families.py \
  --output /tmp/r01-families-reproduction
```

El script corre los tres casos congelados de evidence-families-2026-10-03.json y
compara soporte y resúmenes numéricos (rtol 1e-8, atol 1e-11 para variaciones
pequeñas de aritmética float64/BLAS). Hashes de módulos/entradas son procedencia,
no el criterio de equivalencia entre entornos. El test de repetición local sí
comprueba traces byte-idénticas bajo las mismas entradas/entorno.

Con seed=17, h=6, q=4 y los restantes ajustes del ejemplo: MSE original del caso
periódico es 0.02606 persistencia y 0.02108 lagged ridge completo; el caso sin
memoria da 0.26641 ridge completo y 0.74338 lagged ridge completo. El segundo
expone sobreajuste, pese al subespacio compacto. No se elige un ganador universal.
No son resultados corporales ni validación de HIT, intención o generalización.
Siguen pendientes predicciones específicas, otras familias y reservas independientes.
