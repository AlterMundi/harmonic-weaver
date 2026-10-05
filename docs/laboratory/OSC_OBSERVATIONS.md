# Observaciones OSC por slot — extensión v2

Estado: receptor, ingreso parcial al motor y launcher histórico opt-in.
Relación: #77 y R09. No cambia la sesión web
cotidiana, sus fuentes PyAV/HarMoCAP ni los defaults de audio.

## Evento y relojes

`HarMoCAPDriver(on_observation=callback)` emite `ObservationEvent`, versión 2,
con alcance `updated_slot_only`. Un bundle de persona entrega exclusivamente
los canales de ese slot: no es un cuadro completo de escena. No se combina con
`on_frame`; elegir ambos callbacks falla explícitamente. La interfaz histórica
continúa disponible con su snapshot de todos los slots y sus límites originales.

El evento conserva source/stream/slot, contrato y generación/hash de calibración,
captured_frame_id, bundle_seq, captured_at_us, processed_at_us y
queued_for_send_at_us del productor, más received_at_us del receptor. Los tiempos
del productor se etiquetan `producer_monotonic_us_unmapped`; la recepción usa
`receiver_monotonic_us`. No hay conversión entre esos dominios ni medición de
exposición óptica. Cero en los campos del productor se conserva: no se interpreta
como timestamp conocido de exposición ni se sustituye por el reloj receptor.

`slot_update` conserva los estados observed/held/invalid de cada canal.
`slot_invalidated` identifica tombstone, lease_expired, receiver_reset,
stream_changed o cambios de contrato/calibración. Un tombstone conserva su
metadata de bundle; una invalidación local carece de metadata de captura (`null`),
porque no es un nuevo cuadro observado. `to_dict()` permite exportar todos esos
campos sin reinterpretar su reloj. El stream live puede perder cuadros: esa traza
no sustituye el archivo científico con originales, PTS y procedencia por pose.

## Orden, estados y consumo

Bundle_seq crece en el stream; frame_id y capture_time crecen por slot. Dos
personas del mismo frame conservan sus IDs compartidos y producen dos eventos,
sin volver a observar la primera al recibir la segunda. Repetidos/desordenados
se descartan. Expiración y tombstone conservan el watermark para que un paquete
viejo no resucite un slot. Los cambios de stream invalidan los slots anteriores.
El receptor recuerda hasta 64 streams retirados: rechaza sus paquetes tardíos;
ese límite es memoria de sesión, no autenticación ni garantía permanente.
Reset requiere un stream nuevo para reanudar este modo.

`SlotObservationHistory` es un consumidor de referencia para pruebas/research,
no un buffer de audio. Deriva únicamente muestras nuevas observed usando deltas
del reloj productor. Held/invalid interrumpen la derivada; cambios de identidad y
gaps superiores a max_gap_us producen warmup/causa explícita. No rellena gaps ni
calcula velocidad a partir de ticks del receptor. Sus filas deben drenarse o
exportarse por el llamador en una sesión larga.

## Migración y límites del motor

No conectar v2 a `Engine.ingest_driver_frame`: esa función necesita todos los
canales declarados e inventa la secuencia de su adapter. El motor actual también
usa un reloj configurable (por defecto de pared), distinto de la recepción
monotónica del driver. `Engine.ingest_driver_observation(event)` ofrece el ingreso
parcial: exige exactamente los canales declarados para ese slot, verifica rangos
antes de cambiar valores y conserva watermark por slot/identidad. El contrato y
stream del adapter siguen sujetos al gate instalado del engine; la validación
de hello/calibración del productor corresponde al driver. El evento no saltea
esa validación ni autoriza automáticamente un productor nuevo.

La traza `driver_observation_received` contiene el evento completo, incluido su
reloj de recepción, y aparte adapter_stream_id, adapter_contract_id,
adapter_sequence y engine_applied_at_us (`engine_configured_us`). Esa secuencia
interna ordena actualizaciones parciales; no se presenta como captured_frame_id.
Los envelopes y snapshots v2 etiquetan capture_clock y receipt_clock.
Los envelopes held/invalid no reciben una nueva captura válida. No se reemplaza
captured_at_us por now_us ni se rellenan snapshots con slots anteriores.

Para fuentes que entran por este seam, los ticks y bundles de otras personas no
vuelven a muestrear rutas cuyo input usable sigue igual. Las transiciones de
salida pueden avanzar sin recalcular historia corporal. Held conserva el último
target permitido por la política, sin renovar historia de derivada/fase/peaks;
invalid respeta suppress/reset/hold_then_reset y permite completar el release.
Las fuentes y callbacks legacy conservan sus reglas anteriores.

En el harness de ensayo, agregar `--harmocap-events v2` selecciona este callback,
tanto live como con `--replay`. El default es `legacy`, guardado en run_config.
Es una opción de transporte del harness, no un preset del laboratorio corporal.

## Derivada con reloj de captura

El transform `derivative` permite `clock: engine` (default histórico) o
`clock: source_capture`. Stage → Edit chain expone esa elección, `max_abs`,
`max_gap_ms` en modo captura y `max_dt_ms` en modo engine. Guardar la escena
conserva esos campos; cambiar de reloj no modifica los presets sonoros aceptados.

El modo captura divide el cambio de señal por el delta real del productor:
no sustituye timestamps faltantes por llegada/tick ni aplica el clamp temporal
legacy. Exige muestras observed y metadata v2. Para múltiples inputs, todos
requieren el mismo source/stream/contrato/calibración/frame y timestamp. Espera
la pareja alineada antes de actualizar la historia; frames duplicados o atrasados
no cambian su baseline. Una nueva identidad o un gap mayor a `max_gap_ms`
(default 500 ms) inicia con derivada cero. Held/invalid interrumpen la historia.

Falta de metadata o inputs desalineados siguen la política invalid existente,
incluido hold_then_reset sin renovar su plazo. Snapshot/Patchbay explican la
causa mediante `sample_reason`, incluyendo calentamiento por gap/identidad.
El delta de captura no depende del jitter de recepción. Las unidades son las de
la señal seleccionada por segundo del productor, no velocidad corporal métrica
ni una garantía de timestamp óptico. Los filtros que preceden la derivada pueden
seguir usando su propio reloj operativo.

Los aggregators preservan la identidad y timestamp de captura si todos sus
inputs declarados (incluidos los canales de include_when) están observed y
comparten cuadro, identidad y reloj. Esto cubre combinaciones, cadenas de
aggregators y bin_2d. La reevaluación fixed_hz conserva el mismo frame: no produce
un nuevo sample de derivada. Una combinación parcial, held, un predicado de otro
cuadro o un mix de fuentes continúa con su valor numérico habitual, pero sin
metadata de captura común; la derivada source_capture aplica su política invalid.
No se atribuye sincronía a una cohorte que cambia por selección de participantes.

**Pendiente:** tratamiento temporal de los otros transforms y sincronía explícita
entre productores. Un input derivado sin metadata compatible se rechaza en este
modo; no se infiere sincronía entre productores. El opt-in de transporte no certifica replay científico.

R09 describe observaciones espaciales y procedencia en el laboratorio. Este
evento describe transporte de canales OSC: no crea coordenadas 3D, calibración
métrica, correspondencia entre personas ni un MotionFrame completo de escena.
Un adapter futuro debe declarar pérdidas y conversión; no promover canales OSC
a mediciones espaciales calibradas silenciosamente.

## Verificación

`tests/test_harmocap_observation_events.py` usa fixtures sintéticos de dos cuerpos:
identidad, duplicados, estados, gaps, streams/calibración, expiración, tombstone y
callbacks fallidos. La suite histórica del driver acredita compatibilidad.
`tests/test_engine_driver_observations.py` verifica ingreso parcial/gating,
held/invalid/recovery, export de ambos relojes, ausencia de resampling al recibir
otro slot o tick, y ambas modalidades del launcher con bundles OSC reales
sintéticos. Esto prueba software; sincronía física gesto/audio, precisión de pose, HIT y
aceptación humana requieren evidencia independiente.

`tests/test_capture_derivative.py` verifica jitter de llegada, duplicados/orden,
gaps/identidad, ausencia de fallback, inputs alineados y vencimiento del hold.
`laboratory-ui/tests/captureClockStage.spec.ts` verifica guardar y recuperar los
controles contra el Stage API real con fixture sintético aislado.

`tests/test_aggregator_capture.py` verifica combinaciones encadenadas, bin_2d,
frames/tiempos distintos, held/legacy, selección/predicados, y entrega de dos
personas al motor seguida de ticks sin un nuevo cuadro.

## Suavizado en reloj de captura (opt-in)

Además de `derivative`, `smoothing` acepta `clock=source_capture` y
`max_gap_ms` (default 500). Stage permite elegir ambos controles; omitir `clock`
conserva `engine`. One-pole/ramp usan el delta real del productor, independientemente
del jitter de llegada. En este modo `max_dt_ms` no recorta un delta válido;
`max_gap_ms` determina cuándo iniciar una historia nueva. Todos los inputs deben
ser observed y compartir identidad de captura/timestamp; no hay fallback al reloj
operativo cuando falta metadata. Duplicados/atrasos se suprimen antes de modificar
cualquier estado del chain. Tras held/invalid, cambio de stream/calibración o gap,
el primer target inicializa el suavizador, sin interpolar desde datos previos.

Puede encadenarse a una derivada con el mismo reloj. Otros transforms del chain
siguen usando su reloj declarado/default: esta opción no convierte automáticamente
integradores, eventos o clocks de distintos productores. No cambia el filtro
corporal del laboratorio ni presets aceptados. Tests `test_capture_smoothing.py`
y el recorrido Stage verifican cálculo/persistencia; no sincronía física.

## Fase integrada y slew en reloj productor (opt-in)

`phase_accumulator` y `slew_limiter` también aceptan `clock=source_capture` y
`max_gap_ms` (500 default). Stage los ofrece al agregar transforms y muestra
wrap/límite de fase opcional, rate de slew, reloj y gap/delta. Engine sigue siendo
el default; los cambios de chain activan una historia nueva mediante el mecanismo
existente de escena. Cada transform requiere inputs observed alineados y avanza
una sola vez por captura; `max_dt_ms` limita sólo el modo engine.

En captura, fase integra la velocidad actual (deg/s) con delta productor y wrap.
Tras pérdida/época/gap, empieza en cero: es origen convencional del integrador,
no fase física medida ni estimación del desplazamiento durante la pérdida. Slew
inicia el primer target sin inventar un intervalo. Held/invalid y cambios de
stream/calibración reinician esas historias; slew engine conserva comportamiento
legacy. Los relojes de otros productores no se convierten por esta opción.
Esto no cambia las fases de los osciladores ni el preset afinado del laboratorio.

`test_capture_phase_slew.py` cubre jitter, duplicados/atrasos, pérdida, gap,
stream, metadata/alineación y validación. Los recorridos Stage verifican opciones,
persistencia, vuelta al reloj engine y quitar el límite opcional de fase.

## Eventos en reloj productor (opt-in)

`beat_envelope`, `peak_detector` y `pad_dwell` aceptan `clock=source_capture` y
`max_gap_ms` (500 default). Stage expone sus umbrales, tiempos, niveles y reloj;
beat puede elegir decay fijo o ratio del intervalo entre beats. El modo engine
conserva comportamiento anterior. Decay/refractory/intervalos de commit usan el
reloj elegido; duplicados/atrasos no avanzan estados ni renuevan su baseline.

Tras pérdida, metadata de captura ausente, gap o cambio de stream/calibración,
beat inicia en floor con el primer input como baseline (sin inventar una subida);
peak inicia con dos valores iguales (sin inventar ascenso desde cero). Dwell
inicia en el primer target. No se integra tiempo perdido. Inputs desalineados se
suprimen conservando la última captura común; una segunda llegada del mismo
frame puede completar el conjunto sin borrar aquella historia. No se establece
sincronía entre productores independientes.

`pad_dwell` mantiene su semántica existente: intervalo mínimo desde el último
commit, junto con min_change_ms. No garantiza que el candidato se haya mantenido
estable durante todo dwell_ms; el editor lo etiqueta como intervalo de commit.
La opción de reloj no agrega un debounce de estabilidad ni cambia sonido actual.

`test_capture_events.py` verifica jitter, duplicates/order, warmup, gaps/épocas,
metadata perdida y validación; el editor Stage verifica persistencia y decay
fijo/automático con fixtures sintéticos. Son controles de software, no eventos
corporales confirmados ni sincronía física.
