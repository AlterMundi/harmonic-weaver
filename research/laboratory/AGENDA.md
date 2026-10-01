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
