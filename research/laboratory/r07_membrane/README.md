# R07 · Membrana rectangular virtual

Primer núcleo experimental, separado del instrumento live. Implementación:
`harmonic_weaver.lab.research.membrane`. No cierra la investigación R07.

Modelo de ondas con bordes fijos, formas seno-producto y frecuencias
`f_mn = c/2 * sqrt((m/Lx)^2 + (n/Ly)^2)`. Referencia pedagógica primaria:
[Daniel Russell, Penn State: modos de membrana rectangular](https://www.acs.psu.edu/drussell/demos/membranesquare/square.html).

Cada modo satisface `q'' + 2γq' + ω²q = gain * shape(x_exc,y_exc) * PCM`.
Integración exacta por exponencial de matriz con fuerza constante durante
cada intervalo de muestra; salida en el extremo derecho del intervalo.
No hay keypoints, etiquetas corporales, interpolación de pose ni eventos.
Los bloques conservan estado; reset explícito comienza otra realización.

Configuración estricta: dimensiones en metros, velocidad de onda, cantidad
de modos por eje, amortiguación, frecuencia de muestreo, posición normalizada
de excitación y ganancia. Se rechazan modos sobre Nyquist e inputs no finitos.
PCM y ganancia representan fuerza sin calibración física: desplazamiento y
energía modal son proxies, no medidas de presión, metros o joules.
El truncamiento modal tampoco describe dinámica de arena o agua.

Verificación automática inicial: frecuencia/nodos/bordes, respuesta analítica
sin amortiguación a fuerza constante, decaimiento pasivo, igualdad exacta al
particionar bloques, reset y rechazo sin alterar estado. Cuatro pruebas:
`PYTHONPATH=src .venv/bin/python -m pytest tests/research/test_membrane.py -q`.

Segundo corte: `field` suma todos los modos en puntos normalizados declarados;
`field_rms` mide RMS sobre las muestras contiguas entregadas, incluyendo términos
cruzados de interferencia. No normaliza ni recorta la figura. Soporte vacío se
rechaza. No es un promedio de amplitudes modales ni una figura de arena.
Render/proyección tienen presupuesto de ocho millones de elementos por llamada;
usar bloques menores para recorridos largos. Seis pruebas pasan, incluyendo
cancelación entre modos, bordes exactamente nulos y rechazo del render antes de
alterar estado. Falta el acumulador de ventanas con procedencia y selección causal
desde archivos verificados: estos métodos no infieren reloj ni gaps por sí solos.

Tercer corte: `FieldWindow` acumula covarianza modal en memoria acotada por
modos² y proyecta RMS sin almacenar cada superficie. Registra inicio/fin de
muestras y tiempos de salida, rechaza gaps/duplicados y entradas no finitas
sin alterar el acumulador. Ocho pruebas pasan; equivalencia con RMS directo
usa tolerancia numérica, no promete igualdad binaria entre particiones de la
suma matricial. Los índices son declarados por el llamador: no certifican por
sí mismos procedencia del PCM, ausencia de un reset externo ni reloj físico.

Cuarto corte: `membrane_pcm.project` recibe un run R05 individual completo,
verifica todos sus artifacts antes/después y excita exclusivamente desde
`sum.wav`. Exige coincidencia de sample rate; no remuestrea. Reproduce desde
estado cero y muestra cero hasta el fin solicitado; acumula sólo la ventana
seleccionada, sin eliminar su historia previa ni leer excitación futura.
Devuelve grilla RMS, reloj, request y hashes de PCM/manifest. Límite actual:
120 segundos de historia causal por llamada, sin cache ni worker todavía.
Diez pruebas conjuntas pasan, incluyendo repetición, particiones, comparación
directa con campo, rechazo de reloj/ventana e integridad alterada. Integración
con pares R05, worker/API/UI y controles de campo siguen pendientes.

Quinto corte: selector explícito `arm=single|excited|mapped`. Para pares, verifica
también el padre y el brazo no seleccionado antes/después de proyectar; devuelve
hash del manifest del par y del brazo. No compara corridas independientes como
si compartieran input/reloj. Doce pruebas pasan: incluye ambos mecanismos sobre
un soporte idéntico, rechazo por alteración del brazo no seleccionado y mutación
de un input durante la proyección. Worker/API/UI y banco de controles pendientes.

Sexto corte: `membrane_run` persiste request normalizado, resultado y manifest
con hashes de fuente/configuración/código y entorno. No copia PCM ni datos
corporales. CLI: `PYTHONPATH=src .venv/bin/python -m
harmonic_weaver.lab.research.membrane_run --source RUN_R05 --request REQUEST.json
--output NUEVA_CARPETA`. Destino existente se rechaza. `verify` comprueba hashes,
contrato de request, reloj, grilla finita/no negativa y bordes nulos, con rehash
final. No recalcula la simulación ni autentica autoría: un manifest reescrito
no es evidencia científica independiente. Trece pruebas pasan, incluyendo
resultados persistidos repetidos e integridad alterada. Este corte todavía no
es un worker cancelable: lifecycle, interrupciones y exposición web pendientes.

Séptimo corte: worker one-shot con flock no bloqueante, request/source.json
congelados y manifest running/failed/complete. Referencia local al run R05,
sin copiar sus datos. Computa en carpeta interna, verifica artifacts y repite
la proyección antes y después de promover el resultado para revalidar fuente;
rehash de inputs/result previo al complete. Es conservador y actualmente
triplica el cálculo; optimizar sólo preservando esos contratos. Quince pruebas
del conjunto pasan (dos del worker), incluyendo publicación verificable,
rechazo de rerun y fuente ausente sin resultado publicado. Todavía faltan
pruebas de muerte real durante promoción, servicio propietario/cancelación,
API/UI. No se afirma durabilidad frente a corte de energía.

## Próximos cortes, necesarios para la entrega

- Adaptador de PCM verificado R05: frecuencia de muestreo declarada, ventana
  causal, preroll/reset y soporte temporal explícitos; no alimentar pose.
- Campo de desplazamiento y RMS temporal, nodos y controles con señales
  conocidas. Límites de memoria y duración; prueba de truncamiento modal.
- Worker, artifacts/manifest verificables, cancelación y recuperación de
  interrupciones siguiendo contratos R05/R06.
- API/UI con todos los parámetros, presets portables, visualización sincronizada
  y contraste entre estado de voces, mezcla final y membrana. No confundir estas
  rutas ni aplicar parámetros a live silenciosamente.
- Banco reproducible de señales/control y recuperación de atributos reservados.
  Las semejanzas de figuras no demuestran información conservada ni HIT.
- Medio físico: faltan actuador, membrana/material/bordes caracterizados,
  observación sincronizada y calibración. No se ha realizado escucha ni ensayo
  físico ni validación humana de esta implementación.
