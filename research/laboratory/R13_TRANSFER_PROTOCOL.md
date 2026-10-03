# R13 · Transferencia reservada: predicción antes de intervención

2026-10-02. Issue #27, propuesta Anni P3/P4/P5/P6. Banco de software implementado;
no transferencia demostrada entre personas/tareas, aprendizaje humano, beneficio
clínico/deportivo ni dispositivo diseñado. El instrumento sigue libre de protocolo.

## Preguntas separadas y controles

- Predicción: ¿un modelo congelado conserva precisión en observaciones reservadas?
- Transferencia: ¿qué relaciones sobreviven al cambiar toma, sujeto o tarea bajo
  equivalencias funcionales y restricciones explícitas?
- Adaptación: ¿cuánto cambia con un prefijo observado, sin puntuar ese prefijo?
- Intervención: ¿una sugerencia o feedback mejora un resultado elegido por una
  persona en intentos nuevos, frente a controles y con retención/transferencia?
- Persona–prótesis: ¿qué cambia en el sistema acoplado cuerpo/dispositivo, bajo
  objetivos y restricciones acordados con usuario/especialistas?

El banco implementa predicción reservada y dos adaptaciones limitadas. Las otras
preguntas necesitan datos/diseños independientes. No identifica una trayectoria
ideal ni usa categorías olímpico/para/recreativo como escala de valor corporal.
Tres personas podrían servir para factibilidad, no para universalidad.

## Reproducibilidad y reservas implementadas

JSON nativo R13 conserva tarea/grupos/fuente/proveedor, feature IDs ordenados,
unidad común, observaciones con tiempo original y causas, división train/test,
settings, equivalencia funcional y restricciones. Hay 1..16 features, 2..12
secuencias, hasta20000 observaciones/16MiB. Las secuencias son independientes: no
se crean pares de entrenamiento ni histories atravesando sus fronteras.

| Reserva | Gate software | Lo que todavía necesita evidencia humana |
| --- | --- | --- |
| within_take | Train precede test del mismo recording_id con embargo en segundos | Sólo validación temporal dentro de toma, no otra persona/tarea |
| take | Recording IDs de test no aparecen en train | Identidad/procedencia real de sesiones; recortes/transcodificaciones pueden tener IDs distintos |
| subject | Grupos declarados distintos y recordings distintos | Correspondencia estable/consentida de grupos, no inferida del slot de tracking |
| task | Task IDs declarados distintos y recordings distintos | Equivalencias funcionales, restricciones y resultado comparable, no sólo renombrar tarea |

Los snapshots EVAL fijan recording_id al hash de video congelado, conservan
person_slot/procedencia/preset/cache/calibración declarada y exigen mismas features/
unidades. No abren video/recalculan tracking ni trasladan calibración. Aliases de
un mismo evento físico, IDs importados o subject groups no se vuelven verdad por
pasar JSON. Dos presets del mismo intervalo se rechazan como reserva temporal;
no son dos sesiones ni dos cuerpos.

La normalización (centrado o z-score) y base SVD se ajustan sólo con entrenamiento.
Ridge aprende pares historia→objetivo a horizonte H de muestras soportadas. Todos
los métodos reciben exactamente los mismos pares de entrenamiento y, por cada
condición test, los mismos objetivos válidos. MSE se calcula en unidades originales
al deshacer normalización, no en z-score. No mezcla unidades ni imputa datos.
La base es una representación aprendida, no una prueba de harmonicidad/HIT.

Baselines congelados: persistencia, media train, ridge completo y ridge de
subespacio. Control opcional mezcla objetivos **de pares de entrenamiento** con
semilla, preservando sus valores e inputs; destruye asociación predictiva, no es
una validación de toda la familia de shuffles relacionales de Anni/R04.

Prefijo0: sin adaptación. Prefijo>0 de cada secuencia test:

- pooled_prefix: modelos adicionales con entrenamiento original + prefijo.
- prefix_only: modelos específicos adicionales sólo con ese prefijo.

La normalización/base/regresiones de los adicionales se ajustan únicamente con
ese material permitido. Modelos originales permanecen congelados. Los orígenes
hasta el último timestamp del prefijo quedan excluidos **para todos los modelos**,
para comparar sobre soporte común. Historia posterior puede incluir pasado del
prefijo ya observado; ningún objetivo posterior modifica pesos, escalas o bases.
Un prefijo sin pares suficientes falla explícitamente. Prefijo no equivale a
calibración anatómica ni ajuste de audio; son pesos del predictor experimental.

Missing/gaps dividen history/target support: ninguna ventana cruza un gap, null o
límite de secuencia. H son observaciones únicas, no segundos fijos; cada forecast
conserva origin/target/history_start/elapsed. El estimador es offline y los modelos
congelados; no es el CausalSubspace que se reajusta continuamente en live/R01.
Se distinguen familias; no se altera el instrumento cotidiano.

Worker propio, BLAS/OMP limitados a1 por entorno de lanzamiento, cancelación y
shutdown explícitos; no entrenamiento dentro del hilo live. Artefactos:
request.json, result.json (modelos/scalers/bases/coefs/metrics), predictions.jsonl
(predicciones/targets/errores/orígenes/hash de modelo), manifest.json (hashes,
code/environment/settings/soporte/límites). Repetir utiliza el **código actual**:
comparar hashes de outputs, no confundirlo con ejecutar automáticamente un commit
histórico. Lectura/descarga verifica integridad y declara code_matches_current;
recomputación exacta sólo mediante verify(recompute=True) con código/entorno
correspondiente. Integridad histórica no demuestra corrección del resultado.
Hashes no son custodia firmada ni anonimización. Datos corporales permanecen locales.

La división explícita no vuelve ciego un dataset ya visto. Si se seleccionan
hiperparámetros después de mirar test, es exploración. Antes de inferencia formal,
reservar nuevas tomas/personas y congelar protocolo/configuración en una fase
separada. El propio test no selecciona automáticamente el mejor predictor.
[scikit-learn, prevención de leakage](https://scikit-learn.org/stable/common_pitfalls.html)
recomienda aprender transformaciones sólo en entrenamiento.
[TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
expone un gap entre train/test; este banco añade un embargo explícito dentro de
toma, no utiliza esa clase ni declara validación cruzada completa.

## Primer recorrido reproducible y evidencia

Control sintético de dos osciladores: train y toma reservada con distinta fase,
proveedor synthetic visible. Cambiar el objetivo final reservado conserva modelos
normalización/base/coefs y predictions anteriores; el error de ese objetivo cambia.
Los tests comprueban igualdad de ridge completo/subespacio con base de rango
completo, prefix-only/pooled, shuffle, gaps y reservas/recompute/repeat.

Validación local del cuerpo derecho previamente seleccionado: features del preset
aceptado congelado, seis velocidades zone.1..6.speed enT/s. Train0..25s, test30..60s,
embargo5s, historia2, horizonte3, componentes3 y normalización train.891objetivos
comunes; outputs repetidos tienen hashes idénticos. Receipt sólo local. Es
**within_take**, misma cámara/cuerpo/tarea y video ya visto: no prueba transferencia
entre cuerpos/tareas, ni predicción prospectiva independiente, ni beneficio/HIT.
No se publican métricas corporales privadas, frames, tracking o receipt.

## Control cuadrático opcional (2026-10-03)

`quadratic_control=false` conserva los cuatro predictores anteriores. Al activarlo,
`quadratic_ridge` recibe la misma historia centrada/normalizada con entrenamiento:
coordenadas en orden historia row-major, seguidas de productos de todos los pares
de coordenadas en triángulo superior, incluyendo cuadrados. Se ajustan medias de
regresores/objetivos e intercepto con train; la regularización ridge común no penaliza
el intercepto. No se seleccionan hiperparámetros con test ni se añade información
sensorial. No hay términos cúbicos, frecuencias elegidas ni reajuste online.

El modelo queda congelado y comparte objetivos/causas/gaps/soporte con los anteriores.
Si se eligen prefijo y shuffle, aparecen también adapted_quadratic_ridge y
shuffled_quadratic_ridge bajo sus mismas restricciones. Máximo features × history_steps
de24 (324 regresores); se rechaza exceso antes de encolar, sin reducir dimensiones
silenciosamente. Más capacidad no garantiza generalización y un ridge igual no iguala
complejidad. El usuario puede explorarlo sin cambiar el instrumento ni sus voces.

Web: **Control no lineal: ridge cuadrático R13**, portable por el mismo JSON. El botón
**Cargar recurrencia cuadrática R13** prepara un positivo sintético explícito
`x_next=1-2*x*x`, train/test con distintas condiciones iniciales; no es una nueva
toma corporal. API template acepta `kind=quadratic`; default oscillator sigue igual.

Banco público reproducible con positivo cuadrático, oscilador lineal y ruido IID:

```bash
lab_r13_output="$(mktemp -d /tmp/weaver-r13-public-XXXXXX)"
PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -m research.laboratory.r13_quadratic_controls \
  --output "$lab_r13_output/runs"
```

[Evidencia sintética](r13-quadratic-evidence-2026-10-03.json): positivo MSE cuadrático
~6.27e-16 frente a lineal ~0.473; oscilador ambos ~1.58e-7; ruido IID ambos peores
que la media train. Cada caso repetido bajo entradas/entorno congelados y recomputado.
Son controles positivos/negativos de software, no transferencia/HIT ni superioridad
general. Dieciséis tests de R13 pasan, incluidos prefijo/targets futuros/gaps/shuffle;
Chrome sobre producción/worker real verifica opción, configuración portable, soporte
común y repetición. Nuevas reservas corporales y selección independiente siguen pendientes.

## Experimento siguiente, antes de intervención

1. Definir con participante tarea, resultado útil, restricciones y equivalencias.
   Medidas de error, estabilidad, carga y preferencia deben seguir separadas R12/R10.
2. Reservar una nueva toma y después otras personas/tareas; acordar correspondencias
   funcionales sin imponer misma trayectoria. Fijar grupos y procedencia antes de
   dividir. No asumir disponibilidad de material de élite/para o de prótesis.
3. Separar desarrollo/selección de hiperparámetros de test final; usar una reserva
   nueva cuando la actual ya se exploró. Documentar fuentes/calibraciones/units/
   timestamps/calidad y adaptación permitida. No recalibrar usando objetivos test.
4. Congelar settings y ejecutar baselines/shuffle; comparar sin adaptación, prefijo
   limitado y modelo específico sobre soporte común. Reportar fallos/nulos,
   cobertura, variabilidad entre intentos y grupos; no tratar frames como sujetos.
5. Sólo si hay una señal reproducida, definir feedback/controles de coaching y
   musical, intentos nuevos/orden, retención y transferencia. Un modelo que predice
   bien un video no puede demostrar aprendizaje causado por un feedback nunca dado.
6. Persona–prótesis queda como protocolo separado: usuario define objetivos,
   restricciones y comfort/adaptación; especialistas y sistema cuerpo–dispositivo,
   simulación y ajustes reversibles antes de diseño físico. Cargas/metrología/
   evaluación independiente necesarias; no se generan recomendaciones de dispositivo
   a partir de un score 2D o un óptimo musical.

Pendientes: nuevas tomas/participantes/grupos verificados, mapeos funcionales entre
features distintas, selección nested/validación externa, uncertainty científica,
variantes relacionales/HIT específicas y más predictores, intervención/retención,
sensores/cargas/metabolismo y colaboración usuario–dispositivo. PR de Oliva permanece
sin cambios de head y sin merge; directorios reservados no se tocaron. No se cierra
#27 al completar este banco de software ni se sustituye el roadmap completo.

## Contraste local de recordings congelados (2026-10-03)

Un primer recorrido corporal ya reserva un segundo archivo respecto de dos
segmentos train del primero: seis descriptores de velocidad de zona, mismo
baseline, sin transferir calibración. Prefijo0/60 conserva modelos originales;
al comparar condiciones se usa la intersección exacta de (secuencia, origen,
objetivo) de sus predictions, no sus medias individuales de distinto soporte.
Requests/resultados/repeticiones/receta e identidades corporales quedan locales.
Dos tests Chrome verifican import nativo, worker, repetición, resultados frente
al CLI y ausencia de modificación del instrumento. Ver VALIDATION para alcance.

Se puede repetir cualquier request archivado sin abrir video o recalcular pose:

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  -m harmonic_weaver.lab.research.heldout_run \
  --request /ruta/local/request.json --output /ruta/local/corrida-nueva
```

También puede importarse ese request en R13 y repetirse desde la web. Una
normalización JSON float/int en metadatos puede cambiar el request digest aunque
los valores y modelos numéricos coincidan; comprobar binding/integridad dentro
de cada archivo y comparar resultados por separado. No trasladar datos privados
al repo como requisito de reproducibilidad. Reserva de recording por hash no
certifica adquisición independiente, homología corporal ni escala física.
