# Agenda de investigación del laboratorio corporal

2026-09-29. Registro abierto; hipótesis y resultados se conservan por separado.

El instrumento cotidiano permite juego y exploración intuitiva. La evaluación
reproducible aplica después presets congelados a las mismas fuentes. Ninguna
de estas modalidades reemplaza a la otra.

Fuentes originales, preservadas sin reescritura:

- [Propuesta de Anni](sources/PROPOSAL-2026-09-28-hit-performance.md).
- [Interferencia relacional v0](sources/NOTE-2026-09-29-relational-interference-v0.md).
- [Plan](../../docs/LABORATORIO_ROPE_FLOW_PLAN.md).
- [Decisiones vigentes](../../docs/laboratory/DECISIONS.md).

| ID | Pregunta / alcance | Próximo experimento | Condición para avanzar |
|---|---|---|---|
| R01 | HIT y geometría: constraint armónico, recurrencia informativa, carga correctiva; Grassmannianos, positividad/amplituedro y ondas KP | Separar predicciones compartidas de consecuencias específicas de HIT | Representaciones estables y controles; no inferir harmonicidad de compresión |
| R02 | Organización corporal: modos colectivos, geometría global/interna, retardos | Comparar local, angular, relacional y colectivo sobre las mismas tomas | Tracking y timestamps fiables |
| R03 | Jpsh!: preparación, activación y despliegue desde centros variables o múltiples | Marcas humanas frente a candidatos cinemáticos; centros alternativos al core | Comparar anticipación temporal; no confundir precedencia con causalidad |
| R04 | Interferencia: refuerzo, oposición, transformación y variación compatible | Rotación uniforme, inversión y oposición local que favorece al conjunto | Continuidad con issue #6; umbrales/mapeos editables |
| R05 | Sonificación: parámetros vs medios/resonadores excitados | Mismo movimiento con ambos mecanismos | Distinguir organización corporal de organización agregada por instrumento |
| R06 | Activación HIT: consulta no bloqueante, phi y alternativas | Perturbaciones racionales, phi, otras irracionales y aleatorias con condiciones comparables | Un medio y observable definidos; hipótesis, no privilegio asumido |
| R07 | Dibujo→sonido→Lissajous/cimática: semejanza vs información preservada | Recuperar atributos reservados desde señales/figuras y controles | Diferenciar estado de voces, PCM y medio físico |
| R08 | Cuerda: trayectorias, cruces, propagación desde manos | Anotación y segmentación asistida en clips cortos | Calidad verificada; cruces 2D no demuestran nudos 3D |
| R09 | 3D y sensores de movimiento | Comparar monocular con multivista calibrada; IMUs cuando resuelvan incertidumbres | Sincronización, escala y evidencia independiente |
| R10 | Experiencia de practicantes/observadores: placer, disfrute, belleza, agencia | Video solo, sonido solo y ambos; orden/control de niveles | Protocolos y registros subjetivos explícitos |
| R11 | OpenBCI y SNR | Definir señal de interés, ruido/artefactos y controles por condición | Protocolo separado y sincronización; no equiparar un índice EEG con placer |
| R12 | Fisiología/eficiencia: corazón, costo energético, trabajo, rendimiento | Instrumentación apropiada y tareas delimitadas; contrastar belleza y eficiencia | No inferir calorías ni trabajo mecánico de a·v 2D |
| R13 | Transferencia/aplicación: otras tareas/cuerpos, aprendizaje, gimnasia y persona–prótesis | Replicación reservada y luego intervención prospectiva | Límites explícitos; objetivos definidos con cada participante |

Cada experimento añade una nota fechada con fuente, configuración, condiciones,
evidencia, resultado (también nulo/negativo), límites y siguiente pregunta.
Cerrar una issue de software no resuelve automáticamente la pregunta científica.

## Antecedentes primarios

- HIT, capítulos 8 y 10, manuscrito local citado en el plan.
- [Geometrías positivas](https://arxiv.org/abs/1703.04541).
- [Grassmanniano y solitones KP](https://arxiv.org/abs/1106.0023).
- [DMD](https://arxiv.org/abs/1312.0041), [DMD con control](https://arxiv.org/abs/1409.6358).
- [Sonificación por impulsos/modelos](https://doi.org/10.1007/s12193-023-00423-8).
- [EMOKINE](https://doi.org/10.3758/s13428-024-02433-0).
- [GVHMR](https://zju3dv.github.io/gvhmr/), [OnlineHMR](https://tsukasane.github.io/Video-OnlineHMR/).
- [Oscilloscope Music](https://oscilloscopemusic.com/info/about/).

Son líneas relevantes; no una revisión sistemática ni evidencia nueva a favor de HIT.


## Bancos implementados, sin cierre científico

R01: [primer banco sintético de subespacios y predicción](r01_grassmann/README.md),
configurable por web/CLI y basado en estimador colectivo de producción. Evidencia
sintética real/repetida, controles y límites preservados. Incluye soporte pareado
entre controles y horizontes configurables con forecasts congelados en su origen.
Incluye entrada de features desde comparaciones congeladas, con unidades,
procedencia, deduplicación y gaps explícitos; repetición corporal local sin publicar
datos privados. Falta comparación amplia entre familias de predictores y
predicción específica HIT. R01 sigue abierto;
R02–R13 conservan sus experimentos/dependencias de esta agenda.

R02/R03 — 2026-09-30: el estimador de propagación de producción empareja objetivos
antes de calcular mejora frente a historia propia. Control reproducible en
`tests/test_lab_collective.py`: predictores idénticos con disponibilidad desigual
no producen una ventaja falsa. `tests/test_lab_propagation.py` conserva control de
retardo sintético conocido y dirección inversa débil. Falta banco ampliado por
web, comparación de modelos/cuerpos y anotaciones humanas de preparación/Jpsh;
estos controles de software no demuestran intención ni causalidad.


R03 — anotaciones humanas tipadas (2026-09-30): el control web de marcas ofrece
nota libre (default), preparación/despliegue/liberación percibidos y experiencia.
El evento mark conserva contexto existente (fuente/persona/calibración/preset,
revisión y tiempo de fuente observado), annotation_category, origen human_button
y reaction_latency_corrected=false. Es el momento del botón y del último estado
observado, no un onset físico ni ground truth de intención. Sigue pendiente
revisión temporal offline, intervalos/incertidumbre y comparación reproducible
contra candidatos cinemáticos con soporte común y controles reservados.


Marcas congeladas: GET /api/marks/snapshot y enlace web descargan todos los
eventos mark hasta through_sequence, con sequence/event y content_sha256. Hash
es SHA256 de JSON sin content_sha256, sort_keys=True, separators=(",",":"),
allow_nan=False, encoding UTF-8 (escape Unicode por default Python). IDs de
sesión permanecen por evento; no se atribuye historial a la sesión recién abierta.
Incluye marcas históricas/sistema: filtrar annotation_origin para anotaciones
humanas tipadas. Texto/contexto privados, descarga sólo local. Pendiente selección
por fuente/persona/segmento y banco de contraste con candidatos.


La descarga de marcas admite source_id/person_id exactos y registra selection
en el contenido hasheado. La UI ofrece export de fuente/persona seleccionadas
cuando ambas identidades existen, además del historial completo. No migra ni
reetiqueta anotaciones entre cuerpos; IDs de tracking no demuestran identidad
biométrica. Mantiene cursor de historial incluso con selección vacía. Selección
por segmento/categoría y contraste cinemático siguen pendientes.


Filtros web/API de marcas: start_s/end_s opcionales delimitan [inicio,fin);
categoría opcional selecciona annotation_category exacta sin atribuir categorías
a marcas antiguas. Tiempos no finitos/negativos o intervalo invertido rechazados.
Marcas con tiempo desconocido no entran en selección temporal. La selección
completa se incluye en content_sha256. No deshace loops: marcas de diferentes
vueltas pueden compartir source_time_s; sesión/revisión/secuencia permanecen
por evento y el contraste deberá seleccionar épocas explícitamente.


Marcas nuevas con runtime guardan observed_epoch (último tick), transport_epoch
(actual al botón) y frame_time_s (frame observado). Se capturan bajo locks
runtime→store; un seek pendiente puede mostrar épocas distintas y tiempo de
frame anterior. No inferir alineación nueva de ese frame. Épocas se interpretan
junto al session_id del evento, no son globales entre reinicios. Sin runtime o
marca histórica, datos desconocidos quedan null/ausentes. Pendiente filtro web
por sesión/época y comparación de candidatos sobre soporte temporal común.


Filtro session_id/observed_epoch disponible por API y web, con sesión obligatoria
si se limita época. Selection integra ambos en hash; marcas sin época quedan
fuera del filtro. Siguiente entrega: contraste reproducible de candidatos sobre
features congeladas y anotaciones seleccionadas, con controles y soporte común.


through_sequence opcional en API y campo web permiten repetir la misma selección
tras nuevas anotaciones; omitirlo toma cursor actual. Rechaza cursor negativo o
posterior al journal, cero produce conjunto vacío. Conservar JSON y hash sigue
siendo necesario: cursor identifica un corte de esta base local, no cualquier
otra instalación. Selección fuente/persona/sesión/época/intervalo/categoría se
reaplica explícitamente. No certifica ausencia de cambios externos a SQLite.


R03 — núcleo de coincidencia temporal: lab/research/temporal_match.py compara
eventos con matching monótono uno-a-uno, máxima cardinalidad y mínimo lag
absoluto entre empates. Tolerancia/offset explícitos; soporte común de intervalos
[start,end), sin cruzar gaps. Offset mueve marcas y soporte conjuntamente; no
estima reacción. Métricas precision/recall desconocidas sin denominador. Máximo
500 eventos por lado acota costo cuadrático. Siete controles sintéticos pasan.
Es núcleo preliminar, NO banco completo ni resultado corporal: pendiente carga
verificada de snapshots/targets, identidad/sesión/época, extracción causal de
candidatos configurable, controles temporales, manifests y UI. No inferir
intención/Jpsh ni causalidad de coincidencia temporal.


R03 extracción preliminar: event_candidates.extract_candidates recibe timestamps,
valor/validez, high/low en unidades originales, refractory_s y max_gap_s. Sólo
cruce desde estado armado bajo emite candidato; inicial alto/gap no emite; cruce
suprimido se consume sin reataque diferido. Missing/gap reinicia historia; no
imputa ni inventa soporte temporal. Límite 14400 muestras. Controles de prefix
causal, sostenido, refractario y gaps pasan; falta adapter de features verificadas,
API/UI configurable, controles y manifest reproducible del banco completo.


R03 mark_input.verified_marks comprueba hash/schema/cursor/secuencias y contexto
explícito fuente/persona/sesión/época/categoría/origen humano. Rechaza mezcla de
contextos y marcas durante discontinuidad pendiente. Conserva reloj botón/frame;
no corrige reacción ni certifica autoría. Límite 500 anotaciones. Integra formato
real del snapshot local; adapter de features y banco web/manifest siguen pendientes.


R03 candidate_input.CandidateRequest/candidate_snapshot selecciona una señal
de una comparación congelada, con umbrales/refractario/gap explícitos. Reutiliza
body.snapshot: hashes, persona, unidades, zero lookahead, timestamps y dedup de
holds; no lee ni copia video. Conserva filas inválidas/provenance y genera
candidatos causales. Integración con replay sintético pasa. Pendientes: unir
marcas/features con identidad de fuente verificable (IDs runtime y asset no son
intercambiables), soporte común explícito, controles, worker/manifests y UI.


Vínculo fuente R03: nuevas marcas runtime incluyen source_identity usando el
contrato de captura (biblioteca declarada + hash del cache manifest, sin rehash
del video ni copias). verify_source_binding exige video, media_id equivalente
a cache.media_sha256, cache_key/key, generation y cache_manifest_sha256 iguales
al replay. Históricos sin identidad no se relabelan. Validación del snapshot SHA
es paso previo separado. Pendiente job integrado que ejecute ambas verificaciones
y contraste sobre soporte explícito; ninguna coincidencia de rutas basta.


R03 coincidence.compare_frozen une hash de selección de features, snapshot de
marcas verificado, binding medio/cache y persona. Recalcula candidatos desde
filas y request; soporte conservador sólo entre observaciones válidas consecutivas
separadas ≤max_gap, sin extrapolar final/aisladas. Mark_support debe declararse,
no se infiere de anotaciones. Resultado conserva inputs/contexto/provenance,
parámetros/soportes/matches y hash de contenido repetible. 17 controles de núcleos
pasan, incluido caso integrado sintético. Pendientes worker/persistencia/API/UI,
controles temporales/soporte pareado y experimento corporal; no ciencia resuelta.


R03 corrida local congelada: preparar carpeta nueva con request.json (argumentos
de compare_frozen), marks.json y features.json. Ejecutar
`PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.coincidence --folder /ruta/local`.
Worker lock exclusivo, hashes de entradas antes/después, manifest running/failed/
complete y result.json con hash. No sobrescribe manifest existente. Registra
hashes de módulos R03/Python, no fingerprint completo de dependencias. Dos
directorios sintéticos dan mismo hash resultado. Aún no CLI de preparación,
worker administrado/API/UI/controles ni interpretación científica.


CoincidenceService administra workers R03 en research/r03: congela tres entradas,
registra queued separado del manifest del worker, lista/restaura mediante lock,
y sirve whitelist con hashes de entradas/resultado. Un worker activo por
servicio. Cancel/close sólo procesos propios, completion concurrente preservado.
Prueba de subprocess real y restauración completa pasa, igual SHA a ejecución
directa; descarga alterada/traversal rechazada. API/UI y validación específica
de cancelación/inicios concurrentes pendientes. No comparte inventario R01.


R03 API inicial: POST /api/research/r03 congela CandidateRequest desde el
lector verificado de evaluación y marcas del store con persona/fuente/sesión/
época/categoría y through_sequence explícitos. mark_support es lista de
intervalos [inicio,fin), nunca inferida de botones. tolerance_s (0–10 s) y
mark_offset_s (−10–10 s) son explícitos; offset no se estima. Valida binding de
medio/cache/generación/persona antes de lanzar worker. GET inventario y
artifacts, POST {id}/cancel reutilizan servicio R03; cierre sólo workers propios.
7 tests API/worker pasan: child real, corte de marcas preservado tras append,
restauración al recrear app, descarga idéntica, tampering/whitelist rechazados,
intervalo invertido/persona incorrecta y ausencia de biblioteca rechazados.
Reader replay mockeado en este test HTTP; lector real tiene cobertura separada
y aún falta integración browser/API/replay completa. No audio ni datos privados.
UI R03, controles temporales y experimento humano siguen pendientes.


R03 UI inicial en pestaña Investigación: comparación/corrida/señal, grupos
explícitos de marcas por fuente/persona/sesión/época/categoría, corte congelado
y cobertura JSON [inicio,fin) manual. Configura high/low/refractario/gap/
tolerancia/offset; no deriva cobertura de botones. Actualizar el corte deselecciona
el grupo. Configuración portable sólo settings y signal_id, no contexto humano.
Inventario, cancelar, descargar artefactos y ver precisión/recall/soporte común.
Prueba Chrome aislada pasa: cobertura inválida/ausente y tolerancia fuera de
rango bloquean ejecución; payload conserva contexto/cursor; export excluye
contexto, refresh exige reselección y resultado visible. Build TS/Vite pasa.
API simulada en prueba UI; todavía falta recorrido browser/API/replay real,
controles temporales y aceptación humana. No cambian defaults del instrumento.


R03 integración evaluación→lector real→API→worker: fixture de pose sintética
produce replay causal local en caché CPU explícita. candidate_snapshot real
verifica artefactos, unidades/procedencia y excluye control holds. Marcas
sintéticas ligadas al mismo manifest/cache/generación; no anotación humana real.
Dos POST HTTP producen exactamente mismos bytes de resultado y coinciden con
compare_frozen directo (entrada normalizada: límites float, corte explícito).
Features descargadas iguales al lector. Alterar trace hace fallar otro POST antes
de crear worker; inventario conserva dos corridas. Tres tests integración/API
pasan. Se corrigió referencia de prueba: corte omitido y límite int vs float
son entradas diferentes para hashes; no se relajó el chequeo de igualdad.
Esta prueba usa TestClient, no browser contra servidor de red ni cuerpo humano.
Pendientes browser/API real, cancelación concurrente y controles temporales.


R03 ciclo de vida: 12 tests servicio/worker/API pasan, cinco casos nuevos
con children reales. Cancel queued y running deja cancelled, close deja
interrupted y confirma proceso terminal; hashes de entrada se preservan,
resultado inexistente no se descarga. Cancel de completed preserva output;
cancel repetido es idempotente. Instancia restaurada no cancela procesos ajenos
ni altera estado. Dos threads con barrera contra un mismo servicio admiten
un solo child; después de cancelar admite otro en carpeta nueva. close ahora
marca closed bajo el mismo RLock y rechaza start posterior: evita un child
que escape del cierre. No verifica admisión global entre instancias distintas
ni carrera completion exactamente durante terminate. No hardware/audio.


R03 controles temporales declarados: offsets opcionales (default [], sin
cambio de audio), hasta 16 distintos no nulos ±10 s; suma con offset manual
también limitada. Cada condición tiene métricas disponibles y paired sobre
intersección idéntica del soporte de todas las condiciones, sin puentes por gaps
ni circular wrap. Cuenta marcas/candidatos elegibles por condición: mismos
segundos no implica mismos denominadores. No optimiza offsets ni calcula
p-values. UI permite JSON de offsets, configuración portable y tabla comparativa.
10 tests núcleo (incluye soporte fragmentado/empty/invalid), API con child real
confirma controles congelados, Chrome panel pasa payload/invalid/export.
17 tests núcleo/worker/API pasan antes de ampliar API a controles; luego 12
núcleo/API y Chrome pasan con controles. Build TS/Vite pasa. No evidencia
corporal/humana ni significación; controles elegidos post-hoc son exploratorios.


R03 browser→HTTP→lector replay→worker completo: Chrome contra Uvicorn
localhost aislado sirve bundle CoincidencePanel con fetch real, sin route mocks.
Fixture pose/cache y marcas sintéticas, sin dispositivos ni medios privados.
Selecciona comparación/señal/grupo, declara cobertura y shifts ±0.1 s, ejecuta
dos workers; resultados iguales byte a byte, tabla de tres condiciones visible,
features.json descarga real con nombre esperado. No errores de API visibles.
No es recorrido completo de main/WebSocket ni escucha/aceptación corporal.
Servidor propio detenido al terminar. Reproducción:

```bash
npx --prefix laboratory-ui vite build laboratory-ui/tests/r03_harness --outDir /tmp/weaver-r03-network-ui --emptyOutDir
PYTHONPATH=src:tests:../harmonic-shaper-dev/src .venv/bin/python tests/r03_http_fixture.py --root /tmp/weaver-r03-fresh-unique --ui /tmp/weaver-r03-network-ui --port 8879
# En otro terminal, desde laboratory-ui:
LAB_R03_NETWORK_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/coincidenceNetwork.spec.ts --reporter=line
```

Root de fixture debe ser nuevo (no sobreescribe); Ctrl+C cierra servicio y
workers propios. Prueba exige endpoint de fixture explícito, no usa lab del
usuario por defecto. Aún pendiente experimento humano y agenda científica R03.


R04 prerrequisito (2026-09-30): RelativeMode de producción valida reloj finito
no negativo y vector 2D finito antes de actualizar historia. Faltante/vector
no válido/tiempo inválido limpian historia, anterior y derivador; no propagan
NaN a observaciones posteriores. Nueve casos inválidos se recuperan tras
warmup fresco; 11 tests existentes modelos/matemática pasan. Sin cambios de
defaults ni síntesis; no prueba interferencia física, técnica ni HIT. Próximo:
banco R04 usando este mismo estimador y controles de rotación/inversión/
oposición, con configuraciones y evidencia reproducibles.


R04 banco sintético inicial: [protocolo y CLI](r04_relational/README.md) usa
RelativeMode de producción en cinco escenarios de Anni con rotación uniforme,
inversión de ambos extremos y velocidad común. Dos tests pasan: invariancia
numérica, frenado contextual, prefijo causal, repetición SHA y no overwrite.
CLI real 30 muestras produce valores declarados en README; son construcciones
sintéticas, no evidencia corporal. Pendientes backend/UI, replay verificado,
oposición local favorable y controles de emparejamiento/ruido/ángulos/humanos.


R04 servicio/API inicial: RelationalService comparte ciclo de vida owned con
R03, pero root research/r04, inputs request.json y whitelist propios. Worker
flock congela hash request, compara tras cómputo, publica result/manifest sólo
con hash confirmado; error deja failed. Inventario restaura por mismo protocolo
de writer lock; close sellado y cancel sólo child propio. POST/GET
/api/research/r04, {id}/cancel y {id}/artifacts/{name}. Dos tests propios
con child real cubren restauración/hash/tampering/whitelist/inventario separado
y HTTP real TestClient; 11 servicio/worker/lifecycle R03 antes de conectar API,
9 R04/R03 API+lifecycle después pasan. No dispositivos/audio. Pendientes panel
R04, browser/red R04, interrupción específica a mitad de cómputo y replay
corporal/control de oposición favorable. No ciencia resuelta.


R04 panel web inicial en Investigación: todos los 10 parámetros del banco
editables, validación de rangos y samples entero, JSON portable importar/exportar.
Inventario/cancel/artifacts/result; traza y muestra seleccionables con valores
I/R/A y velocidades de extremos. Faltantes se muestran indefinidos, nunca cero
ni neutralidad. Prueba Chrome aislada pasa edición sin llamadas/ejecución
congelada/rango inválido/export-import sin ejecutar/resultado faltante. Build
TS/Vite pasa. API simulada en este test UI; backend con child real probado
separado. Pendientes browser→API real R04, entrada corporal y controles ampliados.
No cambian defaults del instrumento ni audio. Vite propio detenido al finalizar.


R04 browser→API→worker verificado por Chrome contra Uvicorn real, sin mocks.
Panel aislado usa fetch same-origin, servidor sin runtime/audio/cámara. Dos
corridas de 30 muestras producen bytes de resultado idénticos; 20 trazas,
request.json descargado con nombre correcto. UI mantiene I/R/A indefinidos
para aceleración compartida; muestra 10 del mismo frenado distal da I=−1
con proximal quieto y +1 con proximal móvil. No errores API visibles. Servidor
propio detenido con shutdown confirmado. No verifica main/WebSocket ni datos
corporales reales; entrada corporal y controles ampliados siguen pendientes.

```bash
npx --prefix laboratory-ui vite build laboratory-ui/tests/r04_harness --outDir /tmp/weaver-r04-network-ui --emptyOutDir
PYTHONPATH=src .venv/bin/python tests/r04_http_fixture.py --root /tmp/weaver-r04-fresh-unique --ui /tmp/weaver-r04-network-ui --port 8879
# Otro terminal, desde laboratory-ui:
LAB_R04_NETWORK_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/relationalNetwork.spec.ts --reporter=line
```

Root debe ser nuevo: fixture nunca pisa inventario previo. Ctrl+C cierra
servicio/workers propios. URL explícita requerida; no usa laboratorio del usuario.


R04 fallos específicos del worker: 8 tests worker/servicio pasan. Requests
mutados en contenido o reemplazados por symlink, resultado alterado y manifest
interno symlink no pueden confirmar output; quedan failed sin result raíz.
Lock ocupado no crea manifest; settings inválidos quedan failed. Child real
produce computed/result, mantiene lock antes del commit externo; inventario
lo conserva running. SIGKILL+wait permite restaurar interrupted con hashes,
idempotente, sin descargar resultado interno ni relanzar. Worker ahora valida
manifest computed regular/no symlink antes de leerlo. No verifica todos los
puntos de crash del filesystem ni hardware; replay corporal sigue pendiente.


R04 entrada de extremos corporal, preparación inicial: EndpointRequest elige
evaluación/run, COCO parent/child distintos y segmento ≤120 s. Lector carga
generación de pose congelada/hash mediante load_source; no copia video ni
recalcula tracking. Exige escala/procedencia de calibración congeladas para
esa persona; Kinematics causal de producción con settings del preset, warmup
desde inicio seleccionado sin preroll inventado. Velocidades T/s, faltantes
explícitos, reloj estricto y límite 14400. Snapshot conserva código de
Kinematics/analysis/contracts, escala/settings/source/cache/preset. Test con
replay sintético real pasa repetición exacta, warmup/gaps/contexto y rechazo
de extremos iguales/fuera de segmento/generación alterada. No medición
corporal nueva ni observación humana; worker/API/UI corporal aún pendientes.


R04 extremos congelados→contrastes→worker/API: start_body congela request e
input.json del lector verificado. Worker incluye ambos hashes y verifica
cambios antes de commit. probe_endpoints usa RelativeMode real en original,
rotación uniforme, inversión de ambos y velocidad común, con relojes/validez/
vectores/unidad/segmento validados. Faltantes reinician historia sin relleno.
Samples/hz sintéticos se declaran unused; no resampling. Resultado conserva
scale/settings/provenance/code y límites. POST /api/research/r04/trace recibe
{settings,selection}; descarga input verificada. Nueve tests integración/
worker/servicio pasan: replay sintético real, dos children con SHA idéntico
y mismo resultado directo, invariancia numérica, HTTP con lector real.
Panel corporal R04 y recorrido browser siguen pendientes. No ejecución corporal
humana nueva ni calibración transferida/audio cambiado.


R04 selección corporal web: comparación/run, COCO proximal/distal, segmento
configurables con persona/escala/procedencia congeladas visibles. Usa settings
relacionales de panel principal, samples/hz no aplican a pose. Bloquea ausencia
de calibración explícita, extremos idénticos y límites fuera de segmento.
No transfiere calibración ni ejecuta al editar. Chrome dos tests panel/panel
corporal pasan payload seleccionado, bloqueos e import/export existentes;
build TS/Vite pasa. Test UI con API simulada; backend lector real/child probado
separado, recorrido corporal browser→API real todavía pendiente. Endpoints
no se incorporan aún al JSON portable; fuente/calibración no se transfieren.
No defaults de audio modificados. Vite propio cerrado.


R04 recorrido de entrada corporal browser→HTTP→lector pose→worker pasa con
fixture de pose sintética real en cache. Chrome elige COCO 7/9, segmento .2–2,
efectúa dos corridas con bytes idénticos; cuatro contrastes, faltantes y
relaciones observadas. Snapshot input.json descargado realmente; UI muestra
persona one/escala/unidad del resultado congelado, no de fuente actual.
API/lector no mockeados, sin dispositivos ni datos corporales privados.
Servidor propio cerrado. No evidencia humana ni main/WebSocket completo.

```bash
npx --prefix laboratory-ui vite build laboratory-ui/tests/r04_harness --outDir /tmp/weaver-r04-body-network-ui --emptyOutDir
PYTHONPATH=src:tests:../harmonic-shaper-dev/src .venv/bin/python tests/r03_http_fixture.py --root /tmp/weaver-r04-body-fresh-unique --ui /tmp/weaver-r04-body-network-ui --port 8879
# Otro terminal, desde laboratory-ui:
LAB_R04_BODY_NETWORK_URL=http://127.0.0.1:8879 PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/relationalBodyNetwork.spec.ts --reporter=line
```

Reusa fixture R03 de evaluación/pose, no inputs privados. Root nuevo requerido.
Extremos portables y controles ampliados de oposición/ruido siguen pendientes.


R04 configuración corporal portable v1: export/import JSON con schema_version,
settings y endpoints COCO. Valida versión/keys/índices/distinción y parámetros
antes de aplicar; no incluye fuente/persona/escala/calibración/segmento.
Importar no corre worker ni cambia selección fuente/segmento. Dos tests Chrome
panel/body pasan recuperación de extremos/settings, segmento preservado y
cero llamadas al editar/importar; build pasa. No aceptación humana ni nuevos
experimentos corporales; controles ampliados y evidencia siguen pendientes.
No cambian defaults de síntesis; Vite propio cerrado.


R04 perturbación local proximal: proximal_multiplier configurable ±4
(default −1 sólo banco investigación; audio intacto). Nueva condición
proximal_scaled transforma únicamente velocidad proximal antes de RelativeMode: 
−1 invierte, 0 detiene, 1 conserva original. Sintético ahora 25 trazas, pose
5 condiciones. No supone pose físicamente posible ni oposición beneficiosa.
Tres tests banco, dos servicio y uno lector real/worker pasan (6 total);
identity multiplier=1 da mismas traces que original, inversión local en
shared_acceleration cambia missing a relación reforzada construida. Controles
globales conservan invariancia; no se exige invariancia local. Dos Chrome
panel/body pasan edición/payload/JSON y build pasa. Network tests actualizados
a nuevos conteos pero no reejecutados en este incremento. Control de tarea/
valor global, ruido/emparejamiento y anotación humana siguen pendientes.


R04 requisito de calibración auditado: evaluación local existente del fragmento
de dos personas/cuerpo indicado está complete pero baseline sin escala ni
procedencia. No se ejecutó R04 real inventando normalización ni se alteró
inventario/calibraciones privadas. Próxima corrida corporal exige calibración
explícita para esa fuente/persona y una evaluación nueva que la congele.
Test de integración nuevo con replay baseline sin escala confirma endpoint
reader y POST /trace rechazan antes de worker; inventario R04 vacío y tabla
de calibraciones idéntica. Dos tests integración pasan, incluido positivo
con escala explícita. Esto no bloquea bancos independientes ni cierra R04.
No publicar IDs/rutas/hashes/medios privados.


R04 ruido reproducible: perturbation_std (0–2, default 0) y
perturbation_seed (0–2147483647, default 0) en API/UI/JSON. Nueva condición
noisy_endpoints añade ruido gaussiano independiente a velocidades preparadas,
no a pose cruda. Sintético usa streams por escenario para conservar prefijos;
pose consume ruido por observación y no vuelve válido ningún faltante.
Ahora 30 trazas sintéticas/6 condiciones pose. Ocho tests banco/servicio/
entrada pasan; añadido test sintético semilla distinta sólo cambia ruido,
misma repite, cero exacto y prefijo causal. Test pose real sintética verifica
ruido repetible, prefijo y faltantes todavía missing; dos tests entrada pasan.
Dos Chrome panel/body y build pasan. Network conteos actualizados pero no
reejecutados aquí. No ruido calibrado de cámara ni estimación de robustez
corporal todavía, ni cambio de audio. Vite propio cerrado.


R04 resúmenes pareados: summarize intersecta timestamps observados exactos
de todas las condiciones y reporta disponibles/pareadas/excluidas, medias
I/R/A y MAE vs original en esa misma muestra. No medios estimados en soportes
distintos. Soporte en segundos sólo entre rows adyacentes en TODAS las
condiciones y dentro de max_gap: no puente sobre fila missing ni extrapolación.
Medias por muestra, no integral temporal. Empty produce None, no cero.
Resultados sintéticos por escenario y de pose incluyen resúmenes/hash de
módulo; panel muestra tabla. Once tests summary/banco/entrada pasan: cinco
nuevos comunes/availability desigual/gaps/empty/invalid, reader real/worker
existentes mantienen repetición. Chrome panel/tabla y build pasan. Tests
network selectores actualizados sin rerun aquí. Estadística descriptiva, no
significación/eficacia ni aceptación corporal humana. Vite propio cerrado.


R04 revalidación network tras controles/resúmenes: Chrome corporal y
sintético contra mismo Uvicorn aislado con std=.02/seed17 pasan; cada
recorrido repite dos workers con resultados idénticos byte a byte. Tablas
noisy_endpoints visibles, settings congelados correctos y denominadores
pareados iguales en resultado de pose. Downloads reales conservados.
Primer intento sintético falló por selector global de indefinidos: nuevas
tablas muestran None legítimos, por lo que se limitó assertion a Muestra R04.
No cálculo cambiado; rerun del test afectado pasa. Servidor y children
propios cerrados. Fixture pose sintética, no evidencia humana ni hardware.
Actuales 30 traces sintéticas y 6 condiciones pose, con proximal/noise.
Reproducir con fixture r03_http_fixture + harness R04 y variables
LAB_R04_NETWORK_URL / LAB_R04_BODY_NETWORK_URL al mismo endpoint8879.


R05 núcleo inicial aislado: resonadores complejos pasivos con pasos exactos
expm, seis voces default (ampliables32), ratios/carriers/amortiguamiento/grafo
configurables por contrato Python. Siete tests impulso analítico, cola libre,
partición de bloques/fase/reset/silencio, norma libre no creciente y invalid
pasan. No audio/live ni parámetros aceptados cambiados. Norma interna no
es energía física; coupling puede cambiar modos efectivos, opción separada
de investigación. [Protocolo](r05_resonators/README.md). Worker/API/UI,
excitación desde features, PCM/figura y niveles/latencias comparables pendientes.
No experimento humano ni claim HIT.


R05 excitación causal inicial: prepare acepta documento de selección
single-signal congelada (compatible CandidateRequest/snapshot verificado),
unidad explícita, settings y sr/nvoices. Modos threshold_crossings (impulso
fijo) y positive_delta (diferencia positiva cruda, no aceleración), gain,
reference_scale/unidad, max_impulse, umbral delta, thresholds/refractario/gap,
6–32 pesos de voces independientes. Eventos sparse con hash input/provenance
y sample_index ceil relativo a inicio: no anticipar observación. Reusa detector
causal R03; primer high y recuperación no reactivan, held no repluck ni
refractario retrasado. Tres tests propios + siete resonadores pasan.
Sin PCM/dispositivo/UI ni niveles normalizados; política de cola, preparación
real por API, comparación de mecanismos y evaluación humana pendientes.


R05 render por bloques: Render prepara excitación sparse y genera voces,
suma cruda y norma interna en memoria limitada al bloque (16–8192). Reloj
segment_frames=ceil(duración·sr), tail_frames=ceil(tail_s·sr), eventos siempre
ceil, fuera del crop no pasan a cola. Policies ring(default) vs reset
configurables: reset en timestamps de invalid/gap detectado, no onset físico
inferido; puede ser discontinuo y no declara ausencia de clicks. Manifest
de preparación conserva clocks/settings/events/resets/procedencia/límites.
Indices sparse por bisección evitan revisar todos los eventos por bloque.
Trece tests render/excitación/kernel pasan; tres de render repetidos tras
optimizar índice mantienen igualdad exacta al partir bloques y reejecutar.
Cola sin nuevas observaciones, ring/reset y silencio/crop exacto verificados.
Sin WAV/PCM persistido, worker/API/UI/comparador/niveles ni aceptación humana.
No se integra al Shaper aceptado ni abre dispositivos.
