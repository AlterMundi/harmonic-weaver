# R09 · Observaciones espaciales y sincronización

Primer corte: `spatial_observations.py` define streams con dimensión, marco,
unidades, proveedor, slot de sujeto, calibración y reloj originales explícitos.
Mapeo de reloj afín t_común=offset+rate*t_fuente, incertidumbre no negativa y
método declarado. Sincronización medida exige referencia de evidencia; esto no
verifica por sí mismo la evidencia ni convierte una suposición en medición.

Pose de imagen es 2D normalizada; profundidad monocular debe permanecer inferred.
Metros y multivista requieren ID de calibración; el contrato no prueba exactitud
ni resuelve extrínsecos. Missing conserva causa y no admite posición/confianza.
Gaps permanecen gaps; no interpolación, identidad biométrica ni escala inventadas.

Validación: dos tests pasaron (0,13 s), con reloj afín, roundtrip, gaps/missing y
rechazo de coordenadas no finitas, dimensión incorrecta, profundidad presentada
como observada, escala sin calibración y sincronización medida sin evidencia.

Pendientes: adaptador de HarMoCAP 2D, importación configurable/API/UI, evaluación
de ambigüedades con clips, calibraciones realmente verificadas, multivista y
proveedores monoculares. No se instalaron modelos, compraron sensores ni
reconstruyeron videos privados. Este contrato no es un benchmark 3D ni evidencia
sobre HIT. Comparar cámaras/IMUs requiere medir sincronización, escala, deriva y
error contra referencia independiente; reproyección baja no demuestra profundidad.

## Corte 2 · Adaptador de observaciones existentes

`spatial_adapter.convert` recibe MotionFrames congelados, person_id explícito y
Clock. Mantiene camera_isotropic/frame_height (x puede superar 1 por aspect);
no los normaliza como [0,1] ni estima profundidad/metros. Conserva sequence/time,
confianza soportada y held como held. Produce 17 etiquetas; missing borra posición
residual y distingue persona ausente, articulación no presente y missing de origen.
No selecciona otra persona ni transfiere calibración. Fuente/stream, geometría,
unidades/dimensión y timestamp_origin deben ser homogéneos; gaps no se rellenan.

Cuatro tests contrato/adaptador pasaron (0,14 s): unidades reales, held/missing,
slot ausente, gaps, repetición sin mutación y rechazo de fuentes/geometrías/relojes
mezclados o 3D. Fixtures sintéticos del contrato, no tracking privado nuevo.
Pendiente API/UI/importación/persistencia y validación de clocks/cámaras reales.

## Corte 3 · API de conversión/validación

POST `/api/research/r09/convert` recibe el Request del adaptador y devuelve inputs,
stream espacial, cobertura por observed/held/inferred/missing y tiempos comunes
calculados con el reloj declarado. Verifica resultado finito. POST
`/api/research/r09/validate` valida un Stream externo y devuelve
`validation: contract_only`: no autentica source, calibración ni sincronización.
Ambas rutas son stateless y no crean un archivo de datos corporales ni cambian live.

Cinco tests contrato/adaptador/HTTP pasaron (0,75 s): cobertura exacta, clocks,
roundtrip y rechazo de slot booleano, reloj inválido, paths extras y metros
incompatibles. Pendiente UI/importación por fuente autorizada, persistencia
reproducible y medición real de calibraciones/relojes. Validación de esquema no
presenta observaciones monoculares como reconstrucción 3D verificada.

## Corte 4 · Importación y configuración en web

Panel R09 en Investigación: importar JSON local (32 MiB), editar datos, elegir
MotionFrames→2D o validación de Stream, slot explícito y reloj completo editables.
Muestra proveedor/dimensión/unidad, cobertura por estado y JSON resultante; exporta
resultado por descarga nativa. Edición limpia resultado anterior. Reloj inicial
es suposición declarada: incertidumbre cero no demuestra sincronización.
No guarda automáticamente, selecciona personas ni modifica audio/live.

Build pasó; Chrome real con API (1,4 s) importó MotionFrames sintéticos, configuró
slot/offset/incertidumbre, verificó cobertura y tiempo común, descargó resultado,
validó el Stream y mostró rechazo de input inválido. Servidor aislado detenido.
Pendientes persistencia/presets, acceso desde cache autorizado, visualización
espacial y medición real; el JSON importado es declaración, no origen autenticado.

## Corte 5 · Segmento desde biblioteca de tracking

`VideoLibrary.spatial_segment` congela bajo lock una generación in-memory ready
con cache_key/generation definidos, rango inclusivo <=120 s y deep copies. Devuelve
procedencia sin path: job/media/cache/generación/device y rango. `from_library`
convierte ese snapshot con slot/reloj explícitos. POST `/api/research/r09/source`
se registra cuando existe runtime de biblioteca; no calcula tracking ni lee/copia
video. Un slot ausente permanece missing, no selecciona otro.

Seis tests biblioteca/adaptador/contrato/API de conversión pasaron (0,83 s).
Prueba biblioteca usa video inexistente y tracking sintético identificado para
confirmar ausencia de lectura de medios, límites inclusivos, independencia del
snapshot y rechazo de rango vacío/fuera de duración/tracking incompleto. Ruta
source aún pendiente de prueba HTTP y UI. La procedencia es una generación
completa en memoria, no revalidación del cache en disco ni bytes actuales de video.

## Corte 6 · Inventario y controles de biblioteca

GET `/api/research/r09/sources` lista sólo generaciones ready identificadas, con
slots/device/duración/cache, sin paths. Modo web Desde tracking completo: actualizar
inventario explícitamente, elegir generación, rango y slot/reloj. Cambio de fuente
limpia slot/resultado; nunca cambia silenciosamente el cuerpo.

Siete tests hasta HTTP pasaron (0,86 s): inventario, generación/rango inclusivo,
slot ausente→34 missing, job inexistente→404, tracking incompleto fuera de inventario
y solicitud rechazada. Build pasó; este recorrido de biblioteca en Chrome está
pendiente (importación JSON del corte 4 sí verificada). Datos in-memory no acreditan
integridad actual de cache/video. No inicia tracking ni abre medios por esta ruta.

## Corte 7 · Recorrido de biblioteca en Chrome

Fixture opcional `--spatial-generation` inyecta una generación sintética explícita
(no backend de pose real) sin dispositivos. Chrome real contra API pasó (1,5 s):
inventario, elección de fuente/slot obligatoria, rango inclusivo [0,.2] con índices
0/2, generación ligada y sin paths, cobertura 1 observed/33 missing, slot ausente
34 missing, rango fuera de duración rechazado y cero POST a inicio de tracking.
Servidor aislado detenido. Confirma funcionamiento UI/HTTP, no integridad de cache
real, precisión corporal ni calibración. Persistencia/presets siguen pendientes.

## Corte 8 · Conversiones congeladas reproducibles

`spatial_run` guarda Input {conversion: Request}, resultado y manifest en directorio
nuevo; hashes/binding, código y versión Python, archivos regulares y estabilidad
durante lectura. Recálculo actual exige igualdad de conversión; histórico de otras
versiones sólo acredita integridad. No sobrescribe ni requiere generación live.
No autentica observaciones ni prueba profundidad/calibración/sincronización.

Seis tests persistencia/adaptador/contrato pasaron (0,17 s): inputs independientes,
resultado alterado con hash reescrito rechazado, binding histórico, versiones,
symlinks y sobrescritura. Pendiente servicio/API/UI y procedencia de biblioteca
congelada; por ahora runner conserva inputs declarados, sin afirmar origen verificado.

## Corte 9 · Servicio/API e inventario web

POST/GET `/api/research/r09/conversions` y GET `/{id}/artifacts/{name}` guardan
conversiones declaradas, listan resultados verificados y descargan tres JSON.
Servicio elimina sólo su carpeta nueva si falla publicación. Reabrir no necesita
tracking vivo. Web incorpora guardar explícito, inventario/reapertura y descargas.
Guarda sólo Request de conversión, no tracking_provenance: se informa expresamente
que el origen sigue declarado. Persistir procedencia verificada sigue pendiente.

Diez tests contrato/adaptador/biblioteca/runner/HTTP pasaron (1,03 s): descarga,
reinicio y métricas alteradas con hash reescrito rechazadas/excluidas de inventario.
Build pasó; recorrido de persistencia web en Chrome pendiente. También idempotencia,
recuperación de respuesta POST perdida, presets y mediciones físicas pendientes.
No guardado automático ni modificación de live/audio; ningún video privado copiado.

## Corte 10 · Persistencia web verificada en Chrome

Chrome real contra API pasó (1,7 s): importación MotionFrames sintéticos, slot/reloj,
cobertura/t_común, exportación, guardado explícito, descarga nativa del artefacto,
reload/reapertura sin otra corrida y bytes originales intactos; conserva validación
Stream y rechazo de JSON inválido. Fixture/server aislados, servidor detenido.
No aceptación humana, fuente privada ni validación física. Pendientes procedencia
de biblioteca congelada, idempotencia/recuperación de POST y presets.

## Corte 11 · Procedencia de generación guardada

Runner admite procedencia tipada y ligada al segmento; recálculo la conserva.
POST `/api/research/r09/source-conversions` resuelve snapshot/metadata en servidor
con expected_generation obligatorio; si cambió, rechaza sin trasladar fuente.
Ruta de conversión declarada rechaza atribuirse tracking_provenance. Web añade
Guardar desde generación sobre la selección inspeccionada, separado del guardado
declarado. No revalida cache en disco, video actual ni custodia firmada.

Diez tests hasta HTTP pasaron (1,05 s), incluyendo persistencia de generación,
rechazo de generación antigua y de procedencia inyectada por ruta declarada.
Build pasó; botón de procedencia en Chrome pendiente. Idempotencia/presets y
mediciones físicas pendientes; datos privados/audio no modificados.

## Corte 12 · Procedencia persistida verificada en Chrome

Chrome real contra API/generación sintética pasó (1,7 s): guardar desde generación,
una corrida, reload/reapertura y tracking_provenance idéntica al artefacto guardado.
Conserva selección explícita, rango inclusivo, missing para slot ausente y rechazo
fuera de duración; cero POST de inicio de tracking. Servidor aislado detenido.
No prueba calidad corporal, cache físico ni calibración; idempotencia y presets
siguen pendientes. No datos privados ni cambios sonoros.

## Corte 13 · Recibos persistentes de guardado

SaveRequest/source-save admiten clave estricta opcional de idempotencia. Recibo
previo al cálculo liga modalidad+request por hash; recuperar mismo intento devuelve
corrida congelada antes de resolver biblioteca. Funciona tras reinicio y sin job
in-memory; solicitud distinta se rechaza. Falla/interrupción no relanza con ese
recibo. Un propietario, sin coordinación multiproceso ni GC; no signed custody.

Cinco tests servicio/HTTP pasaron (0,99 s): declarado recuperado tras reinicio,
request incompatible, fallo sin relanzar y fuente recuperada tras eliminar job.
Pendiente envío/recuperación de claves desde web y Chrome de respuesta perdida;
las claves opcionales no corrigen aún reintentos de botones web actuales.

## Corte 14 · Recuperación de guardado en web

Ambos botones envían clave de intento y conservan route/body en sessionStorage
antes del POST. Respuesta perdida conserva pendiente y bloquea otro guardado;
reload ofrece recuperación explícita, nunca autoinicio. 4xx libera pendiente.
Si storage falla, no envía POST; JSON grandes pueden exceder cuota del navegador.
Cierre de pestaña no garantiza retención; sin coordinación multipestaña/GC.

Build pasó; Chrome real en fixtures independientes verificó guardado declarado
(1,8 s) y source (2,0 s), abortando respuesta después de aceptación en servidor,
reload y reenvío con cuerpo/clave idénticos, una corrida y reapertura. Conserva
cobertura/procedencia/exportación y ausencia de nueva inferencia. Servidores
aislados detenidos. Tracking sintético, no aceptación/calibración física.

## Corte 15 · Inspector espacial configurable

Vista por frame con índice/tiempo originales, ejes XY/XZ/YZ (según dimensión),
escala y centro explícitos. Conserva unidades/marco, distingue observado/held/
inferido y no dibuja missing ni une puntos. Informa fuera de encuadre; no autoescala
que oculte amplitudes, no profundidad inventada ni reconstrucción física acreditada.

Build pasó. Chrome real verificó 2D→frame missing sin puntos fantasma (2,0 s,
con recorrido source/recuperación de guardado), y 3D monocular sintético con XY/XZ,
centro/escala, coordenadas proyectadas esperadas y clipping informado (1,2 s).
Servidor aislado detenido. Son proyecciones de datos declarados, no benchmark de
reconstrucción; presets de vista, reproducción temporal y evidencia física pendientes.

## Corte 16 · Reproducción con gaps explícitos

Inspector reproduce por timestamps fuente con RAF, velocidad ajustable, pausa,
loop y seek por tiempo/frame. Un gap máximo visible configurable (default .1 s)
oculta puntos cuyo soporte venció hasta la próxima observación, sin interpolar.
Índice/tiempo de observación y reloj de reproducción separados. No autoplay ni
sincronización implícita con video/audio; límite exacto termina reproducción.

Build y Chrome real con generación sintética pasaron (2,0 s): seek a .15 s entre
frames 0/.2 oculta puntos, play avanza hasta .2 y se detiene; recorrido previo de
missing, recuperación de guardado y procedencia intacto. Loop/velocidad están
implementados, validación específica aún pendiente, igual presets de vista.
Servidor aislado detenido; no aceptación física ni audio modificado.

## Corte 17 · Reloj controlado para playback

Chrome real con page.clock y API real pasó (1,6 s): velocidad x2 avanza dentro
rango esperado, pausa mantiene tiempo tras avance del reloj, seek .9 + loop vuelve
al inicio sin detenerse, sin loop termina exactamente en 1 s. Fixture 3D monocular
sintético declarado, sin video/audio asociado. Servidor aislado detenido.
Evidencia del inspector, no sincronización audiovisual ni reconstrucción física.
Presets de vista siguen pendientes; no defaults de síntesis cambiados.

## Corte 18 · Presets portables del inspector

Contrato/API `view-presets` conserva sólo ejes, escala/centros, velocidad/loop y gap
máximo. No admite frames, slot, reloj, calibración ni fuente. Web permite nombrar,
guardar, importar JSON (64 KiB), exportar y aplicar explícitamente. Aplicación pausa
la vista, conserva tiempo actual y rechaza XZ/YZ sobre 2D sin fallback silencioso.
No autoinicio ni cambio de síntesis. Cada guardado crea un ID nuevo.

Prueba HTTP pasó (0,79 s): roundtrip/exportación sin ID, exclusión de datos de
observación/calibración, valores inválidos y recuperación tras reinicio. Build
pasó; recorrido de presets en Chrome pendiente. No acredita comparación física.

## Corte 19 · Presets de vista verificados en Chrome

Chrome real contra API pasó (1,6 s): guardar preset XZ/centro/escala, descarga
nativa, importar archivo exportado y aplicar restaurando ejes/escala modificados.
Al cambiar a otra fuente 2D, aplicar XZ muestra rechazo y conserva XY, sin fallback
silencioso ni traslado de observaciones. Conserva prueba de proyección/clipping.
Servidor aislado detenido. Fixtures 2D/3D declarados, no reconstrucción física ni
aceptación humana; preset no verifica calibración, relojes ni interpretación entre
fuentes. Medición física y líneas restantes siguen abiertas.

## Corte 20 · Comparación causal en reloj común

`spatial_compare` exige mismas dimensiones/unidades/marco y reloj común declarado.
En cada tiempo de referencia toma último candidato <=t, limita edad e incertidumbre
combinada; nunca busca mejor desfase, escala/rotación ni reasigna labels. Selección
de labels explícita y opt-in para inferred/held. Devuelve causas, estados, edad,
coverage, errores en unidades originales y nulos sin soporte.

Dos tests pasaron (0,13 s): frame futuro excluido, gap candidato viejo, error conocido
.5, cobertura 1/3, incertidumbre excesiva→sin soporte, opt-in de inferred y rechazo
de marcos/unidades/relojes/labels incompatibles. Causalidad es respecto a tiempos
declarados, no garantía ante clock incorrecto. Igual nombre de marco no autentica
extrínsecos. Pendientes persistencia/API/UI, procedencia de comparación, matrices
calibradas verificadas y referencia física independiente; no benchmark 3D real.

## Corte 21 · Comparaciones congeladas por API

`spatial_compare_run/service` conserva ambos streams y settings en request,
resultado y manifest. Recálculo exacto actual, binding/hash/archivos regulares y
estabilidad; lectura histórica explícita. POST/GET `/api/research/r09/comparisons`
y GET `/{id}/artifacts/{name}` permiten guardar/listar/exportar/reabrir sin fuentes
live. Importados son declarados, no origen autenticado; no ajuste de calibración.

Cinco tests núcleo/runner/HTTP pasaron (0,90 s): métrica conocida, entradas
congeladas, resultado alterado con hash reescrito rechazado, binding histórico,
symlink/sobrescritura, exportación/reinicio e incompatibilidad de marco.
Pendientes web, resolución de IDs de conversiones/procedencia, idempotencia y
comparación física independiente. No medios privados ni audio modificados.

## Corte 22 · Comparación espacial en web

Panel con referencia/candidato JSON, etiquetas, edad/incertidumbre máxima y opt-in
inferred/held. Guarda explícitamente, muestra soporte y error en unidad original,
JSON con causas, inventario histórico/reapertura y descargas. No ajusta relojes ni
geometría para mejorar error. Entradas siguen declaradas.

Build y Chrome contra API real pasaron (1,3 s): error sintético conocido .5,
coverage 1/2 (primer candidato futuro excluido), descarga nativa y reload/reapertura
sin otra corrida. Servidor aislado detenido. Pendientes selección de conversiones
por IDs/procedencia, presets de comparación e idempotencia; no calibración física.


## Corte 23 · Comparación de conversiones persistidas

`POST /api/research/r09/compare-conversions` recibe reference_id, candidate_id
(IDs de conversión) y settings (labels, edad/incertidumbre máxima, opt-ins).
Resuelve streams de artefactos verificados y congela IDs + SHA256 de cada manifest
como sources en request/result. Revalida fuentes antes y después de publicar;
si cambian elimina únicamente la nueva comparación. La ruta declarada
/comparisons rechaza sources suministrados por cliente. El verificador exige
binding de sources también al leer resultados históricos.

Siete pruebas de núcleo/runner/servicio/HTTP pasaron (1,02 s): error conocido,
causalidad, procedencia, fuentes intactas, rechazo de cambios durante publicación,
exportación/reapertura y rechazo de procedencia declarada como resuelta. Fixture
con incertidumbre .02 por stream usa umbral combinado .04 explícito; defaults
no cambiados. Ningún medio privado ni audio procesado. No autentica calibración,
identidad, sincronización física ni custodia firmada. Pendientes selección por ID
en web, idempotencia y presets de comparación.


## Corte 24 · Selección web de conversiones para comparar

El panel R09 ofrece streams declarados o conversiones guardadas. Actualizar
inventario es explícito; referencia y candidato se eligen sin selección silenciosa.
Con IDs envía settings a compare-conversions y muestra procedencia en el resultado;
los hashes completos permanecen en JSON exportable. No se autentican relojes ni
calibración física. Defaults y síntesis sin cambios.

Build completo pasó. Dos pruebas Chrome contra API real aislada pasaron (1,8 s):
recorrido declarado/exportación/reload y selección de dos conversiones persistidas,
error cero conocido y binding de ambos IDs + hash. Datos sintéticos, sin dispositivos
ni medios privados; servidor de prueba detenido. Pendientes presets e idempotencia
para comparación y validación física de las fuentes.


## Corte 25 · Presets portables de comparación

API comparison-presets y panel permiten guardar, listar, aplicar, exportar e
importar parámetros/etiquetas. No incluyen streams, IDs de conversión, persona,
reloj ni calibración. Aplicar sólo cambia controles, sin seleccionar fuentes o
publicar corridas. Importar valida en servidor (archivo web máximo 64 KiB).
Validación de etiquetas únicas/no vacías ahora pertenece a Settings compartido,
para rechazar presets inválidos antes de comparar. Almacenamiento append-only,
reapertura tras reinicio y exportación sin ID local.

Nueve pruebas backend pasaron (1,19 s), build completo pasó y dos pruebas Chrome
contra API aislada pasaron (2,0 s), incluyendo guardar/aplicar conservando fuentes,
descarga/importación nativa y procedencia de comparación. Sin medios privados ni
dispositivos; servidor detenido. Defaults/síntesis sin cambios. Pendiente
idempotencia de comparación y validación física de relojes/calibración.


## Corte 26 · Recibos persistentes del comparador

Ambas rutas de publicación aceptan idempotency_key (32 hex). Congelan un recibo
con ID y hash de tipo/entrada normalizada antes de ejecutar. Reintentar la misma
entrada devuelve la corrida verificada, también tras reinicio y sin resolver de
nuevo conversiones originales; otra entrada con esa clave se rechaza. Un fallo
con recibo reservado no relanza cálculo: informa corrida no disponible. Fuentes
resueltas siguen verificándose antes/después de publicación inicial; sólo la
nueva carpeta se elimina al fallar. Sin clave, cada llamada sigue siendo nueva.

Once pruebas backend pasaron (1,29 s); después de ampliar el recorrido HTTP,
cinco pruebas de servicio/API pasaron (1,02 s), incluyendo recuperación misma ID,
conflicto de clave, recuperación sin fuentes y fallo sin relanzamiento. No hay
coordinación multiproceso ni GC de recibos. Pendiente usar recibos y recuperación
explícita en web. Audio/defaults intactos, sin dispositivos ni medios privados.


## Corte 27 · Recuperación web de comparación

Antes de POST, web guarda ruta/entrada/clave en sessionStorage; sin capacidad de
persistir no envía. Ante fallo de transporte conserva el pedido congelado y ofrece
Recuperar comparación R09. Recargar restaura sólo el pendiente, nunca reenvía solo.
Mientras hay pendiente bloquea nuevas publicaciones; recuperar usa misma entrada
aunque cambien controles. Respuesta aceptada limpia pendiente antes de lecturas
posteriores; rechazo 4xx lo limpia. Aplica a streams declarados y conversiones por
IDs. No garantiza retención al cerrar pestaña ni coordinación entre pestañas.

Build completo pasó. Dos pruebas Chrome contra API real aislada pasaron (2,3 s):
ambas rutas aceptan POST y pierden respuesta artificialmente, reintento idéntico
recupera sin duplicar; ruta declarada incluye recarga. Además exportación/reapertura,
presets con descarga/importación y procedencia preservadas. Servidores aislados
apagados. Sin dispositivos/medios privados, audio y defaults sin cambios.


## Corte 28 · Ajuste explícito de reloj desde marcas

POST /api/research/r09/clock-fit y panel web reciben nombres de relojes,
evidence_id, incertidumbre declarada y >=3 pares source_time_s/common_time_s
estrictamente crecientes. Ajuste afín por mínimos cuadrados centrado, tasa válida
(0,2], residuos individuales/RMS/máximo e intervalo de marcas. Incertidumbre es
máximo residuo + incertidumbre declarada, NO límite estadístico ni validación
independiente. evidence_id/pares siguen siendo declaraciones no autenticadas.
Resultado exportable incluye entrada completa; no aplica a streams/live ni guarda
corrida. Extrapolación fuera de marcas no validada. Span numérico extremo rechazado.

Cinco pruebas núcleo/API pasaron (1,01 s) para desfase2s/tasa1.001 conocidos,
repetibilidad, perturbación con residuo .02, evidencia ausente, pares insuficientes/
duplicados, tasa inválida y extremos numéricos. Build completo pasó. Pendientes
Chrome de ajuste/exportación, marcas reales con referencia independiente,
validación reservada temporal y persistencia de resultados. Sin dispositivos ni
medios privados; síntesis/defaults intactos. No es evidencia de exactitud física.


## Corte 29 · Marcas reservadas y Chrome de reloj

validation_anchors opcionales se evalúan con reloj ajustado exclusivamente sobre
anchors. Rechaza tiempos compartidos entre conjuntos y orden inválido. Exporta
residuos por marca, máximo reservado (null sin marcas), count y extrapolated
fuera del intervalo de ajuste. No altera tasa/desfase ni incertidumbre empírica;
reservar marcas no autentica su origen ni demuestra independencia física.
Web muestra número/residuo reservado y JSON completo.

Seis pruebas núcleo/API pasaron (1,02 s): perturbaciones reservadas no cambian
fit/uncertainty, residuo .2 conocido, extrapolación identificada y overlap rechazado.
Build pasó. Chrome real con API aislada pasó (1,3 s), repetido después de ampliar
contrato: offset/tasa conocidos, descarga nativa con entrada completa, edición
limpia resultado y evidencia vacía rechazada; no crea comparación. Ese recorrido
Chrome no incluye marcas reservadas no vacías (verificadas por backend).
Servidores detenidos, sólo datos sintéticos, defaults/audio intactos. Pendientes
medición real, validación con marcas independientes y persistencia del ajuste.


## Corte 30 · Persistencia reproducible de ajustes de reloj

clock-fits POST/GET/artifacts y panel guardan request/result/manifest con hashes,
versión Python/código, binding y recomputación. Lecturas históricas son integridad,
no recomputación actual; no autentican marcas ni sincronización. Recibos persistentes
antes de ejecutar recuperan misma ID tras reinicio; conflicto de clave rechazado.
Web guarda pedido/clave antes de POST en sessionStorage y restaura pendiente sin
envío automático, ofrece recuperación explícita y bloquea nuevo guardado mientras
pendiente. Descargas de tres artefactos y reapertura disponibles. No aplica reloj.

Seis pruebas núcleo/runner/servicio/API pasaron (0,89 s, repetidas tras limpieza de
mensajes): repetición, no overwrite, hash alterado, recomputación alterada incluso
con hash reescrito, binding histórico, recibos/reinicio/exportación. Build pasó.
Chrome contra API aislada pasó (1,6 s): ajuste/exportación, pérdida de respuesta
tras aceptación, reload/reintento idéntico, una corrida y reapertura, input inválido
limpia resultado. Servidor detenido, datos sintéticos únicamente, audio intacto.
Pendientes medición real y aplicación explícita con intervalo/uncertainty a streams;
no coordinación multiproceso, GC de recibos ni retención garantizada al cerrar tab.


## Corte 31 · Aplicación explícita de reloj persistido

POST apply-clock recibe fit_id, Stream y allow_extrapolation(false). Resuelve ajuste
verificado, exige source_clock idéntico, rechaza frames fuera del intervalo salvo
opt-in explícito; devuelve índices extrapolados. Reemplaza sólo Clock, conserva
frames/timestamps/estados/coordenadas tipados y previous_clock, calcula tiempos
comunes y congela ID/hash de manifest. Revalida ajuste al final. No modifica live,
no publica conversión ni autentica nombres/evidencia/calibración. Web ofrece ID,
JSON de stream, opt-in y exportación del resultado para inspección/uso explícito.

Ocho pruebas backend pasaron (1,00 s), build pasó y Chrome real contra API aislada
pasó (2,0 s): guardado recuperable/reapertura, rechazo de extrapolación, opt-in,
descarga con frames/reloj original/procedencia preservados. Primera aserción Chrome
falló por defaults null omitidos en fixture; completada fixture tipada y repetida
sin cambios de comportamiento. Servidores detenidos, sólo datos sintéticos,
audio/defaults intactos. Pendientes medición real, persistencia de streams externos
3D/aplicados y validación temporal independiente; aplicar no mejora incertidumbre.


## Corte 32 · Persistencia de streams externos 2D/3D

Input de conversión admite exactamente conversion MotionFrames o stream declarado;
tracking_provenance sólo con MotionFrames resueltos. Se conserva ruta conversions,
inventario, recibos y selección por ID del comparador. Stream conserva contrato,
frames/unidades/estados, exporta coverage y tiempos comunes; input_kind externo
explícito. Binding de stream y tracking_provenance se verifica también en histórico.
Canonical de recibos de MotionFrames mantiene campos previos (sin stream null)
para no invalidar sus claves. Web guardar stream declarado disponible tras validación
(o sobre resultado existente); reabrir conserva visualización 3D y no ofrece guardar
como MotionFrames. No autentica origen ni convierte metadatos importados en
procedencia verificada. Clock evidence_id persiste como declaración del stream.

Once pruebas núcleo/servicio/HTTP pasaron (1,28 s), otras cuatro de recibos/
biblioteca/API existentes pasaron (0,90 s), build pasó. Chrome con API aislada pasó
(1,9 s): guardar externo con respuesta aceptada perdida, reload/recuperación
idéntica y una conversión, reabrir figura inferred hueca, self-comparison excluye
inferred por defecto y opt-in obtiene soporte1/1/error0. Esto es control sintético,
no precisión 3D. Servidor detenido, sin medios privados/sensores, audio intacto.
Pendientes proveedores 3D reales, calibración/sincronización medidas y conservación
server-resolved de procedencia al persistir una aplicación de reloj (copiar JSON
externo conserva reloj, pero no autentica el vínculo a corrida de ajuste).
