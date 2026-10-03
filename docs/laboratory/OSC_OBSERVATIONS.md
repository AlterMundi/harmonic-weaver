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

**Pendiente:** propagación de identidad de captura por canales derivados de
aggregators y tratamiento temporal de los otros transforms. Un input derivado
sin metadata compatible se rechaza en este modo; no se infiere sincronía entre
productores. El opt-in de transporte no certifica replay científico.

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
