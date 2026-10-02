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
