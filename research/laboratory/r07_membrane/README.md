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

Octavo corte: `MembraneService` reutiliza inventario/lifecycle propietario de
R03/R06. Un proceso activo por instancia, cancelación sólo de procesos propios,
cierre explícito, restauración de inventario y descargas verificadas. La referencia
local `source.json` no se ofrece como artifact descargable; el worker no copia
PCM. Diecisiete pruebas pasan, incluidas ejecución real, restauración, rechazo
de cancelación ajena, hash alterado y cancelación inmediata de subprocess propio.
La cancelación inmediata prueba la transición queued: falta kill real dentro de
la promoción y prueba de cancelación durante cálculo ya running. API/UI pendientes.

Noveno corte: prueba con subprocess real pausado justo después del rename de
result.json, aún manteniendo flock. Mientras está vivo, el inventario conserva
running y rechaza descargar; tras SIGKILL y wait, restaura interrupted, conserva
el resultado incompleto sin descargarlo y permite manifest diagnóstico. Tres
pruebas del servicio pasan. Esto cubre muerte en ese punto de publicación, no
todos los puntos de fallo ni corte de energía del host. Sigue pendiente cancelar
un cálculo ya running mediante servicio y la integración API/UI.

DÉcimo corte: API `/api/research/r07` para inventario/inicio y `/{id}`,
`/{id}/cancel`, `/{id}/artifacts/{name}`; configuración portable en
`/configuration`. Inicio selecciona `source_run_id` del inventario R05, sin
aceptar rutas arbitrarias desde HTTP. Presets contienen settings y schema1,
sin fuente/persona/calibración. Ventanas inválidas se rechazan por contrato.
Una prueba HTTP con worker real pasó: configuración, selección, publicación,
descarga verificada y rechazos de source.json, ID y schema inválidos. UI y
prueba HTTP de cancelación running/restauración quedan pendientes.

Undécimo corte: panel R07 en Investigación, con selección explícita de corrida
R05/brazo, todos los parámetros numéricos, import/export de preset portable,
inventario/cancelación y descarga. Figura RMS congelada con escala de color
manual (sin normalización automática), valores por celda y límites visibles.
Default de ventana: primeras 48000 muestras a sample rate 48000; elegir una
fuente con otro reloj requiere ajustar sample_rate explícitamente. Los cambios
del borrador no alteran una figura calculada. TypeScript/Vite build pasó y el
recorrido API real sigue pasando. Todavía falta prueba de navegador contra
servidor real y seguimiento de ventanas con audio; este panel inicial calcula
una ventana bajo demanda, no ofrece aún animación continua ni escucha validada.

Duodécimo corte: servicio verifica fuente individual/par, reloj y soporte antes
de crear job. Fuentes inválidas no dejan carpetas/jobs. Cancelación probada sobre
subprocess real ya running, con 256 modos y 10 segundos de cola sintética:
termina, conserva hashes de inputs, bloquea result y permite manifest diagnóstico.
Cinco pruebas del servicio y una API pasan (seis). UI de navegador, seguimiento
continuo y banco de controles siguen pendientes; no cambia defaults de live.

Decimotercer corte: Chrome headless contra servidor HTTP aislado, panel real y
worker real, con PCM sintético. Pasó import/export sin ejecutar, selección R05,
cálculo, figura 33×33, descarga verificada y recuperación del inventario al
recargar (3 s). Fixture `tests/r07_http_fixture.py`, harness
`laboratory-ui/tests/r07_harness`, test `membraneNetwork.spec.ts` con
`PLAYWRIGHT_CHANNEL=chrome LAB_R07_NETWORK_URL=http://127.0.0.1:8879`.
No dispositivos de audio, cámara ni datos corporales; servidor de prueba detenido.
Esto verifica el recorrido estático HTTP, no escucha humana ni sincronización
física ni animación de ventanas durante reproducción.

Decimocuarto corte: verifier refuerza reloj entero, soporte/grilla exactos,
historia inicial cero, formato SHA256 y consistencia de fuente individual/par.
Ocho mutaciones semánticas con checksum reescrito se rechazan (reloj, borde,
negativo, NaN, historia, source, pair, settings). Conjunto R07 backend/API:
29 pruebas pasan en 7.07 s. Esto detecta incompatibilidades, no certifica que
todo valor interior positivo haya sido calculado honestamente: no rerender ni
firma de custodia. IMPLEMENTATION_STATUS registra alcance y pendientes actuales.

Decimoquinto corte: `RollingFieldWindow` mantiene exactamente las últimas W
muestras modales, sin futuro ni relleno. Warmup explícito si aún hay menos de W;
gaps/duplicados rechazados, reset explícito con nuevo reloj, buffers propios.
Presupuesto de ocho millones de elementos de historial; covarianza recalculada
al observar para evitar deriva acumulada por resta de ventanas. Diez pruebas
del núcleo pasan, incluidas paridad con soporte pasado directo y particiones.
Es infraestructura de animación, todavía no conectada a worker/artifacts/UI.

Decimosexto corte: request opcional `trajectory={window_samples,hop_samples}`
produce una secuencia en una sola pasada por PCM. Cortes exactos de muestra,
último frame en stop aunque no complete hop, historial desde cero y RMS de las
últimas W muestras (puede comenzar antes del inicio de observación). Presupuestos
de un millón de valores de grilla y ocho millones de elementos de historial.
Verifier comprueba inventario, reloj causal, warmup y grillas de cada frame.
Ausencia de trajectory conserva formato anterior. Cinco pruebas del adaptador
incluyen comparación directa de cada ventana pasada y paridad entre bloques;
con nueve pruebas de artifacts: catorce pasan. Exposición de esta opción y
selección sincronizada del frame en UI siguen pendientes.

Decimoséptimo corte: UI ofrece secuencia opcional (default off), ventana/paso
en muestras y selector de frames que distingue RMS global de ventanas móviles.
Al abrir otro resultado se reinicia selección. Chrome HTTP real pasó (1.9 s),
incluyendo preset de secuencia, cuatro frames con reloj exacto, selección de
primero/último y reload. Build TypeScript/Vite pasó. Falta seguimiento automático
del audio; esta selección temporal es manual y no valida sincronización física.

Decimoctavo corte: endpoint listen R07 resuelve únicamente el mix vinculado
al resultado completo, revalida fuente/par y hashes; reutiliza preview float32
seekable R05 sin tocar DOUBLE. Prueba API pasó con Range206 y rechazo tras
alterar PCM. UI ofrece audio y seguimiento opt-in: último frame cuyo tiempo ya
ocurrió, sin frame antes del primero; RAF observa currentTime, incluidos seeks,
pausas y loops. Build pasó. Falta probar esta nueva reproducción/seguimiento
en Chrome real y hacer portable el estado de reproducción/escala visual;
no se afirma escucha ni sincronización física.

Decimonoveno corte: Chrome real decodifica preview y pasa seguimiento opt-in:
antes del primer frame no muestra futuro, seek pausado selecciona último frame
pasado, seek hacia atrás limpia selección, play avanza reloj/figura y pause
congela tiempo. Test HTTP completo pasó en 3.7 s con worker/PCM sintéticos;
servidor detenido. Sigue pendiente loop automático y configuración visual/playback
portable; esto no prueba latencia acústica, dispositivo físico ni escucha humana.

Vigésimo corte: configuración portable incluye playback estricto con
follow_audio=false, loop_audio=false y color_scale=10000 por default; importar
no inicia reproducción ni job. UI permite loop nativo explícito y exporta/importa
los tres controles. Defaults previos de escala y seguimiento se preservan.
Build y prueba API pasan, incluyendo roundtrip sin job y bool numérico rechazado.
Falta probar loop automático y este nuevo preset visual en Chrome real.

Vigésimo primer corte: Chrome HTTP real pasó en 4.1 s, incluyendo roundtrip
de escala=1234/follow=true/loop=true, importación manteniendo audio pausado,
wrap nativo observado por timeupdate y selección de primer frame tras volver al
comienzo. Servidor sintético detenido. El test usa decoder real, no eventos
falsos; no mide R24 ni latencia física y no constituye escucha humana.

Vigésimo segundo corte: `Membrane.transfer_response` calcula respuesta compleja
estacionaria de la discretización exacta held-input a frecuencias declaradas,
incluyendo cero. Exige amortiguación positiva y frecuencias bajo Nyquist; no
altera estado causal. Convención de fase: input index n y output del extremo
derecho de su intervalo. Doce pruebas del núcleo pasan: respuesta estática
coincide con fuerza/ω² y forcing coseno muestreado converge a amplitud/fase
predichas (cola de simulación 2 s), bordes nulos/rechazos. Es control analítico
para banco/convergencia, todavía sin UI ni interpretación como medio calibrado.

Vigésimo tercer corte: `membrane_transfer.compare` compara resoluciones
modales anidadas declaradas sobre idénticas frecuencias/puntos/medio. Exporta
respuesta compleja cruda, magnitud, diferencia compleja y diferencia de fase
respecto al paso previo; fase a respuesta exactamente cero es null, cerca de
cero puede ser inestable. Seis pruebas pasan: repetición, bordes, diferencias,
rechazo de resoluciones repetidas/no anidadas y reloj/medio/puntos inválidos.
No declara convergencia al continuo ni usa el último corte como verdad física.
Pendientes: artifacts reproducibles, API/UI y señales transientes de control.

Vigésimo cuarto corte: `membrane_transfer_run` persiste request/result/manifest
y verifica inventario, hashes, código y versiones antes de recalcular el banco
acotado. Rechaza valores reescritos aunque se actualice checksum. Exige mismo
código/entorno declarado; no promete igualdad entre builds numéricos ni firma
de custodia. CLI con `--request REQUEST.json --output NUEVA_CARPETA`; no overwrite.
Ocho pruebas del banco/artifacts pasan, incluyendo repetición y rechazo explícito
de entorno/código diferentes. API/UI y controles transientes pendientes.

Vigésimo quinto corte: servicio/API `/api/research/r07-transfer` separado de
PCM, con configuración schema1, ejecución acotada síncrona, inventario restaurado
y artifacts recalculados/verificados. Panel web permite editar todo el request
JSON portable, validar sin ejecutar, calcular y comparar magnitud/diferencia/fase
en tabla. Build y prueba API de dos corridas/reload/tamper pasan. No usa worker
cancelable: banco de tamaño acotado, endpoint sync en threadpool. Chrome real
de este panel y controles transientes pendientes.

Vigésimo sexto corte: Chrome HTTP real del panel de transferencia pasa (1 s):
editar puntos/frecuencias/resoluciones, validar preset sin job, dos cálculos con
artifacts idénticos, tabla de ocho filas y restauración tras reload. Fixture
sintético aislado detenido. No hay participantes/audio físico en este banco;
controles transientes y convergencia/atributos científicos siguen pendientes.

Vigésimo séptimo corte: `membrane_controls.compare` genera impulso held de una
muestra, pulso, suma de todas las componentes declaradas y ruido Gaussian seeded
desde cero sobre mismo medio/reloj/puntos. Reporta dosis digital sum_squares,
peak, RMS de campo y energía modal proxy final sin igualar energía ni normalizar.
Tres pruebas pasan: repetición/semilla, suma multisine (tolerancia de aritmética),
bordes, cero y particiones de bloques, contratos. No es ruido de presión calibrado
ni impulso Dirac; artifacts/API/UI de este banco todavía pendientes.

Vigésimo octavo corte: `membrane_controls_run` guarda request/result/manifest
con hashes de código y versiones Python/NumPy/SciPy. Verificador read-only
recalcula el banco y rechaza cambios de valores aun con checksum reescrito;
rechaza entorno desconocido y destino existente. CLI `--request REQUEST.json
--output NUEVA_CARPETA`; no guarda PCM ni datos corporales. Cinco pruebas
núcleo/artifacts pasan, incluyendo dos corridas idénticas y request inválido
sin crear carpeta. Worker cancelable y API/UI pendientes; verificación exacta
es del entorno registrado, no una promesa de paridad numérica entre builds.

Vigésimo noveno corte: worker flock y ControlService propietario separado
R07-CONTROLS. Publica copia JSON del resultado interno verificado con hash y
request congelados; conserva artifacts internos para recálculo al descargar.
Comparación de requests normalizada por contrato permite defaults int/float
equivalentes sin relajar bools. Dos pruebas de subprocess real pasan: repetición,
restauración/tamper y cancelación de cálculo ya running. API/UI y kill durante
promoción de este banco pendientes; no toca audio/percepción live.

Trigésimo corte: API `/api/research/r07-controls` configura schema1, inicia,
lista, reporta/cancela y descarga verificada. Panel web permite editar todos
los parámetros via JSON portable, validar sin ejecutar y comparar dosis/peak,
RMS por punto y energía proxy final. Build y prueba API con worker real pasan.
Defaults del instrumento no cambian. Pendiente Chrome real de este panel,
interrupción durante publicación y protocolo de recuperación de atributos.

Trigésimo primer corte: Chrome HTTP real del banco transiente pasó (2 s):
preset seed29/800 muestras validado sin job, worker real, tabla de cuatro
entradas, artifact con dosis declarada y recuperación al recargar. Servidor
aislado detenido; señales sintéticas sin hardware/participantes. Permanece
pendiente kill durante publicación de este banco, recuperación de atributos
en soporte reservado y protocolos/calibración físicos.

Trigésimo segundo corte: SIGKILL real del worker de controles después de rename
de result y antes de complete. Flock mantiene running mientras vive; al morir
restaura interrupted, conserva bytes incompletos, rechaza descarga y conserva
manifest diagnóstico. Tres pruebas del servicio pasan; conjunto completo R07
backend/API: 52 passed en 10.76 s. IMPLEMENTATION_STATUS actualizado. No prueba
corte de energía ni todos los puntos de fallo; recuperación de atributos y
validación humana/física continúan pendientes.

## Recuperar controles históricos

Abrir un banco transiente conserva el resultado archivado: comprueba inventario,
hashes, request congelado y soporte, sin renderizar de nuevo. La web indica
`Integridad verificada; sin recalcular` y muestra por separado si coinciden código
y entorno. Una diferencia de procedencia no impide leer la corrida.

`Recalcular verificación de controles R07` compara contra la implementación actual
sin sobrescribir artifacts. Exige estructura y soporte exactos, con tolerancia
relativa 1e-12 y absoluta 1e-15 para floats; int/float equivalentes se admiten sólo
con valor exactamente igual, sin convertir bools. El endpoint es
`GET /api/research/r07-controls/{id}/verification?recompute=true`; sin ese parámetro
informa integridad solamente. `membrane_controls_run.verify` conserva recálculo
por defecto para workers y llamados explícitos existentes.

Código/entorno coincidentes no son una prueba numérica; hashes locales no son
custodia firmada. El banco sigue siendo sintético y no valida una membrana física.
No se cambian defaults del instrumento ni se aplica nada al audio live.

## Recuperación de atributos en casos reservados

`membrane_readout` lee exclusivamente figuras RMS calculadas desde el PCM final.
La selección local declara un ID de proyección R07, rol train/test, grabación,
grupo corporal y valores de atributos en unidades explícitas. El servicio
verifica y congela figuras existentes; las etiquetas entran después, en el
decodificador, y no modifican el sonido ni la membrana.

En Investigación → **R07 · Recuperación de atributos reservados**:

1. Editar/validar el preset: atributos/unidades, reserva within_take/take/subject,
   ridge, normalización, embargo y semilla. Exportarlo no incluye casos ni etiquetas.
2. Actualizar figuras disponibles. Agregar casos con IDs de grabación/grupo y
   atributos declarados; el JSON de casos permite corregir o retirar selecciones.
   Conservar el mismo ID de grabación entre renders/presets de una toma.
3. Calcular con al menos tres casos train y dos test, mismo medio y grilla de
   2×2 a32×32. Ventanas idénticas de un PCM no cuentan como múltiples casos.
   take/subject excluyen grabación o PCM compartidos; subject excluye grupo
   compartido. within_take exige entrenamiento anterior y embargo declarado.
   Entre PCM distintos de la misma grabación, el origen temporal se toma del
   manifest R05 verificado; si ya no está disponible, no se inventa ese offset.
4. Comparar siete lecturas sobre exactamente los mismos casos reservados:
   media train, ridge del RMS completo/forma/magnitud y sus controles train-label
   shuffle. Cada atributo conserva su MSE y unidad²; no promediamos unidades
   incompatibles. Normalización/intercepto/coefs usan exclusivamente train.
5. Descargar dataset/result/manifest o reabrir la corrida. La lectura verifica
   integridad y binding de casos/atributos; recálculo explícito verifica números
   sin sobrescribir archivos. Una diferencia de código/entorno se informa aparte.

La forma divide cada vector por su norma L2; un campo cero produce forma cero.
La magnitud es norma L2 sobre puntos de grilla, no loudness ni energía física.
Una tolerancia relativa de resolución numérica evita amplificar a varianza
unitaria el roundoff de formas constantes. El solve dual limita el trabajo a
64 casos; no hay renderer, captura ni audio en esta comparación síncrona.
Publicación usa staging; restos de staging no aparecen como corridas completas.
No se afirma recuperación tras corte de energía en todos los puntos de rename.

CLI sobre un dataset congelado local:

```bash
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.membrane_readout_run \
  --dataset DATASET.json --output NUEVA_CARPETA
```

`verify(folder)` comprueba integridad; `verify(folder,recompute=True)` compara
contra el decodificador actual, tolerancias rel1e-12/abs1e-15. No necesita los PCM
ni las proyecciones originales después de congelar el dataset. El snapshot
contiene RMS, etiquetas e IDs: mantenerlo local cuando provenga de datos corporales.

Control ejecutado en fixture sintético R05→PCM→R07: seis ganancias declaradas
(train .2/.4/.6/.8, test .3/.7), mismo medio y figura5×5, ridge .001. MSE de
ganancia en los dos casos comunes: media train .04; campo completo
3.0862482930651985e-11; magnitud2.498750468642882e-9; forma normalizada .04.
El control shuffle del campo completo dio .0016003555654286051. La recuperación
es de una ganancia codificada explícitamente: prueba el canal configurado y
su confusión con magnitud, no HIT ni información corporal. No aporta significancia
ni independencia humana. Shuffle tampoco conserva autocorrelación temporal.

## Etiquetas desde features corporales congeladas

Para una figura procedente de R05 ligado a EVAL, **Cargar señales para etiquetas
R07** muestra las señales/unidades de la corrida exacta y la ventana de fuente
correspondiente. No acepta otra evaluación arbitraria: verifica la vinculación
PCM→input→trace. El origen R05 se suma a los índices de muestras de la figura;
una ventana en la cola del sonido no recibe una etiqueta corporal contemporánea.

Agregar señales al **Perfil portable de etiquetas R07** y editar su JSON:
`method=mean|rms|std|peak_abs`, `min_observations`, `min_observed_fraction` y
`max_gap_s`. Las señales deben compartir unidad; se usan observaciones únicas
y soporte observado común. Son estadísticas de muestras, sin interpolación ni
ponderación temporal (`std` usa ddof=0). Fracción de observaciones válidas no es cobertura en
segundos ni exactitud de pose. El máximo gap incluye los bordes de la ventana.

**Calcular atributos desde EVAL R07** completa targets, nombres `method:signal`
y unidades, y guarda el perfil como `label_settings` dentro del preset portable.
Muestra cobertura, gaps y duplicados excluidos. Agregar el caso conserva el perfil
de cálculo; al congelar el banco, el servidor recalcula esa etiqueta contra las
fuentes verificadas y rechaza valores/nombres/unidades que hayan cambiado.
Editar a mano el target retira la declaración de etiqueta calculada.
Los IDs de grabación/grupo siguen siendo declaraciones humanas; no se completan
como identidad corporal inferida. Las etiquetas no entran al renderer.

Dataset archivado conserva resumen, cobertura/causas, digest, módulo agregador
importado/NumPy y procedencia EVAL. Recálculo del decoder usa esos targets congelados;
no revalida automáticamente el cálculo corporal si ya no existen las fuentes.
Cambiar el código de etiquetas no reescribe un archivo histórico. Las pruebas
con tracking sintético verifican este recorrido; no son observaciones humanas.

## Pendientes de entrega e investigación

El adaptador PCM R05, campos/RMS, workers, recuperación, API/UI y controles
transientes están implementados; sus cortes y pruebas se registran arriba.
- Ejecutar el banco con features corporales reales o anotaciones humanas y tomas
  independientes; ampliar controles de espectro/temporalidad y probar estabilidad
  frente al medio/resolución. IDs declarados no certifican identidad ni ceguera
  prospectiva. Ajustar mirando la prueba convierte la comparación en exploratoria.
  Las semejanzas de figuras no demuestran información conservada ni HIT.
- Medio físico: faltan actuador, membrana/material/bordes caracterizados,
  observación sincronizada y calibración. No se ha realizado escucha ni ensayo
  físico ni validación humana de esta implementación.

## Receta corporal local con ventanas reservadas — 2026-10-05

`body_readout.py` enlaza los núcleos existentes: trace EVAL congelado → mapeo de
amplitud experimental R05 con seis carriers → campos RMS R07 → etiquetas de
features EVAL → decoder train-only. Conserva plan antes de render/scoring, PCM,
proyecciones, etiquetas/causas/unidades, dataset y resultados/manifests locales.
No vuelve a inferir pose, lee/copia video ni abre un dispositivo sonoro.

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  research/laboratory/r07_membrane/body_readout.py \
  --evaluation-dir /ruta/local/evaluacion/result \
  --plan research/laboratory/r07_membrane/body_readout_example.json \
  --output /ruta/local/corrida-r07-nueva
```

El ejemplo es configuración sin datos/IDs corporales; exige que la corrida EVAL
incluya [2,34) y la señal elegida. Ajustar previamente ventanas, índices, señales,
medio y mapeo a la pregunta; no elegirlos tras mirar scores reservados. Los tiempos
son segundos fuente. Ventanas train preceden a test y conservan embargo explícito.
Etiquetas usan observaciones únicas válidas, su unidad propia y límites de cobertura;
no rellenan gaps. `source_origin_s` conserva el offset del PCM respecto de la fuente.
El alias EVAL es local y derivado de su manifest: no es un job registrado en la UI.

`dataset.json` permite repetir sólo el decoder con `membrane_readout_run`, sin
video/PCM. La receta usa archivos congelados fuera del inventario web; los mismos
mecanismos y parámetros se operan en los paneles R05/R07 con corridas registradas.
No registra automáticamente estos checks como ensayos en el servidor cotidiano.
Un fallo conserva prefijo/plan, sin manifest final completo; repetir usa destino
nuevo. Datos corporales y scores no se publican por ejecutar este comando.

Recorrido local con tracking corporal: cinco ventanas, tres train/dos test dentro
de la misma toma; PCM/dataset/resultados repetidos bajo las mismas entradas/entorno,
y recálculo del decoder verificado. Resultados numéricos privados. Prueba sintética
end-to-end adicional conserva EVAL byte por byte y comprueba etiquetas angulares
con unidad deg/s aunque la excitación venga de velocidad T/s.

Este corte mide el canal configurado del mapeo experimental R05 y la membrana
teórica. Compararlo con Shaper requiere otro origen de PCM declarado. Dentro de
una toma no hay generalización entre recordings/personas ni muestras independientes;
features de tracking no son ground truth corporal y la membrana no es cymatics físico.


## Origen Shaper desde la web

En Investigación → R07, elegir «EVAL · motor Shaper», una evaluación completa
con PCM habilitado y su corrida. El banco usa el WAV estéreo posterior a shape,
master y limitador, producido por el kernel offline de Shaper. No abre la R24 ni
cambia el instrumento live. Elegir explícitamente promedio `(L+R)/2`, izquierdo
o derecho para excitar la membrana: son condiciones diferentes, no normalización.
El reproductor conserva el audio estéreo original; la figura usa la reducción
congelada. La selección ajusta la frecuencia de muestreo al render; no hay resampling.

Los controles de medio, ventana, grilla y trayectoria siguen disponibles. El preset
portable conserva la reducción estéreo, sin IDs ni rutas de fuentes. La figura
registra evaluación/corrida, hashes de manifest/PCM/trace, etapa de síntesis y offset
fuente. Las etiquetas corporales leen la misma corrida; rechazan ventanas en el tail
sonoro, porque no tienen features contemporáneas. El readout conserva ese offset
para las reservas temporales. No copia video, tracking ni PCM.

La ruta POST `/api/research/r07/from-evaluation` recibe `evaluation_id`, `run_index`
y `settings` (incluidos `arm: single` y `stereo_mix`). Las fuentes R05 y sus artifacts
previos siguen disponibles. Publicación verifica hashes del origen antes/después,
sin volver a renderizar la membrana dos veces como hacía el worker anterior.

Pruebas nuevas usan movimiento sintético → EVAL → motor Shaper real → membrana,
reducciones/particiones/repetición, worker, labels/cola, integridad y reproducción
estéreo con rangos HTTP. No constituyen aceptación auditiva ni cymatics físico.
Este origen habilita el contraste con R05. La primera corrida corporal Shaper
con reserva temporal y repetición está realizada; no establece generalización
entre tomas/personas ni equivalencia de mecanismos.


## Receta repetible con Shaper

La misma receta admite un origen `source.provider: evaluation_shaper`, `run_index`
y `projection.stereo_mix` explícitos. El EVAL debe estar completo y tener PCM:

```bash
PYTHONPATH=src .venv/bin/python -m research.laboratory.r07_membrane.body_readout \
  --evaluation-dir /ruta/local/evaluacion/result \
  --plan research/laboratory/r07_membrane/body_readout_shaper_example.json \
  --output /ruta/local/check-shaper
```

El ejemplo declara 48 kHz; ajustar al sample rate de la corrida antes de ejecutarlo.
Las ventanas son tiempos fuente, no tiempos desde el comienzo del archivo PCM.
Se usa el PCM in-place y se congela su referencia, no se copia ni rerenderiza.
`origin-manifest.json` distingue R05/Shaper; `dataset.json` permite repetir sólo
el decoder con sus controles mean/shape/magnitude/full y targets mezclados.

Corrida corporal local: cinco ventanas (tres train/dos test), plan congelado y
recomputación del decoder. Render Shaper preservó byte por byte la traza EVAL de
features/targets anterior. No nueva escucha humana ni toma independiente.
Comparar con R05 requiere declarar ambos mapeos y conservar medio/sample rate,
ventanas, etiquetas y reservas; una diferencia no identifica qué etapa la causa.
