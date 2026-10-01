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
