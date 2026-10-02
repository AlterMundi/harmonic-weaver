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
