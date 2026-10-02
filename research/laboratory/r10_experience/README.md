# R10 · Experiencia de practicantes y observadores

Issue #24; rama feat/r10-experience-protocol sobre PR #76. No cambia el
instrumento cotidiano ni hace obligatoria una evaluación para explorar.

## Corte 1 · Plan declarado y respuestas tipadas

experience_protocol.py y API /research/r10/preview generan calendario determinista
para estímulos/ventanas declarados, rol practitioner u observer y participant_slot
local (no nombre personal requerido). Configuration ofrece condiciones video_only,
sound_only, audiovisual y desynchronized opcional; repeticiones, preview_gain,
offset de desacoplamiento, escala y preguntas editables. Intervalos <=120s,
condiciones/estímulos/preguntas únicos, límites y entradas finitas/estrictas.

Order_index elige una permutación de condiciones; cada repetición avanza una
posición de ciclo. Todas las permutaciones balancean posiciones y transiciones
sólo al completar el ciclo (3 condiciones=6; 4=24). No se afirma balance para
reclutamiento incompleto. Orden de estímulos permanece explícito, sin optimización
por resultado. Cada trial tiene ID, condición, flags audio/video, ventana y offset
nominal. No reproduce ni prueba exposición; references no resuelve medios.

validate-response exige cada pregunta configurada: null sin respuesta, números
en escala. Mantiene placer, belleza, legibilidad, agencia, sorpresa y reorganización
agradable separados; defaults son preguntas de exploración, no escalas validadas.
Rol se conserva; no infiere placer/eficiencia/HIT/fisiología. Web edita protocolo y
respuesta, muestra calendario, exporta preview, config portable sin participante/
estímulos y respuesta declarada. Operaciones stateless, sin guardar datos humanos.

Validación: 3 pruebas núcleo/API pasaron (0,79 s): ciclo completo3 balancea posiciones/
transiciones, repetición exacta, flags/offset, null/escala/IDs y rechazos. Build completo
pasó. Chrome API aislada pasó (1,4 s): calendario3, exportación nativa config sin
slot/estímulos, respuesta sintética válida, respuesta fuera de escala rechazada y
export obsoleto ausente. Servidor apagado; no sesiones humanas, medios privados,
escucha, exposición o sincronía física verificadas. Audio/defaults intactos.

## Siguientes entregas y dependencias

1. Presets portables guardables/importables, protocolo congelado con manifest y
   procedencia de estímulos resueltos por IDs (EVAL/R05/video) para repetir selección.
2. Player de condiciones con clock/audio/video y eventos de exposición observados
   por software, separando abort/pause/gaps/seeks de ensayos completados. Relojes y
   ganancia nominal no prueban niveles ni sincronización físicos: registrar medición.
3. Registro explícito de respuestas por trial/slot/rol, versiones y faltantes; no
   convertir preview ni validación sintética en respuesta humana realizada.
4. Comparador de respuestas individuales sobre estímulos/condiciones comunes,
   cobertura/faltantes, repetición intraindividual y acuerdos/desacuerdos; estimaciones
   de incertidumbre requieren diseño y tamaño adecuados, nunca rellenar null con0.
5. Decidir preguntas/escala/contexto e instrucciones con participantes; niveles
   comparables, orden completo cuando posible, roles distintos y ventanas idénticas.
   Desacoplamiento temporal no equivale a todas las alternativas de control.
6. Conectar R11/R12 por sincronización/procedencia, conservando independencia del
   registro fenomenológico: ningún proxy EEG/energético sustituye una respuesta.

No es un experimento ejecutado ni resultado científico. Requiere fuentes verificadas,
participantes y aceptación humana; avanzar en software no resuelve esos requisitos.


## Corte 2 · Presets portables persistidos

API /research/r10/presets guarda/lista/exporta name/config versionados con lectura
regular acotada. Config estricto excluye slot, rol, order_index, estímulos, ratings
y trial_id. Exportación sin ID local; append-only, reapertura tras restart. Web guarda
config de preview validada; importa preset completo o config raw exportada (64 KiB),
no aplica automáticamente. Aplicar reemplaza sólo config del protocolo editable,
conserva participante/rol/order/stimuli y limpia preview/respuesta validada sin ejecutar.

Cuatro pruebas núcleo/API pasaron (0,92 s), build completo pasó. Chrome API aislada
pasó (1,7 s): guardar, descargar/importar envelope y raw config, aplicar conservando
selección, limpiar preview y tres presets tras reload. Mantiene pruebas de respuesta
sintética/rechazo fuera de escala. Servidor apagado; no exposición/participación
humanas ni niveles físicos verificados. Defaults del instrumento/audio intactos.
Pendientes protocolos congelados/manifests, resolución de estímulos, player,
exposición observada, respuestas persistentes y análisis sobre soporte común.


## Corte 3 · Protocolos congelados reproducibles

API protocols guarda request/result/manifest con hashes, código/env y binding.
Recomputación actual repite calendario; histórico se identifica sólo integridad.
Recibos persistentes antes de run recuperan misma ID tras restart; otra entrada
con clave igual se rechaza y fallo reservado no relanza. Status complete describe
publicación del artefacto, nunca exposición ni ensayos completados.
Web guarda desde preview validada, persistiendo pedido antes de POST en
sessionStorage; reload restaura pendiente sin envío automático y reintento explícito
usa la misma entrada. Reabre calendario/preguntas/rol/slot/estímulos, inicializa
respuestas null y permite descargar tres artefactos. No guarda respuestas al abrir.

Siete pruebas núcleo/runner/servicio/API pasaron (1,06 s): repetición/no overwrite,
recomputation con hashes reescritos, binding histórico, restart/conflictos/fallo
sin relanzamiento/exportación. Build pasó. Chrome API aislada pasó (1,5 s): cuatro
condiciones/ciclo24 declarado, respuesta aceptada perdida/reload/reintento idéntico,
una copia/reapertura y descarga con orden5/rol/estímulo originales. Servidor apagado.
Sin exposición humana/medios privados/hardware, audio intacto. Pendientes resolver
estímulos por IDs, player/exposición, respuestas persistentes y análisis. No GC,
coordinación multiproceso/tab ni retención garantizada al cerrar pestaña.


## Corte 4 · Estímulos resueltos por IDs R05

POST r05-protocols recibe config/slot/rol/order y stimuli {id,r05_id,arm}, hasta8,
con recibo opcional. Resuelve PCM mono single/excited/mapped por verificador R05 y
original video vía source_binding de evaluación congelada. Congela IDs/hashes de
manifest/input/PCM/medio, evaluación/run/source/person slot, crop fuente y sr/frames.
Calendario toma ventana original seleccionada, excluye tail posterior del ensayo y
usa offset nominal0 (no sincronización física medida). Requiere PCM al menos del
largo del crop; no copia ni decodifica video, no tracking nuevo.

Comprueba fuentes antes/después de publicación; cambios eliminan sólo nuevo
protocolo. Recibo recupera sin resolver otra vez. Inputs y result sources ligados
al protocolo también en lectura histórica; recomputación del calendario no
revalida originales actuales. Ruta declarada protocols rechaza sources manuales.
Nombres/identidad/níveles físicos siguen sin autenticar. No hay exposición humana.

Diez pruebas núcleo/runner/servicio/API pasaron (3,75 s): R05 render real8kHz con
pose sintética, vínculo evaluación/media hashes, selección crop.3–1.5, recuperación
sin fuentes, mutación de PCM durante publicación, API/recibo y procedencia manual
rechazada. Medio original de fixture son bytes b'a', NO video decodificable/Chrome
ni prueba audiovisual. Sin medios privados/hardware/audio device. Pendientes UI/
Chrome de selección por IDs, fixture video real, player/exposición y registros.


## Corte 5 · Vista previa y selección R05 por web

r05-preview resuelve fuentes sin publicar. Selection admite expected_sources; al
publicar compara snapshots completos, rechazando cambios respecto a preview.
Canonical previo de recibos sin expected_sources permanece igual. Web inventario
R05 completo, selector single o excited/mapped según kind, etiquetas y builder
para varios estímulos; selección/config/rol/orden editables en JSON. Guarda sólo
tras preparar y envía hashes esperados. Pedido+clave se conserva antes de POST;
reload/reintento explícito recupera la misma entrada y actualiza inventario general
R10. 4xx limpia pendiente y preview; no aplica de nuevo fuentes silenciosamente.

Once pruebas núcleo/servicio/runner/API pasaron (4,71 s), build pasó. Chrome real
API aislada pasó (1,7 s): inventario/añadir/preparar, cero protocolos antes de save,
respuesta aceptada perdida/reload/reintento idéntico con expected_sources, una copia,
reapertura/calendario y descarga de hashes/crop .3–1.5. Fixture --experience-stimulus
con H264 sintético3s y tracking sintético preparado (no inferido del video), evaluación
real y R05 PCM8kHz; esta prueba NO reproduce audio/video ni verifica sincronía.
Sólo se duplica el medio sintético pequeño en fixture, ningún original privado.
Servidor apagado, audio/defaults intactos. Pendiente player/exposición/mediciones
físicas/respuestas/análisis. Sin garantía de retención al cerrar tab/multipestaña.


## Corte 6 · Media verificada por ensayo y relojes nominales

protocols/{id}/trials/{trial}/media-info reabre protocolo verificado y resuelve
R05/evaluación/video comparando snapshot con publicación. Expone trial, hashes,
duración y audio_support_elapsed_s (null sin soporte/medio habilitado). Reloj:
video_time=source_start+elapsed; audio_time=elapsed+offset; positivo adelanta audio.
Soporte audio intersecta [0,duración] con [0,pcm_frames/sr] desplazado, sin inventar
samples/wrap. Puede incluir tail R05 en condición desacoplada; no confundirlo con
movimiento adicional. Medio cambiado rechazado, ensayo desconocido404 y protocolo
sólo declarado no tiene media resoluble.

Rutas /video y /audio bloquean medio deshabilitado por condición. Video entrega
original verificado sin copiar; audio usa vista float32/Ranges y gain congelado,
PCM autoritativo float64 intacto. Archivos se sirven completos, NO recortados:
metadata define ventana para el player pendiente, no acredita cumplimiento de crop
ni exposición. No hay autoplay ni dispositivo abierto por estos endpoints.

Diez pruebas núcleo/servicio/runner/API pasaron (5,85 s): offset-.5 soporte[.5,1.2],
video clock origen.3, media alterada rechazada, gates video_only/sound_only,
Range44bytes RIFF con gain1, ensayo desconocido404. Fixtures PCM reales con pose
sintética/video bytes b'a'; NO reproducción Chrome ni medición física. Pendientes
player por condiciones/seek/pause/gaps/offset, eventos de exposición y aceptación.
Sin medios privados/hardware/audio ni cambios de defaults del instrumento.


## Corte 7 · Player web por condición

Abrir protocolo congelado con fuentes habilita player por trial. Preparar revalida
media-info y carga sólo medios habilitados, sin autoplay; video siempre muted
(excluye sonido original de cámara). Botones reproducir/pausar y seek nominal en
pausa acotan ventana, sin loop ni avance automático a siguiente ensayo. Clock de
transporte usa performance.now; followers corrigen drift suavemente, no seeks en
cada tick. Audio sólo reproduce dentro de support_elapsed; offset negativo espera
inicio disponible, agotamiento cercano al soporte no reinicia audio. Buffering/error
pausan y requieren reanudación explícita. Tiempo nominal no demuestra exposición.

Cambiar trial/preparar/abrir otro protocolo/unmount detiene medios y descarta
metadata obsoleta. Follower común acepta HTMLMediaElement y pausa un play pendiente
al resolver después de dispose; no toca síntesis Shaper, ratios o fases del instrumento.
Abrir otro protocolo limpia player anterior antes de esperar respuesta. Resultado
histórico sigue identificado por integridad y fuente revalidada al preparar.

Build pasó. Cuatro controles follower pasaron (0,9s); uno de decoder del instrumento
original quedó skipped por falta de fixture específica, no se presenta como ejecutado.
Nuevo Chrome contra API/R05/evaluación/H264 sintéticos pasó (4,4s, repetido tras
limpieza de apertura): cuatro condiciones, sin autoplay, video avanza, seek pausado
.7→video1.0, sound-only sin video, audiovisual, audio espera soporte por offset-.5,
pausa y reload sin player activo. Audio silenciado por test, NO escucha humana,
latencia física o aceptación. Primera corrida falló por formato .7 del slider en test;
corregido a0.7 sin cambiar comportamiento. Servidores detenidos, medios privados
intactos, sin dispositivo audio abierto por backend.

Pendientes eventos persistentes de exposición observada (buffering/seeks/gaps/
completitud), inyección Chrome de fallos/cargas tardías/agotamiento positivo,
respuestas persistentes/análisis y pruebas humanas con niveles/sincronía medidos.


## Corte 8 · Fallos y agotamiento del player

Tres pruebas Chrome del player pasaron juntas (7,5 s), contra API y medios
sintéticos: condiciones y seeks del corte 7; offset positivo +.5 con agotamiento
de audio sin reinicio y fin nominal en 1.2 s; pausa del reloj y ambos medios ante
waiting, sin reanudación automática por canplay; respuesta real de media-info
retenida y liberada después de desmontar el player sin revivir medios.

El evento waiting fue inyectado: verifica su manejo, no una congestión de red real.
Audio silenciado por las pruebas; no acredita escucha, exposición humana, latencia
física o sincronización medida. No se requirieron cambios de producción ni defaults.
El servidor sintético terminó con exit 0; medios corporales y servicios cotidianos
intactos. Pendientes registro persistente de transporte/observaciones, respuestas
y análisis, y ensayos humanos con niveles y sincronización medidos.


## Corte 9 · Contrato de telemetría de transporte

experience_transport.py define snapshots de estado HTMLMediaElement y eventos con
secuencia contigua, reloj monotónico, epochs y posición acotada al ensayo. Rechaza
retroceso sin nuevo epoch, medios incompatibles con condición y valores no finitos.
Resumen determinista cuenta seeks/waiting/errores y fin nominal declarado: NO
calcula duración de exposición interpolando eventos ni equipara fin con completitud.
Hashes e IDs son declaraciones hasta que el servicio futuro los vincule al protocolo.

Dos pruebas pasaron (0,12 s): retroceso/epoch, secuencia/reloj/posición, NaN y medio
deshabilitado; resumen repetible sin métrica de exposición inventada. Es un contrato
aún no conectado al player ni persistido/API/UI. Esos entregables siguen pendientes.
Sin cambios de defaults, sonido, hardware ni medios corporales.


## Corte 10 · Vinculación de transporte al protocolo

bind_protocol verifica artefactos R10 y hash manifest declarado, trial existente,
duración y gates exactos; revalida manifest al terminar. Recupera role/slot, trial
y fuentes congelados, sin tomar identidad ni condición del cliente como evidencia.
No revalida disponibilidad actual de medios ni demuestra exposición. Acepta planes
declarados sin fuentes, identificados por lista vacía, sin inventar media.

Cinco pruebas de transporte y runner pasaron (0,34 s), incluyendo reapertura del
servicio, rechazo de hash/trial/duración/gates contradictorios y artefacto alterado.
Pendientes persistencia con recibos, API, captura de eventos en player y exportación
web. Defaults y experiencia sonora intactos.


## Corte 11 · Registros de transporte persistentes

TransportService guarda trace/binding/manifest locales inmutables en r10-transports,
con ID derivado de contenido, hashes e implementación. Reintentos idénticos después
de restart recuperan el mismo registro sin exigir medios/protocolo originales;
registros nuevos exigen bind_protocol verificado. Lectura valida hashes, identidad
de contenido y trial/gates/duración; resumen se recalcula sólo con código coincidente,
histórico se marca integridad solamente. Exporta tres artefactos; listado omite
registros incompletos/alterados. Publicación incompleta no se relanza silenciosamente.

Cuatro pruebas pasaron (0,32 s inicial; repetidas tras verificación de identidad):
retry/restart, exportación, lectura sin protocolo original, registro nuevo rechazado
sin protocolo, corrupción omitida y traversal rechazado, junto a contrato/binding.
Pendientes API/UI/captura de eventos; sin cambios de sonido/defaults. Hashes no
son custodia firmada; snapshots declarados no prueban exposición humana.


## Corte 12 · API de registros de transporte

POST/GET /api/research/r10/transports publican/listan telemetría declarada;
GET /transports/{id}/artifacts/{name} exporta trace/binding/manifest como attachments.
POST valida contrato y protocolo/trial congelados, retry de contenido idéntico
recupera registro existente. Rutas no abren dispositivo ni exigen protocolo de
evaluación para explorar el instrumento cotidiano.

Nueve pruebas API/contrato/servicio pasaron (2,47 s): creación, retry, exportación
byte a byte después de restart, gates/trial contradictorios y artefactos desconocidos
rechazados. Warning de deprecación Starlette/AnyIO, sin fallo. Pendientes captura y
recuperación web de eventos, respuestas persistentes/análisis y aceptación humana.
No pruebas Chrome nuevas en este corte, no escucha ni sincronía física acreditadas.


## Corte 13 · Captura y guardado explícito desde player

Player captura prepared/play_requested/pause/seek/waiting/media_error/nominal_end,
snapshots cada 250 ms mientras corre y estado HTMLMediaElement. Exportación JSON
local y guardado explícito en pausa, con enlaces trace/binding/manifest. No autoplay
ni protocolo obligatorio para exploración cotidiana. Registro local se reemplaza
al preparar otro ensayo, advertencia visible; máximo 20000 eventos, overflow visible.

Build pasó y tres Chrome pasaron (7,6 s), incluidos registro guardado por API,
trial/seek/play/snapshot/secuencia de trace exportado, gates/offset/buffering/cierre
de cortes previos. Medios sintéticos y audio silenciado; no exposición humana ni
sincronía física. waiting inyectado, no congestión real.

Pendientes congelar y recuperar POST fallido tras reload, inventario web de registros
y conservación de cierre/unmount: closed queda sólo en memoria si no se exporta;
no se afirma durabilidad de eventos posteriores al guardado. Guardar produce snapshot
finito, no actualiza artefacto existente. Sin cambios al instrumento/sonido/defaults.


## Corte 14 · Recuperación web e inventario de transporte

Antes del POST, player congela JSON en sessionStorage. Envió fallido conserva
contenido; no permite guardar otro hasta recuperar el pendiente. Panel independiente
restaura tras reload, retry explícito sin autoplay/player, lista registros y ofrece
attachments. Identidad por contenido evita duplicados; retry no añade snapshots
posteriores. No autoenvío, almacenamiento limitado a la sesión de esa pestaña.

Build y tres Chrome pasaron (7,8 s). API aceptó primer POST y respuesta fue abortada
a propósito; reload restauró pendiente, segundo POST idéntico recuperó un único
registro. También verificadas condiciones/seek/offset/buffering/carga tardía. Audio
silenciado y medios sintéticos; no exposición humana ni sincronía física.

Pendientes gestión explícita de pendiente inválido/rechazado (ahora conserva para
diagnóstico), conservar cierres/unmount posteriores al snapshot, respuestas
persistentes/análisis y ensayo humano. sessionStorage no garantiza recuperación
al cerrar pestaña ni si almacenamiento falla; fallo visible evita enviar sin copia.
No cambios del instrumento/sonido/defaults ni medios privados.


## Corte 15 · Pendientes inválidos recuperables

Panel permite exportar bytes originales del envío pendiente, incluso JSON inválido,
y descartar explícitamente sólo la copia de esa pestaña. No elimina registro ya
aceptado por servidor. Pendiente rechazado sigue disponible para diagnóstico/retry;
no queda bloqueo sin salida. Sin autoenvío ni autodiscard.

Build y cuatro Chrome pasaron (8,3 s): exportación exacta '{broken-json', ausencia
de retry inválido, descarte explícito y reload sin pendiente, más suite del player y
recovery aceptado-respuesta perdida. Medios sintéticos/audio silenciado, sin escucha
humana. Pendientes conservación de cierre y respuestas/análisis; defaults intactos.


## Corte 16 · Respuesta vinculada a preguntas congeladas

experience_response.Request referencia protocolo/hash + Response estricta y
transport_id opcional. resolve verifica protocolo, trial guardado y escala/items,
conserva null; recupera preguntas/role/slot del protocolo. Transporte opcional debe
coincidir en protocolo/hash/trial y trial completo; hash se verifica al terminar.
No exige transporte para declarar una respuesta ni infiere exposición desde fin
nominal. Preguntas configuradas no son escalas científicamente validadas.

Cuatro pruebas response/protocol/transport-service pasaron (0,37 s): null/75,
reapertura, rechazo de escala/item/hash/trial y transporte de otro protocolo/ensayo.
Este corte resuelve/vincula en memoria; persistencia, API/UI de respuestas y análisis
siguen pendientes. Sin datos humanos nuevos ni cambios de sonido/defaults.


## Corte 17 · Respuestas persistentes y API

ResponseService guarda request/result/manifest inmutables bajo r10-responses,
ID por contenido y retry idéntico tras restart. Corrección crea registro nuevo sin
reemplazar ni deduplicar participantes implícitamente. Snapshot conserva preguntas,
escala/trial/role/slot y vínculo opcional de transporte. Lectura valida hashes,
identidad y binding de respuesta/role/slot aun histórica; con código coincidente
recalcula ratings. Reabrir no exige protocolo/media originales; nuevo registro sí.

POST/GET /api/research/r10/responses y GET /responses/{id}/artifacts/{name}.
Ocho pruebas API/servicio/binding pasaron (2,62 s); dos repetidas tras reforzar
binding histórico (0,37 s inicial previo). Retry, corrección, null, exportación
idéntica tras restart, fuente eliminada y corrupción verificadas. Warning AnyIO
de deprecación sin fallos. Pendientes UI/recovery y análisis descriptivo, aceptación
humana y hardware. Datos sintéticos, sin respuestas humanas nuevas ni defaults.


## Corte 18 · Guardado y recuperación web de respuestas

Panel independiente usa respuesta JSON existente y protocolo abierto; apertura
calcula SHA-256 de bytes del manifest recibido, guardado referencia ese hash.
Transport_id opcional explícito. Congela POST en sessionStorage antes de enviar,
retry tras reload sin incorporar ediciones posteriores, listado/exportaciones.
Pendiente inválido/rechazado exportable y descartable localmente; no autoenvío.

Build y cinco Chrome pasaron (9,1 s): respuesta sintética pleasure75/beautynull,
POST aceptado con respuesta abortada, reload, retry idéntico, único registro y
listado; también suite player/transporte. No respuestas humanas ni aceptación.
Snapshots nuevos requieren protocolo abierto; validación stateless sigue separada.
Pendientes análisis descriptivo, cierre duradero de transporte, ensayos humanos
y mediciones físicas. sessionStorage limitado a sesión/pestaña, no backup.
Sin cambios de sonido/defaults ni medios privados.


## Corte 19 · Análisis descriptivo seleccionado

experience_analysis analiza 1–256 IDs de respuestas verificadas, congela snapshots
y hashes, revalida al terminar. Agrupa sólo preguntas/texto/escala idénticos, role y
condición; informa valores, conteo respondido/null, mediana/min/max sin imputación.
Rechaza IDs duplicados y dos correcciones de un mismo protocolo/trial. Registros de
otros protocolos no se consideran participantes independientes por tener otro ID.
API POST /api/research/r10/analysis-preview stateless; no publicación todavía.

Siete pruebas núcleo/API pasaron (2,63 s): mediana50 de0/100, null sin convertir
a cero, corrections rechazadas, roles/escalas separados, repetibilidad y preview
HTTP. Warning AnyIO de deprecación sin fallo. Pendientes web, manifest de análisis
frozen/recovery/exportación y contraste pareado explícito. No hipótesis, causalidad
ni aceptación científica/humana acreditadas; sin defaults ni datos privados nuevos.


## Corte 20 · Selección y tabla descriptiva web

Panel de análisis lista respuestas y exige selección explícita vacía inicialmente.
Preview muestra tabla por preguntas/texto, condición/role y escala: respondidos,
null, mediana/min/max (— sin valores). Exportación JSON incluye snapshots y hashes
de fuentes/límites. Cambiar selección/actualizar invalida preview anterior; tokens
descartan resultados tardíos al desmontar. No participantes inferidos ni autoanálisis.

Build y cinco Chrome pasaron (8,8 s): selección de respuesta sintética, tabla75 y
null como —, descarga real con ID de fuente/null, deselección limpia tabla y
deshabilita análisis; suite player/recovery previa también pasa. Sin aceptación
humana/escucha. Pendientes manifest y publicación/recovery de análisis congelados,
contraste pareado y cierres duraderos. Sin cambios de sonido/defaults.


## Corte 21 · Cálculo puro sobre fuentes congeladas

FrozenInput valida selección/sources ordenados e IDs/hash; calculate trabaja sin
servicio, usando snapshots, identidad de contenido y trial recalculado desde
protocolo. analyze sólo resuelve/verifica fuentes y llama ese mismo núcleo.
Permite recomputar después de eliminar respuestas originales sin inventar fuentes
actuales; hash manifest de fuente sigue referencia, no custodia firmada.

Ocho pruebas núcleo/API pasaron (2,63 s), más dos del núcleo repetidas tras validar
identidad: cálculo idéntico sin original, selección/trial/ratings contradictorios
rechazados. API preservada. Pendientes runner/manifest y guardado/recovery web del
análisis; contraste pareado y aceptación humana siguen abiertos. Defaults intactos.


## Corte 22 · Runner y manifest de análisis congelado

experience_analysis_run publica request/result/manifest en directorio nuevo,
sha256 de entrada/salida, código y entorno Python/metric. Verificador chequea
inventario, regularidad/tamaño, binding selection/sources aun histórico y recálculo
completo sólo si código/entorno coinciden. Histórico dice integridad solamente;
status complete describe artefactos, no roadmap/exposición/validez científica.

Tres pruebas runner/núcleo pasaron (0,40 s), runner repetido tras limpieza import:
resultado igual a preview, recálculo sin original, overwrite prohibido, mediana
alterada con hash actualizado rechazada por recálculo, lectura histórica explícita
y fuentes distintas rechazadas aun con hashes rehechos. Hashes no custodia firmada.
Pendientes servicio/recibos, API y guardar/reabrir web del análisis; pareados y
aceptación humana. Sin defaults/sonido ni datos privados nuevos.


## Corte 23 · Servicio y API de análisis congelados

AnalysisService exige IDs+hashes expected_sources de preview, revalida fuentes
antes/después de publicar. ID por selección/hashes permite retry tras restart sin
fuentes originales; lectura recalcula snapshots. Fallo de publicación elimina sólo
su carpeta nueva, sin tocar respuestas u otros análisis. API POST/GET analyses y
GET analyses/{id}/artifacts/{name}; tres artefactos exportables.

Ocho pruebas servicio/runner/API pasaron (2,70 s): hashes distintos desde preview
rechazados sin publicación, retry mismo ID, exportación idéntica tras restart,
fuente eliminada y paridad preview/resultado guardado. Warning AnyIO sin fallo.
No inyección de fallo durante publicación en este corte; caso queda pendiente
para verificación específica. Pendientes guardar/recovery/reabrir web, pareados y
ensayos humanos. Sonido/defaults y datos privados intactos.


## Corte 24 · Guardar/reabrir análisis en web y fallo de publicación

Panel de análisis frozen guarda selección/hashes de preview, congela pending en
sessionStorage y ofrece retry tras reload sin cambiar contenido. Listado/reapertura
actualizan tablas desde resultado guardado, con etiqueta explícita y attachments.
Pendiente exportable/descartable localmente; no autoenvío/autoanálisis.

Build y cinco Chrome pasaron (9,2 s): POST de análisis aceptado con respuesta perdida,
reload/retry idéntico, único registro, reapertura tabla75/null y suite previa.
Prueba servicio pasó (0,33 s): fallo inyectado después de escribir artifacts limpia
únicamente intento nuevo y preserva bytes del análisis anterior.

Pendientes carreras de reapertura tardía vs edición de selección, contraste pareado,
conservación de cierre y ensayos humanos. Fixtures sintéticos/audio silenciado, sin
aceptación física/científica. Sonido/defaults intactos.
