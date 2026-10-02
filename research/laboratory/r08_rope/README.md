# R08 · Cuerda en plano de imagen

Primer contrato manual `rope_annotations.Annotation`: hash de medio, dimensiones,
frame index y timestamp de fuente explícitos. Estados observed/partial/
unidentifiable/absent y causas blur/occlusion/crossing_ambiguity/out_of_frame.
Segmentos visibles independientes; no se unen detrás de una oclusión. Métrica
inicial: longitud proyectada visible en píxeles, usando dimensiones reales de
imagen, sin confundir coordenadas normalizadas con escala isotrópica.

Dos pruebas pasan: segmentos separados y dato ausente, rechazo de observación
inventada, bool como índice y clocks repetidos. Datos exclusivamente sintéticos.
No hay nueva anotación humana, identidad inferida, tracker de cuerda ni 3D.

Próximos entregables necesarios:

- Binding verificable al medio local y selección de segmentos/frame clocks.
- Persistencia/versiones/edición web de curvas, quality causes y presets de
  herramientas; videos y anotaciones corporales siempre locales.
- Asistencia configurable de segmentación y propuesta de curvas, conservando
  qué es manual, propuesto y confirmado; ninguna interpolación invisible.
- Benchmark de blur/oclusiones/cruces y validación humana de clips difíciles.
- Trayectorias/extremos y propagación mano–cuerda sólo sobre soporte observable,
  con gaps, clocks/unidades y controles explícitos.
- R09: ambigüedad de cruces 2D no resuelve profundidad/nudos. Cámaras multivista
  calibradas/sincronizadas o sensores se eligen con evidencia del benchmark.

Referencia de alcance: issue #23 y research/laboratory/AGENDA.md. Rama apilada
sobre R07 PR #74; no merge automático. Las preguntas científicas siguen abiertas.

Segundo corte: `rope_media.probe/bind` usa ffprobe sobre video local regular,
hash antes/después, dimensiones y PTS de cada frame decodificado (no reloj
inventado desde FPS). Tiempo cero es el primer PTS, conservando su origen.
Binding exige mismo hash/dimensiones e índice/timestamp (tolerancia 1 µs).
Fuentes rotadas, píxel no cuadrado y dimensiones variables requieren adaptador
explícito y se rechazan por ahora. Clips de 1–14400 frames; timeout60s y límite
de JSON16MB tras probe (no garantiza límite de memoria del subprocess).
Tres pruebas conjuntas pasan con MP4 sintético real generado por FFmpeg,
incluyendo identidad/dimensiones/reloj/índice/symlink inválidos. No se procesó
video privado ni se anotó cuerda humana. Persistencia y UI continúan pendientes.

Tercer corte: `rope_run.run/verify` guarda revisiones en carpetas nuevas,
annotation/media-clock/result/manifest con hashes y lineage opcional al manifest
padre. Revalida medio antes de complete; no copia video ni guarda rutas/persona.
Verifica report recalculado y frames contra reloj congelado, rehash final.
Parent debe ser revisión verificable del mismo medio al crear hija; conservar
su hash no equivale a resolver toda la cadena después. Cuatro pruebas pasan,
incluyendo padre intacto, no overwrite y report alterado con checksum reescrito.
Estado actual del video requiere rebind explícito; UI/API y asistencia pendientes.

Cuarto corte: RopeService guarda sólo carpetas de revisión nuevas con IDs
UUID, inventario verificable restaurable, descarga whitelist y rebind explícito
al medio vigente. Resolución de source queda a cargo de biblioteca/API posterior;
no se guarda ruta privada en artifacts. Prueba con MP4 sintético real pasa:
dos revisiones/lineage/restauración/rebind, IDs/rutas inválidos, report alterado
y medio modificado rechazados. UI/API y anotaciones humanas aún pendientes.

### Corte 5: biblioteca y API

`GET /api/research/r08` recupera revisiones verificadas. Con runtime,
`POST /api/research/r08/probe` recibe `{media_id}` de la biblioteca y devuelve
hash, dimensiones y reloj decodificado. `POST /api/research/r08` recibe
`{media_id, annotation, parent_id?}`; `POST /api/research/r08/{id}/rebind`
recibe `{media_id}` y comprueba el archivo actual. Los cuatro artefactos se
obtienen mediante `/api/research/r08/{id}/artifacts/{name}`. No se aceptan
rutas HTTP arbitrarias ni se copia el video. Un runtime ausente permite
consultar revisiones, pero no crear vínculos nuevos. No se infiere persona,
calibración ni profundidad.

Verificación: seis tests de contratos, medios, persistencia, servicio y API
pasaron con MP4 sintético; incluye restauración entre instancias, linaje,
rechazo de rutas/campos extra, whitelist y cambio del archivo fuente.
Pendiente: editor web, asistencia de extracción y anotaciones humanas.
El probe síncrono tiene timeout de 60 s; la lectura masiva de frames deberá
migrar a trabajo observable antes de ofrecer análisis de videos largos.

### Corte 6: panel web inicial y resolución persistente

El panel R08 selecciona assets de biblioteca, prepara una anotación vacía,
permite editar JSON, guardar una revisión derivada, recuperar revisiones,
verificar el video actual y descargar artefactos. No inicia tracking ni audio.
La resolución usa el índice persistente de assets, no IDs efímeros de jobs.
Test de API con VideoLibrary real restaurada sin jobs: pasó; TypeScript y
Vite build pasaron. Interacción del panel aún no verificada en navegador.
Pendientes: editor gráfico sobre video, visor del reloj decodificado y
extracción asistida; el textarea no sustituye esos entregables.

### Corte 7: editor gráfico por índice decodificado

Preparar o verificar una revisión habilita el editor: elegir índice muestra
el timestamp del inventario y un PNG extraído con FFmpeg por `select n`,
no un seek aproximado del navegador. Hash de fuente comprobado antes y
después; imágenes sólo en respuesta HTTP, no se guardan/copían videos.
Click agrega puntos normalizados, nuevo tramo separa curvas, controles
permiten estado/causas/nota. Aplicar frame actualiza el borrador en orden;
guardar crea revisión. Cambiar de frame descarta ediciones no aplicadas.
Backend y compilación comprobados, interacción en navegador pendiente.
Extracción/probe siguen síncronos y bounded por timeout, con lectura
completa por solicitud: falta worker observable/cache de imágenes para
interacción eficiente. No afirmar que está listo para clips largos.

### Corte 8: navegador con API real

Harness aislado `tests/r08_http_fixture.py` crea únicamente un MP4 sintético
y una VideoLibrary persistida sin trabajos de pose ni dispositivos de audio.
El test Chrome `laboratory-ui/tests/ropeNetwork.spec.ts` verificó clicks y
coordenadas sobre PNG real, dos frames con tiempos reales, estado ilegible
por oclusión sin curva inventada, guardado, recarga de página, recuperación,
rebind al video y revisión derivada con linaje. Pasó en 1.9 s (suite 2.6 s).
El primer intento falló por leer el textarea antes de la respuesta HTTP;
se corrigió la espera de la prueba. Esto no equivale a aceptación humana ni
a validación de tracking automático de soga. Servidor de prueba detenido.

Ejemplo de ejecución (directorios temporales nuevos para cada corrida):
compilar `tests/r08_harness` con Vite; iniciar fixture con `--root`, `--ui`
y `--port`; ejecutar Playwright con `PLAYWRIGHT_CHANNEL=chrome` y
`LAB_R08_NETWORK_URL=http://127.0.0.1:<port>`. El test requiere inventario
vacío inicial; nunca apuntarlo al laboratorio cotidiano con datos propios.

### Corte 9: caché de lectura en memoria

RopeReader conserva hasta cuatro inventarios y 32 MB de imágenes PNG con
expulsión LRU. Reconsultar un frame evita FFprobe/FFmpeg, pero verifica el
hash del archivo en cada lectura antes y después; no confía sólo en mtime.
No hay archivos de imagen persistidos ni copias de video. El inventario
se devuelve como copia para evitar mutaciones externas. El servicio HTTP
usa este lector para preparar y decodificar; guardado/rebind conservan su
verificación independiente. Tres tests reader/API/media pasaron en 2.05 s,
incluyendo conteos de probe/decode, presupuesto, copia e invalidación.
Pendientes: trabajos observables/cancelables y medición con clips corporales;
rehash completo sigue costando I/O y el primer decode continúa síncrono.

### Corte 10: extremos explícitos y velocidad proyectada

Cada frame visible admite `endpoints: {a?: {x,y}, b?: {x,y}}`; el editor
permite elegir curva/extremo a/extremo b y borrar etiquetas. Correspondencia
manual, no identidad inferida por posición. Frames absent/unidentifiable
rechazan extremos inventados. El reporte calcula velocidad vectorial y
módulo px/s sólo para la misma etiqueta en índices decodificados consecutivos;
frames saltados, etiquetas ausentes o estado inválido reinician soporte.
No constituye velocidad física ni propagación de tensión en la cuerda.
Campos vacíos se omiten para conservar compatibilidad de revisiones previas.
Seis tests de contratos/persistencia/API pasaron en 2.11 s; build web pasó.
Interacción de extremos en navegador aún pendiente; curva ya fue verificada.

### Corte 11: extremos verificados en Chrome

Recorrido HTTP real ampliado: extremos a en frames 0 y 1 se conservan al
guardar/recuperar; reporte produce ~160 px/s horizontal para desplazamiento
0.1 de ancho en 0.1 s, sin velocidad inicial. Frame 2 ilegible no inventa
extremos. La tolerancia refleja cuantización de clicks del navegador;
contratos numéricos ya prueban valores exactos por separado. Chrome pasó
1.6 s (suite 2.3 s), servidor propio detenido. Sólo video sintético;
correspondencias corporales humanas y velocidad física siguen pendientes.

### Corte 12: procesos de decodificación cancelables y salida acotada

FFprobe/FFmpeg usan captura POSIX con lectura no bloqueante y límite aplicado
mientras llegan bytes (16 MB inventario, 32 MB PNG), no después de acumular
salida ilimitada. Cancelación cooperativa y timeout de 60 s terminan y esperan
el proceso propio; stderr no expone rutas privadas. Cancelación previa no
lanza proceso. Cuatro tests proceso/media/reader/API pasaron en 2.26 s:
proceso confirmado vivo cancelado, timeout, overflow y extracción real.
No confundir esta base con cancelación web completa: faltan jobs observables,
conectar eventos desde UI/reader y hashing interrumpible. Hashes actuales se
calculan fuera del bucle cancelable; API aún síncrona.

### Corte 13: hash y lector cooperativamente cancelables

Hash SHA256 verifica cancelación antes y después de cada lectura de 1 MiB.
Probe, decodificación y lector cacheado propagan el evento hasta hashing y
subprocesos, incluyendo hits. Seis tests proceso/reader/media/API pasaron
en 2.38 s: digest correcto, cancelación entre lecturas y cancelación previa
sin probe/decode. El lock del lector y una lectura de disco ya iniciada no
se interrumpen instantáneamente; cancelación es cooperativa. Falta exponer
trabajos/estado/cancelación HTTP y conectarlos a la UI; no se declara esa
entrega realizada por haber completado la base del backend.

### Corte 14: trabajos efímeros observables por HTTP

POST `/api/research/r08/reads` recibe media_id y opcional frame_index+sha256.
GET `/reads/{id}` observa running/complete/cancelled/failed; POST
`/reads/{id}/cancel` solicita cancelación; GET `/reads/{id}/result` devuelve
inventario JSON o PNG sólo completo. Un trabajo activo por instancia, ocho
registros como máximo; el siguiente trabajo libera resultados PNG anteriores.
Resultados temporales no se restauran al reiniciar y no copian medios. Cierre
solicita cancelación y espera threads propios; errores no publican rutas.
Tres tests jobs/API pasaron: probe y decode reales, expiración, fallo,
exclusión de trabajos simultáneos, cancelación y cierre. Pendiente conectar
UI y probar cancelación HTTP real de proceso largo; rutas síncronas anteriores
permanecen disponibles durante la transición. Revisiones persistidas aparte.

### Corte 15: preparación observable en la web

Preparar anotación inicia `/reads`, muestra estado, consulta el mismo ID
hasta terminal y carga el resultado completo. Botón cancelar solicita al
trabajo propio; desmontar el panel también solicita cancelación, incluida
la respuesta de creación que llega después del desmontaje. No se aplica
un resultado posterior al desmontaje. Fuente/acciones bloqueadas durante
preparación; revisiones no cambian al cancelar. Compilación web pasó;
Chrome HTTP real del recorrido con preparación async pasó 2.3 s (suite 3 s).
Servidor propio detenido. Aún pendiente prueba del botón contra una lectura
larga real y migrar cada imagen del editor a jobs; imágenes/rebind/guardar
siguen usando sus rutas síncronas actuales. No declarar todo R08 cancelable.

### Corte 16: lectura de imágenes mediante jobs web

RopeEditor inicia un job de frame exacto, muestra estado y ofrece cancelar
imagen/reintentar. Índice bloqueado mientras inicia/lee; ninguna curva se
aplica sin imagen cargada. Cleanup solicita cancelación y descarta respuestas
tardías del trabajo viejo. PNG se obtiene sólo desde resultado completo;
no usa la ruta síncrona de frames. Chrome HTTP real del recorrido completo
pasó 2.4 s (suite 3.1 s), build pasó; servidor propio detenido. Faltan prueba
de cancelación con lectura larga real y concurrencia al cambiar fuente/
repreparar; rebind y guardado siguen síncronos. No declarar esa cobertura
por extrapolar el recorrido exitoso de imágenes pequeñas sintéticas.

### Corte 17: cancelación web con proceso vivo comprobado

Fixture opcional `--slow-probe-first` inicia un proceso Python real que
deliberadamente espera 30 s mediante el mismo capturador cancelable. Una
ruta exclusiva del fixture comprueba PID vivo antes/después; no existe en
producción. Chrome confirma proceso vivo, botón cancelar, job cancelled,
proceso terminado, borrador sin cambios, cero revisiones y reintento que
completa probe/imagen reales. Pasó 871 ms (suite 1.6 s); servidor detenido.
Esto verifica UI→API→evento→kill/wait, no rendimiento de FFmpeg sobre video
corporal largo ni cancelación bajo I/O físico bloqueado. El primer intento
falló porque el mount estático ocultaba la ruta de prueba; corregido sólo
en fixture, sin cambios de rutas productivas. Pendientes frame cancel y
concurrencia de fuentes; fuente privada/aceptación humana siguen aparte.

### Corte 18: cancelación web de imagen y reintento

Fixture `--slow-frame-first` permite comprobar un proceso real vivo antes
del botón cancelar imagen. Chrome verificó estado cancelled, PID terminado,
borrador byte por byte intacto, aplicar bloqueado y reintento con PNG real
que habilita aplicar sin crear revisiones. Pasó 1.2 s (suite 1.9 s), servidor
propio detenido. Misma limitación del corte 17: proceso lento sintético por
capturador real, no una medición de video corporal/disco bloqueado. Pendiente
concurrencia al cambiar fuente/repreparar y medición privada de rendimiento.

### Corte 19: medición local con fragmento corporal privado

Lectura real del fragmento existente de 60 s, sin copiar original/fragmento
ni guardar PNG. Este host, una corrida, 1800 frames 1920×1080: preparación
15.764 s; primer frame 1.221 s; frame 900 (30 s) 2.936 s; frame 1799
(59.966667 s) 4.618 s. Reconsultas cacheadas 900/1799: 0.692/0.693 s;
14,137,901 bytes en cache. Hash de fuente confirmado intacto al final.
No se publican ruta, hash, contenido corporal ni curvas/personas. Esto es
medición de lectura, no calidad de tracking ni aceptación humana. La primera
preparación aún es lenta; cache mejora repetición pero rehash completo tiene
coste. Próxima mejora debe conservar binding y límites, sin sustituir el hash
por confianza silenciosa en mtime. Concurrencia web sigue pendiente.

### Corte 20: control de hilos descartado por evidencia negativa

Se probó `-threads 1` en FFprobe y decoder/encoder FFmpeg sobre el mismo
fragmento local, sin copiarlo ni guardar imágenes. Seis tests reader/media/
jobs/API pasaron. Medición: probe 16.040 s (antes 15.764), frame 0 1.216 s,
900 8.569 s (antes 2.936), 1799 16.521 s (antes 4.618), hit 900 0.670 s.
Inventario 1800×1920×1080, tiempos y tamaños PNG coinciden con corrida previa;
fuente hash intacta. Ajuste revertido: no se publica un default más lento.
Una corrida por configuración no prueba causalidad general de scheduling,
pero no justifica adoptar el ajuste en este host. Siguiente optimización
requiere acceso más eficiente sin reemplazar índice/PTS real por seeks
aproximados ni inventar timestamps desde FPS. Concurrencia UI sigue pendiente.

### Corte 21: exclusión de acciones durante lectura de imagen

El editor comunica lectura activa al panel; fuente, preparación y guardado
se bloquean durante starting/running. Cancelar imagen vuelve a habilitar
acciones cuando el job termina, no cuando se envía la solicitud. Esto evita
colisiones con el contrato de un decode activo y guardados que compitan por
I/O. Mensaje visible explica cómo cambiar fuente durante lectura. Chrome
verificó bloqueo, cancelación de proceso vivo, desbloqueo y reintento (1.2 s,
suite 2 s); build pasó, servidor detenido. No hay cola de trabajos ni cambio
instantáneo con lectura activa: requiere cancelar primero. No altera audio.
Pendientes extracción asistida/benchmark anotado y mejora de acceso inicial.

### Corte 22: comparador inicial de curvas declaradas

API `/r08/compare` selecciona referencia/candidata por revisiones verificadas;
UI elige ambas y 2–64 muestras por tramo. Fuente/dimensiones deben coincidir,
igual índice requiere igual PTS. Inventario de referencia define filas;
candidata ausente/ilegible conserva fila sin score, nunca error cero. Reporta
cobertura y distancias simétrica media/Hausdorff **muestreadas**, en píxeles.
Cada tramo se remuestrea por longitud de arco sin unir oclusiones. Presupuesto
total 16 millones de distancias y bloques de 128 puntos limitan trabajo/memoria.
Resultado contiene ambas anotaciones y parámetros congelados para reproducir;
no hay ranking agregado ni comparación física automática. Curvas parciales
pueden tener distinto soporte visible y requieren interpretación explícita.
Tres tests numéricos/API y build pasaron; test adicional de presupuesto pasó.
Pendiente recorrido Chrome y persistir corrida/manifest; resultado actual
se muestra en web y se pierde al recargar, revisiones sí se conservan.

### Corte 23: corridas de comparación persistidas

Comparar revisiones ahora crea una corrida en research/r08-comparisons con
request/result/manifest, hashes, implementación y entorno Python/NumPy.
API/UI recuperan lista verificada y artefactos whitelist tras reiniciar;
resultado congela ambas anotaciones, no depende de IDs efímeros. Verificador
recalcula métricas con código/entorno registrados y rechaza alteración aun
si se reescribe checksum; cambios de versión impiden verificación exacta,
no se anuncian como fallos científicos. CLI `python -m
harmonic_weaver.lab.research.rope_compare_run --request <json> --output <nuevo>`.
Cuatro tests métrica/artifact/API y build pasaron, incluyendo repeat bytes,
no sobrescritura, manipulación numérica, entorno y restauración/whitelist.
Chrome del comparador pendiente. Hashes locales no son custodia firmada,
calidad de anotación humana ni rebind actual a video: requerirlo aparte.

### Corte 24: comparador persistido verificado en Chrome

Test HTTP real con dos revisiones sintéticas: referencia dos frames,
candidata uno desplazado 0.2 de altura sobre imagen 120 px. UI configura
16 muestras/tramo; reporte 24 px de Hausdorff muestreada, soporte 1/2 y
frame faltante sin score. Recargar recupera corrida y resultado byte idéntico;
descarga nativa manifest.json verificada. Pasó 950 ms (suite 1.9 s); servidor
propio detenido. Primer intento usaba selector de texto del label que
incluía opciones; corregido test a rol/nombre accesible. No validación humana
ni benchmark automático/real de cuerda: falta aportar predicciones/etiquetas
con incertidumbre y soporte comparable. Hash/código/entorno no custodias.

### Corte 25: núcleo de candidatos por color y ROI

`rope_mask.Settings` controla RGB objetivo, distancia euclídea RGB, ROI
normalizada, área mínima, cantidad y presupuesto de runs. Núcleo `propose`
produce regiones 4-conectadas en runs de píxeles y declara componentes
omitidos por filtros. No une huecos mediante morfología, no inventa curva,
identidad o extremos; candidates no son anotaciones aceptadas. Imagen RGB
uint8 hasta 4M píxeles, hasta 64 componentes/100k runs. Dos tests sintéticos
pasaron: segmentos separados, ROI/color, determinismo y límites/validación.
Pendiente conectar PNG exacto, API/UI/manifest y revisión humana; esta base
simple no se presenta como tracking de soga ni rendimiento de estado del arte.

### Corte 26: candidatos vinculados al frame exacto en API/UI

`POST /r08/mask` recibe media_id, read_id de frame completo y Settings.
Verifica hash/dimensiones actuales, decodifica PNG owned en RGB y reporta
candidatos con frame_index/PTS reales. Probe jobs no son imágenes aceptables;
resultados expirados fallan. UI edita todos los parámetros JSON y superpone
runs verdes separados; no modifica curvas/revisiones. Cambiar frame borra
máscara, calcular bloquea acciones de fuente, JSON inválido no deja busy
colgado. Cinco tests núcleo/jobs/API y build pasaron; test API adicional
verificó máscara real, binding índice/PTS y cero revisiones automáticas.
Pendientes Chrome y manifest persistido de propuestas; no tracking ni
etiqueta humana inferidos. Cálculo de máscara aún síncrono y acotado.

### Corte 27: candidatos web verificados sin aceptación implícita

Chrome HTTP real verificó JSON inválido recuperable, ROI de media imagen,
120 runs verdes del PNG exacto, ocultar y cambiar frame sin máscara vieja.
Borrador byte idéntico y cero revisiones; cálculo no acepta automáticamente
candidatos. Pasó 1.2 s (suite 2 s); servidor propio detenido. UI muestra
settings efectivos/frame/PTS/limits de máscara calculada por separado del
textarea editable, para no atribuir overlay a ajustes todavía no calculados.
Build pasó. Pendiente persistencia de propuestas/manifest y benchmark
corporal humano; este test no demuestra discriminación de soga frente a fondo.

### Corte 28: persistencia de propuestas sin imagen copiada

`rope_mask_run.run` recibe request de hash/dimensiones/frame/PTS/settings,
resuelve y recalcula contra fuente local exacta, revalida antes de publicar
manifest. Guarda sólo tres JSON request/result/manifest; no PNG/video ni ruta.
Código (incluido lector/decoder), entorno Python/NumPy/SciPy/OpenCV y hashes
registrados. `verify(folder)` comprueba integridad y bindings, **no recálculo**;
`verify(folder,path=video)` requiere código/entorno actuales y recalcula para
rechazar modificación numérica aun con checksum reescrito. Una propuesta
persistida sigue sin ser curva aceptada. Test real MP4 sintético pasó:
repeat bytes, sólo JSON, rebind, alteración numérica y cambio de fuente.
Pendiente servicio/API/UI y control semántico más exhaustivo sin fuente;
metadatos de versiones no prueban mismo build FFmpeg ni custodia firmada.

### Corte 29: guardar, recuperar y revalidar propuestas desde web

Servicio research/r08-masks, API lista/guardar/reverify/artifacts y editor:
guardar congela **settings efectivos**, no textarea modificado sin cálculo;
recalcula desde fuente actual. Propuestas de misma fuente muestran índice/PTS;
mostrar habilitado sólo en frame correspondiente y exige recomputación antes
de superponer. Descargas sólo tres JSON; no PNG/video. Inventario sobrevive
reinicio; integridad offline distinta de reverify con fuente. Dos tests
persistencia/API pasaron guardado, recálculo idéntico, whitelist y restauración;
TypeScript/Vite pasó tras agregar guard explícito de máscara nullable.
Pendiente Chrome de guardado/recuperación; datos/etiquetas humanas no inferidos.

### Corte 30: propuestas persistidas verificadas en Chrome

Chrome HTTP real pasó calcular ROI, modificar textarea sin recalcular,
guardar los settings **efectivos anteriores**, recargar, preparar misma
fuente y recuperar propuesta mediante recomputación. Overlay de 120 runs
restaurado, borrador byte idéntico/cero anotaciones, mostrar bloqueado en
frame distinto. Pasó 1.6 s (suite 2.4 s); servidor propio detenido. Verificar
requiere fuente disponible y código/entorno exactos; integridad offline no
sustituye esa prueba. Persistencia no acepta máscara como soga/ground truth.
Pendientes benchmark anotado humano, algoritmo de curva asistida/tracking,
incertidumbre y latencia/acceso a frames iniciales. Roadmap sigue abierto.

### Corte 31: verificación semántica offline de propuestas

Contrato de Result comprueba dimensiones/budget, inventario de componentes,
IDs únicos/ranking por área, runs enteros ordenados dentro de ROI, área
exacta por sumatoria y ausencia de solapamiento global. Semántica no sustituye
recomputación: una máscara geométricamente válida pero incorrecta sólo se
detecta contra video. Tres tests contratos/persistencia/API pasaron en 1.96 s,
incluyendo counts/área/ROI/orden/booleanos/solapamiento y tamper válido que
requiere recálculo. Código de contrato registrado para corridas nuevas;
verificación offline no exige código actual para recuperar artefactos
históricos, reverify sí. No aceptación humana ni conexión física inferidas.

### Corte 32: propuesta de camino guiada por seeds explícitos

`rope_path.Settings` selecciona componente persistido y puntos start/stop
normalizados, presupuestos de píxeles visitados y puntos de curva. BFS de
cuatro vecinos dentro de región produce camino mínimo candidato, sin snap,
closing ni unión de componentes. Seeds fuera, coincidentes, falta de camino
o presupuesto agotado producen soporte inválido y ninguna curva inventada.
API `/r08/path` exige propuesta guardada y reverify contra fuente antes de
calcular. Tres tests núcleo/API pasaron: línea conocida, ruptura, budgets,
determinismo y binding frame/PTS. No implica centerline real ni seguimiento;
un blob ancho/cruce puede producir camino arbitrario. Pendientes controles
web, persistencia/protocolo y benchmark humano; nada se acepta en borrador.

### Corte 33: curva guiada configurable y uso explícito en web

Editor controla componente/seeds/budgets vía JSON; botón explícito copia
extremos a/b como seeds. Cada propuesta guardada puede producir curva tras
reverify. Overlay magenta y parámetros efectivos, sin cambiar borrador;
`Usar curva candidata como tramo` modifica editor, luego `Aplicar frame`
actualiza borrador y guardar crea revisión. Seeds inválidos bloquean uso.
Chrome real verificó fuera de región, camino de 49 puntos y estos tres pasos
sin aceptación silenciosa (1.3 s; suite 2.2 s). Build pasó, servidor detenido.
Test automático no es aceptación humana de soga. Pendientes persistir
procedencia específica de curva asistida, tracker temporal/benchmark humano
y protocolos de incertidumbre/propagación; shortest path no prueba centerline.

### Corte 34: curva candidata persistida con máscara y seeds congelados

Proponer curva crea research/r08-paths con request/result/manifest: máscara
JSON congelada, hash del manifest de máscara, seeds/componente/budgets,
código/entorno y recálculo exacto. API lista/artefactos y descargas del
candidato en editor; no PNG/video copiados. API reverify máscara contra video
antes de congelarla. Verificador de curva recalcula **sobre máscara congelada**,
no vuelve a video ni firma custodia. Dos tests artifact/API pasaron repeat,
binding y modificación numérica aun con checksum reescrito; build pasó.
Pendientes recuperación web de curvas, vínculo de procedencia al tramo
incorporado, Chrome y benchmark/tracking humano. Camino sigue candidato.

### Corte 35: recuperar curvas con fuente/clock actuales

Inventario de curvas verificadas incluye hash/frame/PTS/soporte; editor
muestra misma fuente y sólo habilita recuperación en frame correspondiente.
POST `/paths/{id}/rebind` recalcula artefacto congelado, verifica hash/PTS
contra video actual y vuelve a verificar artefacto antes de devolver. Usar
tramo permanece explícito; no aplicar automáticamente al recuperar. Dos tests
artifact/API y build pasaron recuperación exacta. Pendiente Chrome de reload,
vínculo de procedencia dentro de la anotación y benchmark humano/tracker.

### Corte 36: procedencia del tramo asistido en anotación

Frame admite curve_sources por segmento: ID de curva, hash de su manifest y
relación exact/edited. Campos vacíos se omiten conservando revisiones previas.
Guardar por API verifica manifest/soporte/fuente/frame/PTS y geometría si
exact; un tramo modificado no puede declararse copia exacta. Edited conserva
vínculo sin afirmar misma geometría. Editor incorpora origen al usar camino,
marca edited al agregar puntos y borra vínculos al borrar curvas; aplicar
conserva origen sólo en estados visibles. Cinco tests contratos/run/API
pasaron exact/edited, rechazo de geometría/manifest falsos y persistencia;
build pasó. Pendiente Chrome de recuperación/procedencia y export portable
con dependencias; un vínculo local no implica aceptación científica humana.

### Corte 37: procedencia/edición/recuperación verificadas en Chrome

Recorrido real pasó candidato de 49 puntos, incorporación/aplicación con
origen exact y manifest hash, edición a 50 puntos marcada edited, guardado,
reload y recuperación de anotación con origen intacto. Recuperar curva
original verifica fuente y conserva 49 puntos, sin modificar tramo editado.
Chrome pasó 2.1 s (suite 3 s); servidor propio detenido. Prueba automática
sintética no es aceptación humana de geometría ni desempeño real de tracker.
Pendientes portable bundle con dependencias, tracking temporal, benchmark
humano e incertidumbre/propagación; roadmap continúa activo.

### Corte 38: soporte elegible distinto de referencia ilegible

Comparador conserva todas las filas de referencia, separando causa reference
sin curva, candidata faltante y candidata sin curva. Cobertura informa
referencias visibles elegibles, referencias sin curva, falta de candidata
sobre soporte elegible y fracción soportada sobre elegibles (None si cero).
UI muestra estos denominadores; referencias ilegibles no se presentan como
fallos de predicción. Cinco tests métrica/artifact/API y build pasaron, con
caso 1/2 elegibles más frame ilegible y caso sin referencia visible. No se
imputan errores cero ni se extrapola calidad fuera de soporte observable.

### Corte 39: comparador de extremos con etiquetas explícitas

Reportes con extremos añaden error firmado x/y y distancia px por etiqueta
a/b en mismo frame; cobertura visible, faltantes y extremos sólo candidata.
No se minimiza error permutando etiquetas ni se interpolan frames ausentes;
rows faltantes permanecen None. UI muestra cobertura de extremos; resultados
persistidos incluyen estas métricas. Seis tests métrica/artifact/API y build
pasaron swap de etiquetas (100 px, no cero), faltante y cero elegibles.
No valida identidad física ni propagación de tensión; tracking temporal y
benchmark humano continúan pendientes. Cambio de código obliga a distinguir
artefactos históricos de recálculos verificables bajo versión actual.

### Corte 40: historial recuperable frente a cambios de versión

Inventarios/read de comparaciones y curvas distinguen `recomputed` de
`historical_integrity_only`. Código/entorno distinto no oculta artefactos
íntegros: descargas preservan bytes, finitud/envelope/request/hashes se
verifican; no se afirma recálculo actual. Código/entorno actuales requieren
recomputación y corrupción sigue rechazada. UI etiqueta históricos; curvas
históricas descargables no recuperables/incorporables como verificadas
actuales, API interna mantiene verify estricto. Cinco tests historia/artifact/
API pasaron cambios de entorno, bytes intactos, rechazo de corrupción y
adopción histórica bloqueada; build pasó. Pendiente Chrome de esta etiqueta,
migración explícita/re-corrida y portable bundle de dependencias. No custodia
ni resultados científicos falsificados; originales no se reescriben.

### Corte 41: recuperación histórica verificada en Chrome

Fixture HTTP aislado crea comparación y curva sintéticas y simula entorno
anterior sólo en sus manifests locales. Chrome real verificó etiquetas de
integridad histórica, apertura de comparación, descargas nativas de ambos
manifests, bytes idénticos antes/después, persistencia tras reload y curva
histórica no incorporable: botón deshabilitado y API rebind rechazada con 422.
El borrador no cambió. Una prueba pasó (975 ms; suite 1.9 s), sin dispositivos
ni datos corporales; servidor propio detenido. Esto verifica el recorrido web,
no desempeño del tracker ni aceptación humana. Migración explícita/re-corrida,
bundle portable con dependencias, seguimiento temporal e incertidumbre siguen
pendientes; la recuperación histórica no convierte resultados antiguos en
evidencia recalculada bajo código actual.

### Corte 42: núcleo temporal causal con seeds explícitos

`rope_flow.RopeFlow` implementa candidatos Lucas–Kanade piramidales sobre
imágenes grayscale decodificadas. Configuración validada: ventana, niveles,
iteraciones, epsilon, mínimo eigenvalor, error forward/backward, desplazamiento,
gap máximo y presupuesto de puntos. Cada índice corresponde al seed declarado;
no asigna etiquetas físicas a/b. Flujo ida/vuelta, finitud, bounds y umbrales
determinan soporte. Puntos rechazados no reaparecen automáticamente. Saltos de
índice, timestamps no crecientes, gaps excesivos o dimensiones distintas
resetean soporte; nuevas seeds deben ser explícitas. La imagen anterior se
copia en RAM para evitar mutación del caller; no persiste imágenes.

Diez tests núcleo/anotación pasaron (0.32 s): desplazamiento sintético conocido,
repetición exacta en este entorno, pérdida de textura, umbral de desplazamiento,
cuatro tipos de reset, validación sin mutar estado y ownership de buffer.
Una primera prueba con textura de ruido blanco produjo sesgo subpixel mayor
que 0.1 px; fixture de traslación usa textura suavizada con GaussianBlur.
No se presenta este fixture como benchmark de videos reales ni evidencia de
precisión general. Coordenadas normalizadas escalan por width/height igual que
anotaciones; seed en borde máximo se limita al último píxel explícitamente.

**No está conectado a la web todavía.** Próxima entrega: secuencia de frames
exactos y clock/sha verificados, corrida congelada con código/OpenCV/config,
controles web y overlays candidatos sin aceptación automática. Luego benchmark
contra anotaciones humanas en soporte común, incertidumbre/oclusiones/cruces.
El flujo no segmenta soga, no prueba centerline, identidad de material ni
propagación de tensión. No se modifican síntesis, defaults ni presets.

### Corte 43: corrida temporal ligada al video y congelada

`rope_flow_run` conecta el núcleo con RopeReader: hash y dimensiones actuales,
slice de 2–120 índices consecutivos y timestamps **exactos** del probe, seeds
iniciales explícitos y Settings congelados. Decodifica PNG exacto sólo en RAM,
convierte a grayscale y aplica el mismo núcleo causal. Respeta cancelación en
hash/decodificación y entre pasos, no reacquiere puntos perdidos. Cada imagen
está limitada a 4M píxeles; la corrida guarda request/result/manifest JSON en
directorio nuevo, código, Python/NumPy/OpenCV y hashes; nunca source path ni
copias de video/imágenes. Rehash antes de manifest completo.

CLI (request debe contener clock/hash/dimensiones del probe):

```sh
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.rope_flow_run \
  --request /ruta/local/request.json --video /ruta/local/video.mp4 \
  --output /ruta/local/corrida-nueva
```

Verify offline comprueba envelope, finitud, request, clock/settings por frame e
inventario/hash; **no** comprueba numéricamente candidatos. Verify con video
exige código/entorno actual y recálculo exacto. Diez tests núcleo/corrida pasaron:
repetición byte idéntica sobre MP4 sintético real, índices/PTS, recálculo,
alteración numérica aun con checksum reescrito, clock alterado, cambio de fuente,
cancelación previa/tras decode sin publicación y budgets/gaps. Metadatos de
versión no garantizan mismo build FFmpeg/OpenCV ni custodia firmada.

Pendientes inmediatos: jobs API cancelables, UI de seeds/rango/Settings y
overlays, portable configuración y benchmark humano en soporte común. Decodificar
cada cuadro mediante lector exacto rehashes/relee el video; esta primera
implementación acotada no promete rendimiento realtime ni escala de 60 s.
No identidad de material, segmentación completa ni propagación física inferidas.

### Corte 44: jobs temporales cancelables y API de artefactos

RopeFlowService permite un job activo por instancia, ocho estados efímeros y
corridas JSON persistidas verificadas. POST `/api/research/r08/flow` recibe
media_id autorizado de biblioteca y Request; GET del mismo recurso lista
corridas completas, GET `/{id}` consulta estado, POST `/{id}/cancel` cancela
sólo ese job y GET `/{id}/artifacts/{name}` descarga request/result/manifest.
No ruta de video arbitraria. Inventario marca `integrity_only`: descargar o
reiniciar servicio no equivale a recalcular optical flow. Fallos devuelven
diagnóstico genérico sin paths privados. Cancelación también comprueba la
ventana posterior a publicación antes de marcar complete; archivos de ese job
se eliminan si fue cancelado/falló. Jobs parciales nunca aparecen como completos.
Cierre cancela y espera los threads propios, como lector existente.

Siete tests servicio/API/corrida/API R08 pasaron: ejecución real desde biblioteca,
artefactos y recuperación tras reinicio, recursos no autorizados y clock inválido,
cancelación de subproceso Python confirmado vivo y comprobación de terminación,
cancelación ajena rechazada, limpieza de parciales, cancelación posterior a
publicación y error sin revelar ruta. Casos de subproceso/publicación usan workers
de test; el caso API ejecuta decoder/flujo reales sobre video sintético. Sin
dispositivos, cuerpos ni audio. UI temporal, controles/config portable y
overlays/benchmark humano siguen pendientes; no se promete realtime.

### Corte 45: exploración temporal configurable en web

Editor integra RopeFlowPanel: JSON portable `{frames,settings}` con todos los
controles del núcleo, JSON separado de seeds, copia explícita de extremos
actuales, inicio desde cuadro actual, polling/cancelación y recuperación de
corridas/descargas. Cambiar cuadro/fuente borra seeds; recuperar configuración
recupera parámetros/duración y no observaciones ni calibración. Desmontar panel
solicita cancelar su job propio. Dibujo separado muestra sólo puntos con
soporte del cuadro actual, cuando imagen está lista y hash coincide; no dibuja
líneas ni une gaps. Resultado completo conserva causas y config efectivas.
Lectura recuperada dice integridad, no recálculo de fuente; no adopta anotaciones.

Chrome real pasó corrida de tres cuadros (seeded/reset/reset), dibujo del seed,
borrador intacto, reload/recuperación y config sin seeds (1.5 s; suite 2.3 s).
TypeScript/Vite build pasó. Fixture HTTP ejecutó decoder/flow reales sobre
MP4 sintético, sin dispositivos ni cuerpos; servidor detenido. No aceptación
humana ni desempeño de soga real. Pendientes overlay sobre imagen, recálculo
explícito desde UI, presets nombrados/export, recorrido cancelación web y fallos
de red, benchmark humano y rendimiento de decoder secuencial. JSON portable
puede copiarse/pegarse hoy; no equivale a biblioteca de presets nombrados.
Controles cotidianos/audio/afinación permanecen intactos.

### Corte 46: candidatos temporales sobre el cuadro exacto

Editor superpone anillos azules/índices f sobre la imagen decodificada, sin
polylines ni edición automática. Sólo muestra puntos presentes con matching
hash, dimensiones, índice y timestamp exacto, y ready de imagen actual. El
dibujo separado permanece como vista auxiliar. Cambiar cuadro borra seeds;
un frame reset/no soportado no muestra puntos ni arrastra los del anterior.
Recuperar resultado histórico conserva aviso de integridad, no de recálculo.

Chrome real verificó seed x=.5 en overlay, paso a frame reset sin overlay,
seeds borrados, regreso al seed, borrador intacto, reload y recuperación de
config sin seeds. Una prueba pasó (2 s; suite 2.9 s); build pasó, fixture HTTP
sintético con decoder/flow real, servidor propio detenido. No benchmark humano
ni identificación de soga/material. Pendientes presets nombrados/export,
recálculo UI, cancelación/fallos de red, decoder secuencial y comparación sobre
anotaciones humanas en soporte común; no cierre científico de R08.

### Corte 47: retomar consulta tras interrupción de red

Panel conserva ID conocido del job si falla polling o lectura de resultado/
inventario. Estado `connection_lost` no equivale a fracaso de cálculo ni
terminación del worker. Otro inicio permanece bloqueado; botón Retomar consulta
consulta ese mismo ID y recupera resultado cuando completa. Cancelar permanece
disponible y, sin observador activo, retoma consulta del estado devuelto. Un solo
observador por panel evita polling duplicado; desmontaje conserva cancelación.

Chrome real abortó deliberadamente un GET de estado de job ya iniciado y
verificó ID preservado, otro inicio deshabilitado, cancelación disponible,
retomar mismo ID hasta complete y exactamente un POST de inicio. Conserva
overlay/reset, borrador intacto y reload/config del recorrido anterior. Una
prueba pasó (1.9 s; suite 2.8 s); build pasó, servidor detenido.

Pendiente explícito: respuesta perdida del **POST inicial** antes de conocer
ID; requiere clave idempotente/recuperación de inicio, no resuelta por este
cambio. Cancelación web de worker vivo y pérdidas de artefacto/inventario aún
requieren casos propios. Presets nombrados, recálculo UI, decoder secuencial
y benchmark humano continúan pendientes; audio/defaults intactos.

### Corte 48: inicio idempotente en API con recibo persistido

POST flow admite idempotency_key opcional de 32 hex. Antes de iniciar thread
persiste research/r08-flow-starts/KEY.json con ID y SHA256 del request canónico,
sin path, seeds ni imágenes en recibo. Bajo el owner único del servicio, misma
clave/request devuelve mismo job; distinto request rechaza. Recibo permanece
tras eviction/reinicio: completa recuperable vuelve al mismo ID, corrida
cancelada/incompleta sin artifacts rechaza reintento y nunca relanza.
No coordinación multi-proceso ni garbage collection de recibos implementadas.

Tres tests servicio/API pasaron: reutilización activa, request distinto,
recuperación completa tras restart, cancelada en owner actual y rechazo tras
restart sin nuevo worker. La UI aún no envía clave ni conserva request de POST
sin respuesta: integración/reintento browser pendientes, no declarar ese caso
resuelto end-to-end. Audio/presets intactos; roadmap/benchmark siguen abiertos.

### Corte 49: reintento web del inicio sin respuesta

UI crea clave aleatoria por intento y conserva request congelado en RAM antes
del POST. Si respuesta no llega, estado start_unknown bloquea nuevo inicio y
edición de config/seeds; Reintentar mismo inicio reenvía exactamente clave y
request original, aunque se haya movido el frame. ID recibido pasa al observer
existente. API común conserva status HTTP en Error: rechazo explícito 4xx libera
intento para corregir parámetros; errores de transporte/5xx mantienen request.
No cambio de mensajes de error ni comportamiento de otros paneles.

Chrome real interceptó POST, dejó que servidor lo aceptara y abortó respuesta
al navegador; reintento produjo mismo ID, dos POST de bytes JSON equivalentes,
una sola corrida y borrador intacto. Validación de seeds vacíos desbloqueó
edición. Una prueba pasó (1.3 s; suite 2.2 s); build pasó, fixture sintético
con decoder/flow real, servidor detenido. Pendiente persistir/recuperar intento
desconocido al cerrar/recargar panel (request en RAM), cancelación web viva,
presets/recálculo/decoder secuencial y benchmark humano. Recibos del servidor
evitan relanzar una clave conocida; no recuperan por sí solos una clave perdida
por el navegador. Sin cambios de audio/defaults ni datos privados publicados.

### Corte 50: intento pendiente recuperable tras reload de pestaña

Antes de enviar POST, UI guarda recibo v1 (request+clave) en sessionStorage,
acotado a 1 MB y separado por media_id/hash. Al recibir ID actualiza recibo;
al completar/cancelar/fallar confirmado o rechazar 4xx lo elimina. Remount de
esa fuente valida envelope/fuente/clave/ID y ofrece retomar explícitamente
start_unknown o consulta de ID conocido, sin enviar trabajo automáticamente.
Seeds del editor no se restauran: permanecen sólo en request congelado privado,
no dentro de configuración portable/preset. Recibo local de pestaña no copia
medios ni sale a GitHub; sessionStorage no garantiza recuperación tras cerrar
pestaña/browser y no coordina otras pestañas. Preservar almacenamiento local
es requisito para iniciar; fallos no se silencian lanzando sin recibo.

Chrome pasó respuesta POST perdida tras aceptación, reload/preparación de misma
fuente sin POST automático, reintento exacto/mismo ID, una sola corrida, recibo
eliminado al completar, seeds vacíos y borrador intacto; rechazo seeds vacíos
permite editar. Una prueba pasó (1.4 s; suite 2.2 s); build pasó y servidor
detenido. Recuperación de ID conocido tiene implementación pero requiere caso
browser propio; cancelación viva, presets/recálculo, rendimiento y benchmark
humano siguen pendientes. No cambios de audio/defaults ni aceptación humana.

### Corte 51: recuperación de ID conocido y cancelación viva en Chrome

Dos recorridos browser HTTP verificaron casos pendientes. Primero, servidor
completó cálculo y devolución del artifact fue abortada; UI persistió ID,
reload recuperó consulta explícita, mismo resultado/overlay y recibo eliminado,
sin segundo POST ni mutar anotación (1.6 s; suite 2.4 s). Segundo, fixture
slow-flow-first ejecutó subproceso Python de 30 s por capture cancelable;
endpoint exclusivo de test confirmó PID vivo. Botón cancelar produjo estado
cancelled, PID muerto, inventario vacío, recibo eliminado, sin overlay ni cambio
de borrador. Nuevo inicio explícito ejecutó decoder/flow reales y completó
una corrida (1.4 s; suite 2.2 s). Ambos servidores propios detenidos.

El proceso lento es inyección de test del worker, no medición de cancelación
durante optimización OpenCV ni benchmark de soga. Segundo cálculo y caso de
recuperación sí usan MP4 sintético/decoder/flow reales. Pendientes recálculo UI,
presets nombrados, decoder secuencial, benchmark humano/uncertainty y otros
fallos de almacenamiento/red/reinicio durante cálculo. Sin cambios de código
de producción en este corte; no repetir build anterior como evidencia nueva.

### Corte 52: contrato estructural de soporte temporal

Offline verify valida ahora cada frame/row mediante contrato estricto:
estado/causa/presencia de punto, diagnósticos no negativos y umbrales de
candidatos, IDs únicos y continuidad sin reactivación, seeds sólo iniciales
con posición declarada, resets exactamente cuando source-time supera gap y
bounds del píxel decodificado (tolerancia normalizada 1e-7 por float32).
Campos desconocidos/bools donde corresponde int/estados incoherentes se
rechazan; inventario/clock/config siguen ligados al request. Archivo de
contrato incluido en código registrado para nuevas corridas.

Siete tests contrato/corrida/servicio/API pasaron: nueve mutaciones
estructurales, decode real, repeat/recompute, idempotencia/cancelación/restart.
Test de tamper numérico modifica diagnóstico dentro del contrato: integridad
puede pasar con checksum reescrito, recálculo contra video debe rechazar.
Así no se confunde consistencia estructural con exactitud óptica ni custodia.
No nuevos tests browser/build en este corte backend; referencias previas no
son verificación de este head. Presets/recálculo UI/decoder secuencial/benchmark
humano y otras líneas del roadmap siguen pendientes. Audio/defaults intactos.

### Corte 53: presets temporales nombrados y portables

Contrato Preset v1 contiene sólo name/config; config sólo frames y Settings.
Seeds, fuente, request y calibración se rechazan por extra-forbid. Servicio
persiste entradas UUID nuevas en research/r08-flow-presets; GET/POST
`/api/research/r08/flow-presets` y GET `/{id}` export JSON portable sin ID local.
Lectura requiere archivo regular no symlink <=64 KiB. Importar añade entrada,
no reemplaza preset anterior ni acepta automáticamente observaciones.

UI: nombre, guardar config actual, aplicar preset explícitamente, descarga
nativa y file input para importar JSON <=64 KiB. Aplicar cambia sólo parámetros;
seeds presentes del cuadro actual permanecen, no provienen del archivo.
Presets siguen disponibles tras restart/reload y no cambian instrumento/audio.

Dos tests API pasaron (1.39 s): contrato rechaza observaciones en ambos niveles,
export/import crea ID nuevo y restart conserva bytes. Chrome real pasó guardar,
descargar/importar el archivo descargado, aplicar parámetros con seeds/borrador
intactos y reload con presets persistidos/seeds vacíos (1.4 s; suite 2.2 s).
TypeScript/Vite build pasó; fixture sintético, servidor detenido. Pendientes
recálculo UI, decoder secuencial/rendimiento y benchmark humano de seguimiento;
presets no convierten parámetros en evidencia de calidad física.

### Corte 54: recálculo explícito contra fuente desde web

POST `/api/research/r08/flow/{id}/reverify` recibe media_id autorizado y crea
job owned efímero de verificación. GET `/flow-verifications/{id}` consulta y
POST `/{id}/cancel` cancela; uno activo, ocho estados, cierre cancela/espera.
Verifica artifacts originales, código/entorno actual y recalcula con video por
el mismo núcleo/clock/config. Coincidencia exacta marca `recomputed`, ligada
a ID original y hash de su manifest comprobado antes/después. Cancelación o
fallo no publican esa marca; originales nunca se reescriben. Estado no es
custodia firmada ni benchmark de precisión física.

Web ofrece recalcular/cancelar/retomar polling por corrida; evidencia desplegable
indica coincidencia **en ese recálculo** y carácter efímero. Inventario continúa
marcado por integridad; reload no presenta prueba anterior como estado actual.
Dos tests servicio/API pasaron (1.36 s): cálculo real exacto, fuente alterada
rechazada, archivos intactos y subproceso de verificación vivo detenido en test.
Chrome con HTTP/MP4 reales sintéticos pasó recálculo, marca sólo tras completar,
bytes originales idénticos, borrador intacto y reload sin marca (1.8 s; suite
2.6 s); build pasó y servidor detenido.

Pendientes evidencia de verificación persistida/exportable, casos browser de
cancelación/red específica de recálculo e inicio perdido (verificación es sólo
lectura), decoder secuencial/rendimiento y benchmark humano. Cambios de código/
entorno en históricos se rechazan: recálculo actual no migra resultados viejos
ni falsea verificación. Audio/defaults y demás roadmap intactos.

### Corte 55: evidencia de recálculo persistida y descargable

Coincidencias completas guardan directorio UUID nuevo en
research/r08-flow-verifications con report/manifest JSON: ID original, hash de
su manifest, UTC de comprobación, código/entorno del cálculo y código del
productor de evidencia. Canceladas/fallidas no reciben marca recomputed.
Lectura exige archivos regulares <=64 KiB, hashes y contrato estricto de
reporte con timestamp UTC/IDs/código válidos; devuelve registro histórico,
no recalcula ni prueba exactitud/custodia por hashes.

GET `/api/research/r08/flow-verifications?source_run_id=...` lista evidencia
histórica por corrida; GET `/{id}/artifacts/{name}` descarga report/manifest.
Report por ID puede recuperarse tras restart. Web lista historial y descargas,
separado del estado del recálculo actual; reload conserva registro histórico
sin marca de comprobación actual de fuente. Originales intactos.

Dos tests backend pasaron (1.37 s): persistencia/restart, source alterada,
cancelación viva y rechazo de UTC malformado con checksum reescrito. Chrome
pasó recálculo real sintético, descarga nativa de report, bytes originales,
borrador/reload e historial sin marca actual (2 s; suite 2.7 s); build pasó y
servidores detenidos. Un checksum reescrito con reporte semánticamente válido
no es detectable como falsificación: no hay firma/custodia externa. Pendientes
browser cancel/red específicos de recálculo, decoder secuencial/rendimiento,
benchmark humano y demás líneas abiertas. Audio/defaults intactos.

### Corte 56: decoder secuencial exacto y medición local

`rope_sequence.sequence` lee 1–120 cuadros consecutivos con un FFmpeg owned,
select por índices y vsync 0, PNG en pipe; no seek aproximado ni resampling.
Streaming valida signature/IHDR/IEND/CRC, count exacto, 32 MB/frame, chunks
<=1 MB y deadline 60 s del proceso/consumo. Buffer no acumula la secuencia;
caller puede acumular si lo decide. Cierre temprano del generador mata/espera
su proceso; cancelación antes/durante decode hace lo mismo. Fuente regular,
hash/inventario, 4M píxeles y rehash al agotar generador. Consumir sólo un
prefijo no equivale a comprobar integridad final; cerrar explícitamente en
salidas tempranas. Sin cambios al lector/flow existentes en este corte.

Cuatro tests reales/sintéticos pasaron: igualdad pixel-array con lector
individual para índices no cero, fuente modificada, count/CRC/truncación,
presupuesto, cancelación/close con PID confirmado vivo, rangos/symlink,
pre-cancel sin spawn y timeout con proceso detenido.

Medición privada sobre fragmento local ya autorizado, sólo agregados públicos:
probe 15.747 s; cinco cuadros consecutivos en ventana intermedia, individual
11.123 s, secuencia 2.699 s. Todos los píxeles iguales, fuente SHA intacta,
0 archivos escritos/0 imágenes o videos copiados. Una corrida en este host,
sin controlar cache del sistema, no benchmark general ni calidad de pose/soga
ni promesa realtime. Coste de probe aparte; ventana corta incluye preroll.

**Todavía no integrado en corridas/UI.** Próximo paso: modalidad de decoder
configurable/congelada y presets, pruebas de paridad de features/manifest y
cancelación integrada. No cambiar default hasta evidenciar esa integración.
Benchmark humano, cruces/uncertainty y resto de roadmap pendientes.

### Corte 57: decoder configurable e integrado a flow y presets

Request y config portable admiten decoder individual_png (default existente) o
sequential_png. Default se omite en serialización conservando shape de requests
y presets históricos; secuencial queda explícito en request/result/preset.
Flow consume stream PNG exacto por mismo núcleo grayscale/clock/Settings; finally
cierra generador ante cancelación/fallo de tracking y fuente se comprueba al
agotar stream y después del cálculo. Código de sequence incluido en manifest.
Selector web y JSON controlan modalidad; recuperar configuración y export/import
de preset conservan decoder sin seeds/fuente/calibración. No auto-migración de
artifacts de otra versión ni cambio del default/audio.

Once tests backend pasaron (5.02 s): pixel/feature parity, repeat secuencial,
verificación fuente, contratos/cancel/close/timeout e integración/API anteriores.
Preset con modalidad secuencial pasó prueba API propia (0.78 s). Chrome pasó
dos recorridos (suite 4.2 s): seq real sintético, interrupción de polling/mismo
job, recuperación de configuración, overlay/reset y preset descargado/importado
con decoder, seeds/borrador intactos. Build pasó; servidor propio detenido.
Cancelación de tracking prueba cierre del stream con generador instrumentado;
terminación de decoder real pertenece a tests de sequence, no confundir ambos.

Mejora de tiempos anterior no se generaliza a toda corrida ni realtime. Pendientes
medición integrada sobre segmentos locales, datos VFR y modalidades difíciles,
benchmark humano contra anotaciones, incertidumbre/cruces y demás roadmap.

### Corte 58: VFR y medición integrada local

Tres tests VFR pasaron (3.86 s): FFV1/Matroska, H264/MP4 con mux default y
H264/MP4 sin edit list. Fixtures presentan intervalos .1/.3 s; un caso tiene
origen PTS .2 s, normalizado por probe sin reconstruir clock a fps nominal.
Pixel arrays entre individual/secuencia, frames de flujo y PTS coinciden
exactamente; gap .3 s corta soporte y siguiente frame no reactiva seeds.
Corrida congelada/recompute secuencial coincide.

El primer fixture MP4 esperaba seis cuadros pero probe reportó cinco.
Inspección independiente con FFmpeg rawvideo confirmó cinco decodificados,
aunque metadata nb_frames declara seis. Sin edit list el fixture presenta
seis, origen distinto; ambos casos se conservan. No cambiamos decoder para
inventar cuadro/timestamp ausente ni inferimos comportamiento general de MP4
a partir de este caso. Validación utiliza inventario real decodificado.

Medición integrada privada autorizada, mismo fragmento/ventana de cinco cuadros:
RopeReader.probe 16.146 s separado; calculate individual 15.515 s vs secuencial
3.830 s, frames/features completos idénticos. Reader/metadata compartidos,
individual sin cache inicial de imágenes, secuencial no usa esa cache; cache
del sistema no controlada. Seeds diagnósticos arbitrarios, no etiqueta de soga,
mano/persona ni calidad de tracking. Sin persistir resultados/imágenes/video.
Sólo tiempos/paridad agregados publicados. Una corrida de este equipo no es
promesa realtime ni experimento científico de cuerpo/HIT. No cambios de
producción/defaults en este corte; benchmark humano y roadmap siguen abiertos.

### Corte 59: núcleo de benchmark de extremos con soporte explícito

`rope_flow_benchmark.evaluate` recibe Annotation manual y snapshot de flow
validado, más mapping explícito etiqueta a/b → índice de seed (distintos y
existentes). Exige mismo hash/dimensiones y clock compartido. No asigna identidad
por proximidad ni optimiza swaps. Evalúa extremos seleccionados anotados dentro
de ventana; excluye cuadro inicial porque seeds son input, no estimación.
Referencia fuera de ventana/etiqueta no seleccionada se conserva como exclusión,
no fallo de tracker. Candidatos perdidos permanecen unsupported con error None,
incluida pérdida anterior sin reactivación; causa del frame se conserva si existe.

Errores x/y/distancia en px; mean/max sólo sobre soporte válido y coverage sobre
elegibles explícita (None si cero), sin imputar ceros. Snapshot/request normaliza
contrato pero no verifica archivo fuente ni origen de los artefactos por sí solo.
Flow observa imagen actual, por lo que no son métricas de forecasting ni pruebas
de identidad física/propagación. Referencia humana requiere calidad independiente.

Tres tests pasaron (0.27 s): errores conocidos ±10 px, media 7.5 px sobre cuatro
de ocho elegibles, cuadro input y exterior excluidos, faltantes/no revival,
swap explícito con 70 px (no optimizado a cero), etiquetas seleccionadas, cero
soporte, source/clock/mapping/bools/snapshot inválidos y repetición exacta.
Sin datos corporales ni aceptación humana; audio/defaults intactos.

**Núcleo todavía no integrado a persistencia/API/UI.** Próximo: corrida congelada
con vínculos a manifests de revisión/flow, comparación web/mapping editables y
descargas, luego etiquetas humanas y controles sobre segmentos reales. Evaluar
endpoints no valida curva completa/centerline, cruces ni incertidumbre física.

### Corte 60 — persistencia del benchmark temporal

`rope_flow_benchmark_run.py` congela referencia, snapshot de flujo y mapeo explícito,
con IDs y hashes de manifests declarados por el llamador. Escribe únicamente
request/result/manifest JSON en un directorio nuevo; nunca reemplaza una corrida.
Verifica inventario, binding de entradas, números finitos, archivos regulares y
estabilidad de hashes durante lectura. Con código/entorno actuales exige igualdad
contra recomputación; versiones distintas se presentan como
`historical_integrity_only`, sin afirmar verificación numérica actual.

Evidencia: siete tests del cálculo/persistencia pasaron (0,39 s), incluyendo
alteración de métrica con hash reescrito, referencia congelada, binding histórico,
procedencia inválida, symlink y prohibición de sobrescritura.

Límite: este runner no autentica los artefactos originales ni reejecuta tracking
contra video. Pendiente resolver ambas fuentes desde servicios verificados,
comprobar sus hashes antes/después y exponer selección/mapeo/cobertura en la web.
No se procesaron ni publicaron medios privados; no cambió síntesis ni defaults.

### Corte 61 — resolución de originales y API del benchmark

`RopeFlowBenchmarkService` recibe sólo IDs de revisión/flujo y mapeo a/b→índice.
Obtiene los snapshots mediante los propietarios que verifican los artefactos,
congela sus hashes de manifest y los vuelve a comprobar antes/después de guardar.
Un cambio descarta únicamente la nueva corrida; originales quedan intactos.
POST/GET `/api/research/r08/flow-benchmarks` y GET
`/{id}/artifacts/{request,result,manifest}.json` permiten ejecutar, listar y
exportar. Reabrir una corrida no exige que sigan presentes los originales:
recomputa la métrica sobre las entradas congeladas, con lectura histórica explícita.

Evidencia: nueve tests cálculo/persistencia/servicio/HTTP pasaron (2,23 s), con
video sintético y tracking real, originales sin cambios, procedencia ligada,
fallo ante modificación durante publicación, descarga y restauración después de
reinicio; HTTP rechaza booleanos como índices, campos extra e IDs inválidos.

La resolución verifica artefactos locales al crear; no es firma/custodia ni
revalidación del tracking contra el video actual. La referencia sigue siendo
manual y no aceptada científicamente por esta prueba. Pendiente UI para elegir
revisión y flujo, declarar el mapeo y mostrar error junto con cobertura/exclusiones.

### Corte 62 — benchmark temporal en la web

El panel R08 permite seleccionar revisión/corrida, actualizar inventario y declarar
índices a/b (vacío excluye; duplicados bloqueados). No selecciona ni optimiza el
mapeo automáticamente. Muestra soporte/elegibles, candidatos faltantes, exclusiones
por ventana/semillas/etiqueta y media/máximo sobre soporte; nulos dicen sin soporte.
Incluye JSON congelado, inventario histórico y descarga de los tres artefactos.
Cambiar corrida limpia el mapeo; evaluar no modifica el borrador manual ni síntesis.

Validación: build TypeScript/Vite pasó; Chrome con API y video sintético reales
pasó selección explícita, bloqueo de mapeo vacío/duplicado, cobertura/exclusión,
descarga nativa y recuperación tras reload sin crear otra corrida (1,7 s).
Servidor aislado apagado. No hubo revisión de calidad manual ni aceptación humana.
Pendiente recuperación de respuesta POST perdida/idempotencia del benchmark y
selección asistida más legible con previews; no confundir métricas de imágenes
observadas con forecasting, profundidad o identidad física.

### Corte 63 — recuperar respuesta perdida del benchmark

Clave opcional estricta de idempotencia, recibo persistido antes del cálculo y
selección ligada por hash: mismo intento recupera la corrida congelada; otra
selección con esa clave se rechaza. Una publicación interrumpida no se reinicia
silenciosamente con el mismo recibo. El recibo no contiene paths, video ni seeds.
La web conserva el cuerpo pendiente en sessionStorage antes del POST; ante
respuesta perdida bloquea un nuevo intento y ofrece recuperación explícita.
Recargar muestra el intento sin enviarlo automáticamente; error HTTP 4xx libera
el pendiente. Cierre de pestaña no garantiza retención. Recibos sin GC, servicio
con un solo propietario; múltiples procesos no están coordinados.

Evidencia: nueve tests backend/HTTP pasaron (2,16 s), incluidos recuperación tras
reinicio, rechazo de clave con selección distinta y publicación fallida sin
rearranque. Build pasó. Chrome real (2,4 s) abortó la respuesta después de aceptar
el POST, recargó, recuperó con cuerpo/clave idénticos y comprobó una sola corrida,
además de cobertura, descarga y reapertura. Servidor aislado apagado.
