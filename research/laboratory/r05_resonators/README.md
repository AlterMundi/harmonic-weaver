# R05 — núcleo experimental de resonadores

Primer prerrequisito del banco parámetros vs medio excitado (#21). Aislado de
Shaper/live: no instala rutas, abre dispositivos, reproduce audio ni modifica
presets aceptados. API/UI/banco congelado y comparación corporal siguen pendientes.

Núcleo `harmonic_weaver.lab.research.resonators`:

`dz/dt = (iΩ − Γ − gL) z`, L laplaciano de grafo simétrico no negativo.
Cada muestra aplica el impulso explícito antes de un paso exacto `expm(M/sr)`;
la salida por voz es Im(z), y la suma incluye todas las voces. El estado complejo
mantiene fase entre bloques. Una cola sin entrada es actividad del instrumento,
no un evento corporal inventado. `state_norm_squared` no es energía física.

Settings: fundamental_hz (default40.4), ratios (mínimo6/máximo32, default1–6),
sample_rate (8000–96000, default48000), damping_per_s por voz (0–100, default2),
coupling_per_s (0–100, default0), topology isolated/chain/ring/complete/custom.
Custom adjacency simétrica 0–1, diagonal cero, una fila por voz. Frecuencias
positivas bajo Nyquist. No escala/amplitud de excitación ni mapeo corporal se
infiere automáticamente.

Acoplar puede alterar modos efectivos: es una alternativa explícita de
investigación, no promesa de conservar los ratios audibles del instrumento
actual. Topología aislada y coupling0 permiten carriers declarados desacoplados.
No representa aún un medio cimático físico, resonador mecánico ni sensación.

Siete tests comprueban impulso desacoplado contra decaimiento/seno analíticos,
cola, fase idéntica al partir bloques, reset/silencio, norma libre no creciente
con grafo completo y rechazo de contratos inválidos. No validación humana.

Siguientes entregas: excitación causal desde features y comparación con mapeo
de parámetros sobre mismas entradas; política de niveles/latencias/tail explícita;
WAV/manifests, worker/API/UI/presets; pruebas sobre soporte común, estados de voces
vs PCM/figura separados, agencia/legibilidad y controles reservados. No llamar
organización corporal a recurrencia producida por este núcleo.


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

Persistencia inicial: `resonator_run.run(document, request, folder)` valida antes
de crear una carpeta nueva (0700), congela input/request y escribe por bloques
`sum.wav` mono y `voices.wav` multicanal, WAV DOUBLE (float64) sin clipping ni
normalización. Manifest running/complete/failed, hashes de entradas/salidas/código,
Python/NumPy/SciPy/SoundFile/libsndfile/platform, preparación y reloj completo.
Peak, RMS y cantidad de muestras sobre full scale son diagnóstico: amplitudes
mayores que uno siguen intactas; comprobar niveles antes de reproducir. Rehash
de entradas antes del commit final; archivos parciales de fallos no son resultados
completos. No se sobrescribe una carpeta existente. No hay recuperación automática
tras kill, verificador público, worker/API/UI ni comparador de mecanismos todavía.

```sh
PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.resonator_run \
  --input /ruta/local/features.json --request /ruta/local/r05-request.json \
  --output /ruta/local/corrida-r05-nueva
```

Request contiene exclusivamente `resonators`, `excitation`, `render` (objetos
opcionales con defaults descritos arriba). Input es la selección single-signal
congelada, con unidad, filas y procedencia; el CLI no verifica por sí mismo su
relación con un cache corporal original. No usar artefactos sintéticos como
evidencia de movimiento humano. Tres tests nuevos prueban roundtrip PCM exacto,
repetición/hash idéntico con bloques 256/317, suma de voces, niveles, no sobrescritura,
rechazo previo a crear carpeta e invalidación por entrada alterada durante render.
Dieciséis tests R05 pasan; no escucha ni aceptación humana realizada.


R05 — verificador read-only (2026-09-30): `resonator_artifacts.verify(folder)`
requiere manifest complete, inventario exacto, archivos regulares sin symlinks,
hashes antes/después, preparación consistente con entradas congeladas, WAV DOUBLE
con sr/canales/duración exactos, PCM finito y suma de todas las voces exacta.
Recalcula niveles por bloques; tolerancia RMS 1e-12 relativa/1e-15 absoluta por
agrupamiento flotante, pico/conteos exactos. No rerenderiza osciladores ni demuestra
que una falsificación coherente sea auténtica: integridad local sin firma, no
custodia ni evidencia científica. Preparación se comprueba con código instalado;
compatibilidad histórica entre versiones no garantizada.
CLI: `PYTHONPATH=src .venv/bin/python -m harmonic_weaver.lab.research.resonator_artifacts /ruta/local/corrida`.
24 tests R05 pasan, incluidos 8 de verificación: read-only sin cambios, hash,
symlink, manifest no terminado, WAV truncado con hash actualizado, suma alterada
con hash actualizado, niveles y preparación inconsistentes. Worker/API/UI,
recuperación de corridas interrumpidas y comparación de mecanismos pendientes.
Sin cambios a audio live/defaults ni aceptación humana.


R05 — worker/service (2026-09-30): `ResonatorService` inventario separado r05,
misma propiedad/cancelación/close/admisión por instancia R03/R04. Valida y congela
settings antes de encolar; worker one-shot bajo flock, manifest running, render
interno y verificación integral antes de promover WAV/manifest complete. Rehash
de entradas exteriores, hashes worker/verificador. Descargas de entradas o PCM
requieren verificación de todo el resultado; manifest disponible para diagnóstico.
No descarga completa de cancelados; no cancela procesos ajenos/restaurados.
Tres tests propios con procesos reales: completa/restaura/verifica/tamper y no
sobrescritura; render largo cancelado con process.wait confirmado, segunda
corrida rechazada mientras activo, cierre impide nuevos trabajos; contrato inválido
no encola. 27 tests R05 pasan. Sin procesos de prueba vivos al terminar.
Pendientes: endpoints/API/UI/presets, pruebas de interrupción abrupta y carreras
específicas R05, comparación de mecanismos, soporte común y aceptación humana.
No rutas web habilitadas aún, no dispositivos ni cambios al Shaper/live/defaults.


R05 — API y selección replay verificada (2026-09-30): GET/POST /api/research/r05,
POST {id}/cancel y GET {id}/artifacts/{name}. POST selección explícita
{evaluation_id,run_index,signal_id,start_s,end_s}, objetos resonators/excitation/render;
los umbrales/refractario/gap derivan exclusivamente de excitation. Reusa
candidate_snapshot sobre comparador congelado: hashes, persona, unidad, lookahead
cero, timestamps y holds duplicados verificados; sin recalcular tracking ni
trasladar calibración. Lifespan cierra únicamente workers propios.
Integración TestClient con evaluación/pose sintética real (sin mock del reader)
y dos workers: PCM descargado idéntico, 15200 muestras (1.8s+0.1s a 8k), persona
congelada, deduplicación, restore y descargas verificadas. Replay alterado no encola;
PCM alterado invalida toda descarga de resultado; contratos inválidos/ausencia
biblioteca y artefactos no permitidos rechazados. No evidencia corporal humana.
17 tests integración/persistencia/verificador/regresión R03/R04 pasan.
La corrida HTTP detectó timestamp wall-clock en chunk PEAK libsndfile: se fija
ese timestamp a cero antes de hashes, conservando peaks/posiciones y PCM. No usa
APIs privadas ni altera reloj de fuente; RIFF WAV limitado al contrato actual.
Pendientes UI/presets, prueba navegador/red real R05, comparación de mecanismos,
carreras/interrupción abrupta y escucha humana. Audio live/defaults intactos.


R05 — controles web y configuración portable inicial (2026-09-30):
ResonatorPanel en ResearchPanel: elegir comparación terminada/corrida/señal/
segmento con persona/calibración congeladas visibles; todos los campos de
resonators/excitation/render configurables, listas/matriz como JSON, scalar
numérico y modos/topologías por select. Inicio explícito con validación server,
inventario/poll/cancel/descargas y niveles. No reproducción automática de PCM.
POST /api/research/r05/configuration valida preset schema1 sin selección,
fuente/persona/calibración/segmento ni jobs; defaults seis voces. Export/import
JSON preserva selección de origen y no ejecuta. Arrays malformed no encolan.
Build TypeScript/Vite pasa; tres tests API pasan incluyendo integración con
reader real y preset roundtrip/rechazo de source/version/pesos/grafo inválidos.
Interacción navegador R05 todavía no probada: próximo paso harness aislado y
red real; no afirmar aceptación/escucha humana. Comparación de mecanismos,
figura sincronizada para esta variante experimental y experiencias pendientes.
Defaults live/sonido aceptado intactos; controles R05 son offline separados.


R05 — navegador/red real (2026-09-30): harness aislado r05_harness, Chrome
headless contra Uvicorn create_app sobre evaluación/pose sintética congelada;
fetch/endpoints/reader y dos workers reales, sin mocks de API, audio ni cámaras.
resonatorNetwork.spec.ts pasa: configuración seis voces export/import server,
selección señal/persona/segmento conservada al importar (sin jobs), dos corridas
14400 muestras a 8k/1.7s+0.1tail, PCM descargado byte-idéntico, descarga browser
sum.wav terminada sin error. Los primeros intentos corrigieron sólo expectativas
de selector accesible y decimal .3/0.3; no se cambió producto para hacer pasar.
Servidor propio cerrado; no se tocaron servicios del usuario. No prueba de
main/WebSocket/R24 ni escucha/experiencia humana. Pendientes campos extremos/
grafos/contratos inválidos desde browser, carreras/interrupción abrupta, comparación
de mecanismos y figura experimental sincronizada. Audio live/defaults intactos.


R05 — brazo experimental de mapeo de amplitud (2026-09-30): parameter_render
usa la misma selección single-signal, unidad y clocks que resonadores. Mapea
max(0,value)/reference_scale × gain, limitado por max_amplitude, a 6–32
portadoras f1×ratios/pesos explícitos. Attack/release one-pole por muestra,
max_hold_s explícito; expire/missing/crop liberan amplitud. Ceil a muestras no
anticipa observaciones; fases de portadoras continuas por reloj de muestras,
sin reataques al actualizar valor sostenido ni fase corporal inferida. Tail
es liberación del instrumento, no actividad corporal medida.
Exige carriers isolated/coupling0; damping_per_s y missing_policy heredados se
registran explícitamente como no usados. No es núcleo Shaper aceptado ni claim
paridad con live. Sin normalización/limitador/audio dispositivo. Tres tests pasan:
carrier/suma analítica, held/expiry/missing, partición y repetición exactas,
prefijo causal, cola/negativos/contratos. Settings mapping declarados: escala,
gain, max_amplitude, attack/release, max_hold y pesos. Pendientes comparación
persistida de ambos brazos sobre input común, niveles/latencias, UI de este
brazo y evaluación humana. No da por resuelta organización vs instrumento.


R05 — comparación pareada de mecanismos inicial (2026-09-30):
mechanism_compare.compare prepara resonadores excitados y mapeo de amplitud
sobre el mismo documento/clock/sr/f1/ratios/tail; mapeo declara carriers
isolated/coupling0 aunque resonador pueda acoplar. Procesa bloques compartidos,
sin acumular PCM completo. Métricas frames/peak/RMS/full-scale por brazo y
segmento/common_observed/unsupported_segment/tail; diferencia PCM sólo común.
Soporte común: intervalos entre filas válidas adyacentes con gap <= mínimo de
excitation.max_gap_s/mapping.max_hold_s, cuantización ceil, sin cubrir faltantes,
gaps, última observación aislada ni extrapolar. Soporte vacío => None, no cero.
Ganancia sugerida para igual RMS común es diagnóstico, no aplicada; no equivale
a loudness perceptual. Detector/envelope tienen latencias distintas registradas,
no declaración automática de equivalencia. Fases acústicas ≠ fase corporal.
Seis tests comparator/mapping pasan: soporte fragmentado, colas separadas,
actividad sin soporte no convierte undefined en coincidencia, repetición exacta
a misma partición y métricas equivalentes en 256/317 con tolerancia flotante.
No inferencia eficacia/HIT/agencia ni aceptación humana. Pendiente persistencia
pareada/worker/API/UI/niveles/latencias para recorrido humano. Sonido live intacto.
