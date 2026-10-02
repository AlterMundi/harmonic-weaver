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
