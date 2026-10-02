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
