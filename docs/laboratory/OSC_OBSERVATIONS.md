# Observaciones OSC por slot — extensión v2

Estado: contrato e implementación opt-in del receptor; adopción por el motor y
los launchers históricos pendiente. Relación: #77 y R09. No cambia la sesión web
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
monotónica del driver. La adopción requiere un ingreso parcial explícito que
actualice sólo los canales recibidos, conserve identidad/metadatos y valide el
contrato instalado sin confundirlo con el contrato del productor. Derivadas
corporales deben consumir el reloj de captura; scheduling/leases/smoothing de
salida conservan su reloj de operación declarado. No basta pasar
captured_at_us como now_us ni rellenar el snapshot con slots anteriores.

R09 describe observaciones espaciales y procedencia en el laboratorio. Este
evento describe transporte de canales OSC: no crea coordenadas 3D, calibración
métrica, correspondencia entre personas ni un MotionFrame completo de escena.
Un adapter futuro debe declarar pérdidas y conversión; no promover canales OSC
a mediciones espaciales calibradas silenciosamente.

## Verificación

`tests/test_harmocap_observation_events.py` usa fixtures sintéticos de dos cuerpos:
identidad, duplicados, estados, gaps, streams/calibración, expiración, tombstone y
callbacks fallidos. La suite histórica del driver acredita compatibilidad.
Esto prueba software; sincronía física gesto/audio, precisión de pose, HIT y
aceptación humana requieren evidencia independiente.
