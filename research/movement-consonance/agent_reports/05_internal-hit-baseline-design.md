---
project: harmonic-weaver
title: "Consonancia del movimiento en clave HIT — inventario de código y protocolo de experimento baseline"
type: research-report+design
tags: [hit, consonance, movement, harmocap, harmonic-weaver, harmonic-shaper, beacon-spatial, detune, baseline-experiment]
date: 2026-09-24
confidence: mixta — cada afirmación lleva marca ✅ (verificado leyendo el archivo/fuente primaria), 📊 (fuente secundaria), ❓ (inferencia de diseño que requiere aprobación de Nicolás)
---

## 0. TL;DR

- **HIT no define la consonancia como propiedad de un ratio aislado**: la define como *logro relacional de acople estable* — `Consonance = F(ratio, constitución modal, medio, régimen de acople, receptor, contexto)` (✅ manuscrito HIT, L343, L365-367, L399). "Consonancia del movimiento" en términos HIT = dos procesos oscilatorios (la cinemática del cuerpo y el campo armónico del instrumento) que alcanzan **acople estable con bajo conflicto**: la energía cinemática que entra en cada articulación se transfiere sin corrección no resuelta.
- **El inventario de código muestra que el 70% del camino ya existe**: HarMoCAP entrega 17 keypoints COCO × ~30 fps con suavizado One-Euro, estados de validez, tempo/beat_phase globales y grabación .jsonl (✅ `schema.py`, `smoothing.py`, `tempo.py`); el weaver tiene arquitectura de geometría/activación con 13 transforms y 8 operadores de agregación (✅ `compiler.py`); el shaper sostiene 32 armónicos con envolventes por fuente (✅ contrato).
- **El hueco crítico es uno solo y es preciso**: no existe capacidad de **frecuencia por voz a tasa de control** en el contrato del shaper — las voces controladas por envolvente están fijadas a `f1·N` (✅ `state.py` `_set_harmonic_envelope_source_locked`), y el beacon-spatial tiene sus frecuencias de banda **horneadas en el SynthDef** (✅ `beacon.scd` L98). El motor de audio sí puede modular frecuencia por bloque con fase continua (✅ `audio_engine.py` L242, L268-270): falta capability de wire + store + bump de contrato. Sin eso, el detuneo por articulación es imposible.
- **La regla de detuneo propuesta respeta exactamente la serie de Nicolás**: `f'(n,d) = n·f1·(1 + d/(2n))`, `d ∈ [-1,1]` — ±50% del hueco al vecino, que en la serie armónica es siempre ±f1/2 ≈ ±20.2 Hz (simétrico en Hz, asimétrico en cents: de −1200/+702 cents en H1 a −112/+105 cents en H8). Verificado aritméticamente; reproduce los ejemplos 40→20/60 y 80→60/100.
- **COCO-17 no tiene pelvis ni ombligo** (✅ `KEYPOINT_ORDER`): se propone **punto medio de caderas como F0** y puntos virtuales interpolados para "debajo del ombligo"/ombligo. Decisión de diseño marcada ❓ para aprobación.
- **El protocolo baseline es ejecutable hoy con los repos existentes**: video → `run_realtime.py --source video.mp4 --record` → .jsonl → script de métricas offline (nuevo, ~200 líneas) → correlación de Spearman contra ratings humanos ciegos 1-7 (≥3 evaluadores, 2 pasadas). Las 30 fps con pose 2D imponen problemas serios de ruido en derivadas de segundo/tercer orden — cuantificados aquí — que obligan a usar los estimadores con ventana que HarMoCAP ya implementa.

---

## PARTE A — Qué significa consonancia en Harmonic Information Theory

Fuente primaria: `/home/nicolas/Documents/Harmonic_Information_Theory_Foundations_AlterMundi_for-Ai-agents.md` (2754 líneas; todas las citas por número de línea, leídas directamente) ✅. Complemento: registro HMK `[mem:22]` "HIT — Core Ontological Principles" y `[mem:14]` (metadatos del libro), recuperados vía librarian (`hybrid-pack` + `expand`) ✅.

### A.1 El intervalo como portador mínimo

La cadena fundacional del manuscrito es una sola y aparece dos veces (L261 y L2680, esta última como cierre del libro):

> *Una sola frecuencia puede oscilar. Dos frecuencias pueden entrar en relación. De la relación viene la interferencia; de la interferencia, el patrón; del patrón, la posibilidad de una captación diferencial.* ✅ (L261)

El intervalo —`r = f2/f1`, relación proporcional antes que objeto musical nombrado— es el **portador informativo mínimo** porque satisface cuatro condiciones a la vez (L313-325) ✅:

1. **Robustez de escala**: escalar ambas frecuencias por `k` preserva el ratio (L317, y formalizado en H6, L435).
2. **Generación de patrón**: los intervalos producen organizaciones concretas de interferencia — figuras de Lissajous, ondas estacionarias, estructuras cimáticas (L319).
3. **Privilegio dinámico**: en osciladores acoplados, ciertos ratios anclan mode-locking estable con lenguas de Arnold más anchas (Kuramoto; L321, L361).
4. **Interpretabilidad diferencial** (Bateson): un ratio es informativo cuando constriñe el comportamiento de un sistema receptor de modo distinguible de otro ratio (L323).

La definición operativa de información armónica queda entonces: *relación estructurada con capacidad de generar diferencia repetible para un sistema* (L329) ✅.

### A.2 Consonancia como logro relacional, no como propiedad del ratio

El Capítulo 4 (L337-403) es el núcleo para este proyecto. Puntos extraídos literalmente ✅:

- **Fórmula provisoria**: `Consonance = F(ratio, modal or spectral constitution, medium, coupling regime, receiver, context)` (L343). Ninguna cuenta de la consonancia es conceptualmente completa si abstrae la constitución de los modos que interactúan, el medio, la dinámica del receptor y el horizonte en que la relación se encuentra.
- **Contra la esencia aislada del ratio** (§4.1, L347-357): Sethares mostró que la consonancia no la fija el intervalo solo sino su relación con la organización espectral de los cuerpos sonantes; Plomp & Levelt y Helmholtz la explicaron por **interferencia entre parciales** dentro/fuera de bandas críticas. El ratio se retiene sin absolutizarse: es "un atractor de coordinación estructurada, no una esencia autónoma" (L357).
- **Estabilidad dinámica, no perfección rígida** (§4.2, L359-373): "la consonancia puede reformularse como **acople exitoso** en vez de pureza intervalar estática" (L365); "logro relacional de un acople exitoso más que una joya intrínseca escondida dentro de ratios numéricos aislados" (L367). Consonancia ≠ exactitud: una relación es consonante cuando es *suficientemente estable* para sostener organización coordinada y *suficientemente flexible* para absorber perturbación (L371). La desviación acotada puede expresar capacidad adaptativa, no falla (L373).
- **Armonía natural localizada** (§4.4, L387-393): cada sistema físico tiene su propia armonía natural; "local dos veces: local al sistema sonante y local al sistema receptor" (L393).
- **Proposición mínima** (§4.5, L399): la consonancia es *la capacidad de una relación entre procesos oscilatorios, ondulatorios o modales de sostener una organización coherente, de bajo conflicto y diferencialmente interpretable dentro de un sistema concreto*.

### A.3 Eficiencia, sentido y activación — los tres puentes que el modo-consonancia toca

- **Capítulo 8 (L682-758)**: recurrencia informativa → reducción de carga correctiva → la armonía natural como *atractor de eficiencia informacional* (H4). La cadena: ratios simples generan recurrencia; la recurrencia *informativa* (no trivial) economiza corrección (L726, L754) ✅. Esto es exactamente la intuición de Nicolás: "si la aceleración ocurre en una articulación y esa energía es 100% usada por el sistema, es consonante" — traducido a HIT, una articulación consonante es un sitio de **recurrencia informativa con baja carga correctiva**: la energía cinemática pasa a través de ella sin disipación no resuelta ni corrección continua.
- **Capítulo 9 (L762-836)**: el *sentido* de la consonancia como función de orientación; §9.5 (L812-824) la nombra como **acople estructural** en sentido Maturana/Varela: el organismo no recibe información, es perturbado, y la consonancia es el régimen en que el campo perturbador puede integrarse con menor conflicto que alternativas cercanas (L814). H5: los sistemas biológicos poseen sensibilidad funcional a la organización consonante (L445-453). El placer visual que Nicolás propone como criterio ("movimientos que identificamos como consonantes porque nos dan placer visual a través de su eficacia y sensualidad") es una instancia fenoménica de H5 — el afecto como registro de la diferencia entre estados de organización de mayor y menor fricción (L784) ✅.
- **Capítulo 10 (L840-924)**: el problema de la activación — almacenamiento (recurrencia de ratios enteros) vs. recuperación (relaciones no-lockeantes, phi como candidato); el evento *Jpsh!* (L898-902): perturbación breve y bien colocada que **libera** una organización latente sin reescribirla. Relevancia para el diseño ❓: el continuo afinado↔detuneado que propone Nicolás tiene una lectura HIT natural: el modo afinado es el régimen de *almacenamiento* (recurrencia, lock), y el grado de snap/detuneo controla cuánto se aleja el sistema del lock — el extremo máximamente no-lockeante sería el análogo del offset-phi de consulta. No hay que forzar esta analogía, pero el parámetro de snap debería diseñarse sabiendo que existe.

### A.4 Definición explícita: "consonancia del movimiento" en términos HIT ❓ (inferencia de diseño, fundada en A.1-A.3)

Dos procesos oscilatorios entran en relación:

1. **La cinemática del cuerpo**: cada articulación es un proceso cuasi-oscilatorio (sus ventanas de aceleración/frenado son ciclos), y el cuerpo entero tiene un ritmo global medible (`tempo_bpm`/`beat_phase` ya existen ✅).
2. **El campo armónico del instrumento**: la red de parciales `f_n = n·f1` del shaper/beacon.

**Consonancia del movimiento = el régimen en que el acople entre ambos procesos sostiene organización coherente con bajo conflicto**: la energía que la cinemática entrega en cada articulación es *diferencialmente captada* por el armónico asociado sin residuo no resuelto. Operacionalmente: cuando la articulación acelera y esa aceleración se integra limpiamente en el ritmo global del cuerpo (continuidad rítmica, transferencia de energía eficiente a lo largo de la cadena cinemática), el armónico suena **afinado** — el sistema "usa el 100% de la energía". Cuando la articulación es *frenada por resistencia* (potencia mecánica negativa: la energía entra y se disipa sin hacer trabajo), el armónico **detunea hacia abajo**; cuando se *auto-acelera en desfasaje* con el ritmo global (potencia positiva fuera de fase: energía inyectada que el resto del cuerpo no puede absorber), **detunea hacia arriba**. El detuneo no es castigo estético: es el registro audible de la **carga correctiva** que esa articulación impone al sistema cuerpo-instrumento — la magnitud que el Capítulo 8 identifica con la ineficiencia informacional, y que el Capítulo 9 identifica con la perturbación de alto conflicto que un sistema vivo registra como disonancia.

Esto mantiene la separación arquitectónica del weaver: la geometría (qué articulación → qué armónico, y en qué zona del continuo afinado/detuneado está) devuelve **topología**; la activación decide rutas y ganancias — y, para este modo nuevo, también el multiplicador de frecuencia por voz.

---

## PARTE B — Inventario de lo que ya existe en código

Todo verificado leyendo los archivos citados (✅ con ruta y líneas). Nada de lo marcado ❓ existe en código hoy.

### B.1 HarMoCAP — percepción y contrato de movimiento

| Elemento | Verificación |
|---|---|
| `KEYPOINT_ORDER` = COCO-17: nose, left_eye, right_eye, left_ear, right_ear, left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist, right_wrist, left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle | ✅ `/home/nicolas/Projects/HarMoCAP/src/harmocap/schema.py` L40-45 |
| `FEATURE_ORDER` = 24 features (21 + tempo_bpm, beat_phase, tempo_conf); `N_FEATURES = 24` | ✅ schema.py L52-64 |
| `FEATURE_RANGES`: todo [0,1] salvo `verticality` (−1..1) y `tempo_bpm` (0..240 BPM, no normalizado; 0 = desconocido → estado invalid) | ✅ schema.py L67-73 |
| Coordenadas isotrópicas (x_px/frame_h, y_px/frame_h), origen arriba-izquierda | ✅ schema.py L7-9, L97-98 |
| Estados por keypoint/feature: OBSERVED/HELD/INVALID (imputed reservado) | ✅ schema.py L76-81 |
| Suavizado: One-Euro filter causal (mincutoff 1.0, beta 0.15) + máquina de estados hold-last con decaimiento de confianza (timeout 500 ms) | ✅ `src/harmocap/smoothing.py` L19-53, L56-128 |
| Derivadas causales con Δt real de `captured_at`, ventanas en ms: velocity 120 · accel 200 · jerk 300 · qom 400 | ✅ `docs/FEATURES.md` L11-16; `configs/features.yaml` (windows) |
| Normalización espacial por altura de torso T (punto medio hombros ↔ punto medio caderas); posición referida al centro de caderas | ✅ FEATURES.md L17-21 |
| Jerk sólo de **muñecas** (`smoothness_l/r`); aceleración media global (`laban_time_proxy`); energía cinética proxy manos+centro (`laban_weight_proxy`); directness muñecas (`laban_space_proxy`) | ✅ FEATURES.md L58-64 |
| Tempo: autocorrelación normalizada sobre ventana trailing de 6 s, remuestreada a 30 Hz, re-estimación a ~6 Hz; `beat_phase` es acumulador tipo PLL; necesita ~4.5 s de historia y movimiento periódico, si no → invalid | ✅ `src/harmocap/tempo.py` L13-29, L40-44; `docs/INTERFACE_SPEC.md` L58-67 |
| **Advertencia crítica**: lo que mide tempo es tasa de **eventos** de movimiento, no frecuencia de oscilación (un balanceo a 1.2 Hz produce picos a 2.4 Hz) | ✅ INTERFACE_SPEC.md L49-53 |
| Dominio operativo: cámara **fija, ~frontal**, torso ≥ ~15% del alto del frame; fuera de eso las features degradan sin aviso (2D no invariante al punto de vista) | ✅ FEATURES.md L28-33 |
| Grabación .jsonl (una línea JSON por frame, con calibration, feature_order, kp_state, feat_state) vía `--record` | ✅ `scripts/run_realtime.py` L98, L120-123; `src/harmocap/pipeline.py` L182; fixture verificado: `examples/fixtures/two_persons.jsonl` (17 keypoints × 24 features por persona) |
| Privacidad: trayectoria corporal real = dato conductual, NO publicar sin consentimiento; salida a `outputs/sessions/` (gitignored) | ✅ `scripts/record_session.py` L4-7 |
| `--source` acepta índice de cámara **o ruta de video** (offline) | ✅ run_realtime.py L92-93, L118 |
| FPS de captura: cámara C920e empujada a modo rápido 30 fps vía V4L2; el perfil real (backend, resolución, fps) se registra | ✅ `src/harmocap/capture.py` L8-11, L44-46, L67-75 |

**Conclusión B.1**: la telemetría cruda que el modo-consonancia necesita (posición suavizada por articulación, a 30 fps, con estados de validez, tempo global y grabación reproducible) **ya existe**. Lo que NO existe en el wire: velocidad/aceleración/jerk **por articulación** (sólo muñecas y centro) ni fase por articulación. Para el experimento baseline eso no importa: se calcula offline desde los keypoints grabados. Para el modo en vivo habría que extender el feature set (lo que **bumpea `feature_set_version`**, ✅ FEATURES.md L5-7) o computar las derivadas por articulación dentro del weaver con el transform `derivative` (existe ✅, ver B.2).

### B.2 harmonic-weaver — motor de ruteo

| Elemento | Verificación |
|---|---|
| Regla arquitectónica: "Geometry expanders return TOPOLOGY ONLY. They must never emit instrument routes. Activation expanders own routes." | ✅ `src/harmonic_weaver/engine/geometry_toolkit.py` L9-11; `MEMORY.md` L83-86 ("Geometry returns topology only (zone indices) / Activation owns routes and gains") |
| Constantes: `N_SLOTS = 8`, `N_HARMONICS = 32`; source ID `S = slot*2 + hand_side` (16 fuentes) | ✅ geometry_toolkit.py L18-19, L42-52 |
| Operadores de agregación: `mean, sum, min, max, weighted_sum, difference, abs` + `bin_2d` (cols×rows, serpentine opcional) | ✅ `engine/compiler.py` L150 (lista), L1033-1038 (bin_2d) |
| Tipos de transform (13): `scale_range, curve, smoothing, gate, combine, phase_accumulator, slew_limiter, derivative, beat_envelope, radial_velocity, peak_detector, pad_dwell, match_value` | ✅ compiler.py L510-524; semánticas en `docs/CORE_DESIGN.md` L92-108 |
| `gate` tiene **hysteresis** declarativa; `pad_dwell` debouncer con `dwell_ms`/`min_change_ms`; `slew_limiter` persecución a tasa acotada — los tres útiles para el parámetro de snap | ✅ compiler.py L554-568 (gate), L631-643 (pad_dwell), L579-583 (slew) |
| `derivative`: diferencia trailing causal → velocidad firmada, con `window_ms`, `max_abs`, `max_dt_ms` | ✅ compiler.py L584-590 |
| Registry de geometría: **sólo `vertical_bands` registrado** (`_GEOMETRY_EXPANDERS["vertical_bands"]`); pads_v1/v2 son escenas con agregadores explícitos, no expanders | ✅ compiler.py L1251-1254, L1343-1346; escenas en `rehearsal/scenes/` |
| Expander bands: bandas simétricas por slot+mano centradas en nariz X, `band_span` calibrado por HarMoCAP (ancho de hombros × 2.5); kernel delta, magnitude presence; **`kinetic_energy`, `slew` y `gaussian` declarados pero NO implementados** (Phase 2, raise explícito) | ✅ `engine/geometry_bands.py` L53-82, L90-196; MEMORY.md L88-91 |
| Rutas de banda: `match_value` sobre índice de zona → `harmonic_source_envelope` (bindings N=zone+1, S=source_id), ganancia 1/0, validez held=reject, hold 150 ms | ✅ geometry_toolkit.py L236-276 |
| Canales del driver HarMoCAP: por slot `present/focused`, 17 keypoints × (x, y, conf), 24 features + alias `kinetic_energy` (= `laban_weight_proxy`) | ✅ `src/harmonic_weaver/drivers/harmocap_driver.py` L22-28, L110-139, L250-264 |
| Modo offline: `weaver_runtime --replay <jsonl> --scene <scene>` — hardware-free, re-emite la sesión por el codec del kit a ~30 Hz de reloj monotónico, audita salidas en `instrument_outputs.jsonl` | ✅ `rehearsal/weaver_runtime.py` L607-613, L616-745 (pacing L715-716; codec del kit L455-473) |
| **Traba del replay offline**: exige `instrument_writes > 0` **y al menos una escritura `arp_*`**, o falla con SystemExit | ✅ weaver_runtime.py L741-744 |
| Ensayo full-stack sin hardware: `uv sync --extra rehearsal --extra test && ./rehearsal/run_rehearsal.sh` (requiere checkouts hermanos, pw-jack, scsynth, sclang, ATK) | ✅ `rehearsal/README.md` L5-16; `rehearsal/run_rehearsal.sh` |
| Stack en vivo conocido-bueno: `./scripts/start-live-stack.sh --camera 2 --scene bands-v1 --beacon-mute --pads-view harmocap --shaper-device "R24 Analog Stereo"` | ✅ MEMORY.md L39-47 |
| Push de escena en caliente: `PYTHONPATH=src:. python rehearsal/push_scene.py --scene <file> --switch` | ✅ `rehearsal/push_scene.py` L7-16 |
| Estado actual: branch `feat/geometry-activation`, bands-v1 verificado en vivo (172 transiciones armónicas auditadas, 169 tests verdes) | ✅ MEMORY.md L5-26; BITACORA.md (entradas 2026-09-21/22); branch verificada con git |

**Cómo se enchufaría un modo-consonancia** ❓ (diseño, respetando la regla verificada arriba): un expander de geometría nuevo (`consonance_body` o similar) que devuelva *topología*: (a) agregadores que calculen, por slot y por articulación de la tabla C.1, el índice de armónico (constante por articulación → zona) y un índice de zona de detuneo (bin de `d_j` cuantizado); (b) metadata `zone_layout`. La capa de activación poseería las rutas: presencia → `harmonic_source_envelope` (ganancia, como hoy) **más** rutas nuevas de detuneo hacia una capability de frecuencia-por-armónico que todavía no existe (ver B.3). La evidencia de que el patrón "geometría devuelve índices, match_value rutea" ya funciona en producción es bands-v1 ✅.

### B.3 harmonic-shaper — sintetizador aditivo

| Elemento | Verificación |
|---|---|
| Red armónica: `DEFAULT_F1 = 40.40 Hz`, `N_BANDS = 32`, `F1_MIN/MAX = 20/200`, `MAX_VOICES = 32` | ✅ `src/harmonic_shaper/config.py` L14-18 |
| Motor de audio: seno por voz con `params.freq` leído **por bloque** (256 muestras @ 44.1 kHz ≈ 5.8 ms) y **fase continua entre bloques** (`state["phase"] = carrier_phases[-1] + 2π·freq/fs`) → la frecuencia por voz ES modulable a tasa de control-bloque sin discontinuidad de fase, mecánicamente | ✅ `audio_engine.py` L240-243, L268-270; config.py L9-10 |
| **Pero**: las voces nativas por envolvente tienen la frecuencia **fijada a `f1·N`** en cada activación (`voice.freq = self.f1 * harmonic_n`) | ✅ `state.py` `_set_harmonic_envelope_source_locked` (L384-385) |
| Control global de f1: `update_f1` y `set_vsrate` (0.1..4.0) existen en el store, pero **no están expuestos en el namespace `/digital`** — `set_vsrate` no es alcanzable desde OSC nativo ni desde la API HTTP (grep: cero llamadas fuera de state.py); `/beacon/f1` sólo vía slave broadcast | ✅ state.py L335-351; `osc_receiver.py` L93-94, L139-164; `api.py` L98-196 |
| Capabilities del contrato (24): harmonic gain/envelope/trigger/source_envelope/pan/phase, master, ceiling, clock_bpm, settle_beats, generator_enable, arp_* (8), perc_* (4), panic. **No existe ninguna capability de frecuencia/detuneo por armónico** (grep "detune"/"cents" en el contrato = 0) | ✅ `contracts/shaper.contract.json` (parseado: lista completa de 24 capabilities) |
| API HTTP por voz: gain, pan, phase_deg, attack_s, release_s, shape, lfo_gain, lfo_pan, lfo_phase — **sin freq** | ✅ api.py L181-191 |
| LFO global: rate divisor, waveform (sine/tri/saw/square/samplehold), amount, y destinos gain/pan/phase — modula ganancia/paneo/fase, **no frecuencia** | ✅ state.py L1191-1266; audio_engine.py L232-237 |
| Envolvente por fuente: 16 sources (0..15) por armónico, ganancia audible = máx de fuentes activas, una sola voz seno por armónico | ✅ state.py `set_harmonic_source_envelope`, osc_receiver.py L198-205 |
| `/beacon/voice/freq` (slave) sí mueve frecuencia por voice_id — pero pertenece al ciclo de vida de voces del beacon externo, no a las voces nativas por envolvente que el weaver controla | ✅ osc_receiver.py L93, L123-125; state.py L327-333 |

**Veredicto sobre la pregunta clave (¿se puede modular FRECUENCIA por voz a tasa de control?)**: el motor de audio **puede** (bloque a bloque, con fase continua ✅); el store tiene el punto de escritura (`VoiceParams.freq` ✅); lo que **falta** es el camino completo de control ❓→implementar: (1) capability nueva en el contrato (p.ej. `/digital/harmonic/{N}/detune` con rango en cents o como multiplicador), (2) handler en `osc_receiver.py`, (3) lógica en `state.py` que aplique el multiplicador **sin** que `_set_harmonic_envelope_source_locked` lo sobrescriba con `f1·N` (hoy lo pisa en cada reactivación), (4) bump de `contract_id` + manifiesto en el weaver + safety default (0 cents) en el safety profile, (5) opcional: suavizado por slew dentro del store para evitar zipper noise entre bloques. Es un cambio acotado (~100-150 líneas + tests), pero **toca el contrato**, así que exige coordinación con los golden files (`contract_id.golden`).

### B.4 beacon-spatial — espacializador SuperCollider

| Elemento | Verificación |
|---|---|
| 12 BPF + 1 HPF con frecuencias centrales **literales** en el build del SynthDef: `[40, 80, 120, 160, 200, 240, 480, 720, 960, 1200, 1440, 1680, 1800]` Hz — serie 40·n para n=1..6 y luego 480·m | ✅ `beacon.scd` L97-98, L142-150 |
| Controles por banda en tasa de control (.kr con lag 0.05): gain, az, dist, solo, q (RQ) + mix/master globales. **No hay control de frecuencia central por banda** | ✅ beacon.scd L119-139, L398-449 |
| Contrato (9 capabilities): band_gain, band_azimuth, band_distance, band_solo, band_filter_rq, wet_dry_mix, master_gain, nature_load, nature_gain | ✅ `beacon_spatial.contract.json` (parseado) |

**Consecuencia de diseño** ❓: el detuneo debe vivir en el **shaper** (síntesis aditiva, donde cada voz tiene frecuencia propia), no en beacon-spatial (filtrado de una fuente fija, donde las frecuencias de banda son estructurales). En el stack en vivo actual el shaper es de todos modos el instrumento que el weaver usa para las rutas armónicas del cuerpo (bands-v1 → `harmonic_source_envelope` del shaper ✅ MEMORY.md L33-37). Las frecuencias de banda del beacon (40/80/120/160/200/240...) coinciden con la serie de Nicolás — útil como referencia espectral del campo, pero no como destino del detuneo.

### B.5 Tabla síntesis: capacidad | dónde vive | qué falta

| # | Capacidad | Dónde vive (✅) | Qué falta (❓ = a implementar) |
|---|---|---|---|
| 1 | Keypoints 2D COCO-17 por slot, suavizados, con estado, ~30 fps | HarMoCAP `schema.py` L40-45, `smoothing.py`, `pipeline.py` | Nada para offline. Para vivo: nada (ya viajan por OSC y por el driver del weaver, `harmocap_driver.py` L250-264) |
| 2 | Derivadas por articulación (v/a/jerk de las 17) | Sólo muñecas/centro: `FEATURES.md` L56-64; `features.py` (ventanas L186-206) | Métricas por las 17 articulaciones: offline desde keypoints grabados (baseline) ❓; en vivo, o extensión de features (bump de `feature_set_version`) o transforms `derivative` encadenados en el weaver ❓ |
| 3 | Ritmo global (tempo_bpm, beat_phase, tempo_conf) | HarMoCAP `tempo.py`; wire ✅ `schema.py` L62 | Acople de fase **por articulación** (PLV vs beat_phase): no existe en ningún repo ❓ — se computa offline en el baseline |
| 4 | Grabación/reproducción determinística de sesiones | `run_realtime.py --record`; `harmocap-nico-kit/replay.py` (timing de captura, L8-12); `weaver_runtime --replay` (L607-613) | El gate del replay offline exige escrituras `arp_*` (weaver_runtime.py L741-744) — una escena consonance sin rutas arp **fallaría ese assert**; hay que relajarlo o incluir una ruta arp ❓ |
| 5 | Mapeo articulación→armónico (topología) | Patrón probado: `geometry_bands.py` + `geometry_toolkit.py` (bin_2d + match_value) | Expander de geometría nuevo (`consonance_body`) con la tabla C.1; registry hoy tiene sólo `vertical_bands` (compiler.py L1343-1346) ❓ |
| 6 | Ganancia por armónico y por fuente (16 fuentes) | Shaper `harmonic_source_envelope` ✅ contrato + `state.py`; en vivo verificado (MEMORY.md L16, L33-37) | Nada |
| 7 | **Frecuencia por voz a tasa de control (detuneo)** | Motor: `audio_engine.py` L242, L268-270 (bloque+fase continua); store: `VoiceParams.freq` | Capability de wire + handler OSC + store que no sea pisado por `f1·N` + bump de contrato + safety default + slew ❓ — **el hueco crítico** |
| 8 | Frecuencia de banda en beacon-spatial | `beacon.scd` L98 (literales en SynthDef) | No modulable en tasa de control; se descarta como destino del detuneo ❓ (decisión: detuneo sólo en shaper) |
| 9 | Snap/histerias/debounce de parámetros discretos | Weaver transforms `gate(hysteresis)`, `pad_dwell`, `slew_limiter` ✅ compiler.py L554-568, L631-643, L579-583 | Composición concreta para el grado de snap ❓ (C.3) |
| 10 | Código de métricas de consonancia | **No existe** (grep `consonan` en los 4 repos: sólo "consonants" del vocoder del shaper) | Todo: script de análisis offline + escena + capability ❓ |

---

## PARTE C — Boceto de diseño operativo + protocolo del experimento baseline

Todo lo de esta Parte es **propuesta de diseño ❓** salvo donde se cita código verificado ✅. Las fórmulas son nuevas; los convenios (ventanas, unidades, coordenadas) heredan deliberadamente los de HarMoCAP para que el baseline sea comparable con el sistema en vivo.

### C.1 Mapeo anatómico articulación → armónico

**El problema**: Nicolás propuso "F0 en la pelvis, F1 debajo del ombligo, hacia arriba". COCO-17 **no tiene punto de pelvis ni de ombligo** (✅ `KEYPOINT_ORDER`, schema.py L40-45: sólo `left_hip`/`right_hip` como referencia del tronco bajo).

**Resolución propuesta** ❓: **punto medio de caderas (`hip_mid = (left_hip + right_hip)/2`) como F0/H1**, y puntos virtuales de línea media interpolados entre `hip_mid` y `shoulder_mid = (left_shoulder + right_shoulder)/2` para "debajo del ombligo" (⅓ del camino) y "ombligo/boca del estómago" (⅔). Esto es coherente con HarMoCAP: su propia normalización espacial ya define el torso como punto-medio-hombros ↔ punto-medio-caderas (✅ FEATURES.md L17-21), y `verticality` ya usa esos dos puntos medios (✅ FEATURES.md L60).

**Principio de asignación** ❓: la línea media sube por la serie (la regla explícita de Nicolás); las extremidades se ramifican hacia parciales más altos por **distalidad** — analogía espectral directa: los segmentos distales (muñecas, cabeza) son los que portan el contenido cinemático rápido, como los parciales altos portan el detalle fino de un timbre. Pares simétricos **comparten armónico** (precedente: bands-v1, ambas manos → mismo armónico, ✅ MEMORY.md L88-90).

| Armónico | Articulación / punto | Fuente COCO-17 | Nota |
|---|---|---|---|
| **H1 (F0)** | Pelvis | `hip_mid` = (left_hip + right_hip)/2 | virtual; ancla de la serie ❓ |
| **H2 (F1)** | Debajo del ombligo | virtual: `hip_mid + ⅓·(shoulder_mid − hip_mid)` | literalmente "F1 below navel" ❓ |
| **H3** | Ombligo / abdomen alto | virtual: `hip_mid + ⅔·(shoulder_mid − hip_mid)` | ❓ |
| **H4** | Hombros / esternón | `shoulder_mid`; left_shoulder, right_shoulder lo ponderan | par simétrico compartido ❓ |
| **H5** | Cabeza | `nose` (cluster: left_eye, right_eye, left_ear, right_ear promediados con peso por confianza) | ❓ |
| **H6** | Rodillas | left_knee, right_knee (compartido) | rama descendente ❓ |
| **H7** | Tobillos | left_ankle, right_ankle (compartido) | contacto con el suelo; en artes marciales es la raíz de la cadena cinética ❓ |
| **H8** | Codos | left_elbow, right_elbow (compartido) | ❓ |
| **H9** | Muñecas | left_wrist, right_wrist (compartido) | lo más distal = parcial más alto ❓ |

Los 17 nombres COCO-17 quedan cubiertos (los 4 puntos faciales se pliegan al cluster cabeza). 9 armónicos ≤ `N_BANDS = 32` del shaper ✅ y ≤ `N_HARMONICS = 32` del weaver ✅.

**Alternativas documentadas para la decisión** ❓: (B) altura vertical pura en pose de referencia — tobillos=H1, cabeza=H17: viola "F0 en la pelvis"; (C) distancia de cadena cinemática pura desde pelvis (rodillas=H2, tobillos=H3, muñecas≈H5-H6 por la cadena cadera→columna→hombro→codo→muñeca): respeta F0-pelvis y el flujo de energía suelo→pelvis→extremidades de las artes marciales, pero interlea piernas y columna. **Requiere aprobación de Nicolás**: la recomendada es la tabla de arriba (línea media H1-H5 + ramificación distal H6-H9), con la nota de que rodillas/tobillos podrían bajar a H2/H3 si se prefiere la lectura de cadena cinética.

### C.2 Consonancia por articulación desde keypoints 2D a 30 fps

Notación: `p_j(t)` = keypoint isotrópico suavizado (One-Euro ✅) de la articulación j; `T` = altura de torso ✅; ventanas trailing causales `W_v = 120 ms`, `W_a = 200 ms`, `W_j = 300 ms` (las de HarMoCAP ✅ configs/features.yaml); `Δt` = tiempo real entre extremos de ventana (nunca índices de frame ✅ FEATURES.md L11-14). Todo causal, todo en unidades de torso.

**Métricas base** ❓ (fórmulas nuevas, convenciones heredadas):

1. **Velocidad** (vector): `v⃗_j(t) = (p_j(t) − p_j(t−W_v)) / Δt_v / T`  [T/s]
2. **Aceleración** (segunda diferencia con ventana): `a⃗_j(t) = (v⃗_j(t) − v⃗_j(t−W_a)) / Δt_a / T`  [T/s²]
3. **Jerk** (tercera diferencia): `jerk_j(t) = ‖a⃗_j(t) − a⃗_j(t−W_j)‖ / Δt_j / T`  [T/s³]
4. **Potencia mecánica firmada** (el discriminador freno/bomba de Nicolás): `P_j(t) = ⟨a⃗_j(t), v⃗_j(t)⟩`. `P_j < 0` = la articulación está siendo **frenada** (resistencia absorbe energía → candidato a detuneo bajo); `P_j > 0` = se **auto-acelera** (inyecta energía → si además está desfasada del ritmo global, candidato a detuneo alto).
5. **Fracción de frenado**: `brake_j = Σ_t |P_j(t)|·𝟙[P_j<0] / Σ_t |P_j(t)|` sobre ventana de 1 s.
6. **Acople rítmico global** (coordinación contra el ritmo del cuerpo): sea `φ_j(t)` la fase de la envolvente de rapidez `‖v⃗_j‖` (vía Hilbert o vía tiempos de pico) y `φ_B(t) = beat_phase(t)` la fase global que ya entrega HarMoCAP ✅. `PLV_j = |⟨exp(2πi·(φ_j − φ_B))⟩|` sobre ventana de 6 s (= ventana del estimador de tempo ✅ tempo.py L40). `PLV_j → 1` = la articulación bloquea fase con el ritmo global (continuidad rítmica); `→ 0` = desacoplada. Gatear por `tempo_conf` y excluir tramos con tempo invalid (✅ INTERFACE_SPEC.md L60-62). **Precaución verificada**: tempo mide tasa de eventos (el doble de la frecuencia de oscilación ✅ INTERFACE_SPEC.md L49-53) — por eso la referencia es `beat_phase` directamente y no una frecuencia derivada.
7. **Eficiencia direccional**: `straight_j = desplazamiento neto / longitud de camino` sobre 300 ms (generalización de `laban_space_proxy`, que hoy sólo se computa para muñecas ✅ FEATURES.md L64).
8. **Suavidad**: `smooth_j = 1/(1 + jerk_j/jerk_ref)` con `jerk_ref = 40` (fallback de calibración ✅ configs/features.yaml).

**Proxy de consonancia por articulación (la magnitud objetivo)** ❓:

```
C_j = clip( w_P·(1 − brake_j) + w_φ·PLV_j + w_s·straight_j + w_m·smooth_j , 0, 1 )
```

con `w_P + w_φ + w_s + w_m = 1`. **Los pesos NO se fijan a priori: se calibran contra los ratings humanos del protocolo C.4 — ese es exactamente el experimento baseline** ("medir la matemática de eso"). Interpretación HIT: `C_j` alto = la energía de la articulación es diferencialmente captada por el sistema (recurrencia informativa, baja carga correctiva, A.3); `C_j` bajo = conflicto no resuelto.

**Drive de detuneo por articulación** ❓:

```
d_j = clip( k·(brake_j − max(0, pump_excess_j)) + m·errφ_j , −1, +1 )
```

donde `pump_excess_j` = fracción de potencia positiva **fuera de fase** con el beat, y `errφ_j ∈ [−1,1]` = error de fase circular normalizado `(φ_j − φ_B)`. Signo: frenado por resistencia → `d_j < 0` → detunea bajo; auto-aceleración desfasada → `d_j > 0` → detunea alto. (La forma exacta —si `errφ` entra con signo propio o modula sólo el término de bombeo— es parte de lo que el baseline debe discriminar.)

**Problemas de ruido/jitter a 30 fps con pose 2D** (cuantificados en esta sesión con σ_pos ≈ 2 px, torso T ≈ 200 px ⇒ σ ≈ 0.01 T; aritmética verificada con Python):

- **Nyquist = 15 Hz**: oscilaciones de miembro rápido (golpes de arte marcial) se acercan al límite; el jerk de eventos balísticos queda submuestreado. Aceptar: las métricas describen el régimen rítmico (0.5-5 Hz), no los transientes balísticos. ❓
- **Amplificación de derivadas**: segunda diferencia frame-a-frame de una señal con σ = 0.01 T da ruido ≈ √6·σ/Δt² ≈ **22 T/s²** — del orden o mayor que las aceleraciones reales (~1-10 T/s²). Tercera diferencia: ≈ √20·σ/Δt³ ≈ **1200 T/s³**, inutilizable. Con estimadores con ventana (120/200/300 ms, los de HarMoCAP) el ruido baja a ~0.12 T/s (vel), ~0.8 T/s² (acel), ~4 T/s³ (jerk): usable **sólo** con ventana. Por eso las fórmulas C.2 heredan las ventanas del repo ✅ y no se proponen derivadas frame-a-frame.
- **Estados held**: durante oclusión la máquina de estados retiene coordenada (hold-last ✅ smoothing.py L118-126) → las derivadas leídas sobre held dan cero = "suavidad" falsa. Regla: las métricas por articulación se computan **sólo sobre frames OBSERVED**, y `C_j` se marca invalid si la fracción observed de la ventana cae bajo un umbral (0.7 ❓).
- **Tempo inválido**: cuerpo quieto o no-periódico → las 3 features de tempo llegan invalid (✅ INTERFACE_SPEC.md L60-62) → PLV indefinida. El protocolo excluye esos tramos del agregado.
- **2D no es invariante al punto de vista** (✅ FEATURES.md L30-33): el corpus debe ser cámara fija ~frontal; con vista lateral fuerte, `straight_j` y la simetría pierden sentido.
- **Normalización por torso**: usar siempre unidades T (invariancia a distancia/tamaño ✅ FEATURES.md L17-21) — los pesos de C.2 ya lo asumen.

### C.3 Regla de detuneo formalizada

Serie: `f_n = n·f1`, n = 1..32, `f1 = 40.40 Hz` (DEFAULT_F1 del shaper ✅ config.py L14; la serie 40/80/120 del ejemplo de Nicolás coincide con la región ya explorada del beacon ✅ `beacon.scd` L98).

**Límite del detuneo (la regla del 50% del paso al vecino)**: el hueco entre armónicos vecinos es uniforme, `f_{n+1} − f_n = f1`; hacia abajo desde H1 el ejemplo de Nicolás ("40 puede ir a 20") fija el límite inferior en `f1/2`, i.e. el mismo hueco `f1` medido hacia el sub-armónico. Con `d ∈ [−1, +1]`:

```
f'(n, d) = f_n + (d/2)·f1  =  n·f1·(1 + d/(2n))
```

que reproduce exactamente los ejemplos: n=1 (40 Hz): d=−1 → 20, d=+1 → 60 ✓; n=2 (80): d=−1 → 60, d=+1 → 100 ✓.

**Como multiplicador (ratio)**: `r(n,d) = 1 + d/(2n)`, acotado a `[1 − 1/(2n), 1 + 1/(2n)]`.

**En cents**: `ε(n,d) = 1200·log2(1 + d/(2n))`. Límites por armónico (verificado aritméticamente en esta sesión):

| n | f_n (Hz, f1=40) | rango (Hz) | rango (cents) |
|---|---|---|---|
| 1 | 40 | [20.0, 60.0] | [−1200.0, +702.0] |
| 2 | 80 | [60.0, 100.0] | [−498.0, +386.3] |
| 3 | 120 | [100.0, 140.0] | [−315.6, +266.9] |
| 4 | 160 | [140.0, 180.0] | [−231.2, +203.9] |
| 8 | 320 | [300.0, 340.0] | [−111.7, +105.0] |

Simétrico en Hz (siempre ±f1/2 ≈ ±20.2 Hz con el f1 real del shaper), **asimétrico en cents** — consecuencia logarítmica, no bug. Nota musical ❓: ±20 Hz contra un vecino a f1 de distancia produce batidos de ~20 Hz — plena zona de roughness (Plomp-Levelt, citado en HIT L353): el detuneo máximo suena claramente áspero, que es la intención semántica.

**Grado de snap y modo afinado/detuneado** ❓: parámetro global `s ∈ [0,1]` (snap inverso) tal que `f''(n,d) = n·f1·(1 + s·d/(2n))`. `s = 0` = modo **tuned** (la serie exacta, d se ignora: sólo presencia/ganancia); `s = 1` = modo **continuum** completo. Valores intermedios = "grado de snap" hacia la rejilla. Entre ambos modos, un cuerpo en movimiento activa el continuo completo de frecuencias, como pide Nicolás.

**Histéresis/snap cuantizado** ❓: para evitar aleteo del detuneo alrededor de la rejilla, cuantizar con banda muerta: si `|ε| < θ` (θ ≈ 15-25 cents ❓), snap exacto a la rejilla; fuera de θ, continuo; la transición requiere cruzar `θ + h` (histéresis h ≈ 5-10 cents ❓). Implementable **sin transforms nuevos**: `gate` ya tiene `threshold` + `hysteresis` declarativos ✅ (compiler.py L554-568), `pad_dwell` da debounce temporal ✅ (L631-643), y `slew_limiter` suaviza la persecución del objetivo de frecuencia ✅ (L579-583) — los tres validados en el compilador del weaver. La composición exacta (cuántos encadenamientos hacen falta y si la cuantización va en el weaver o en el store del shaper) queda para la implementación.

### C.4 Protocolo del experimento baseline

**Objetivo**: medir la matemática de los movimientos que los humanos percibimos como consonantes — calibrar las métricas candidatas de C.2 contra ratings perceptuales, y dejar el corpus + los datos + el script de análisis como baseline reproducible. Es la versión operacional de lo que HIT llama sensibilidad funcional a la organización consonante (H5, ✅ manuscrito L445-453) aplicada al dominio del movimiento.

**Fase 0 — Preparación** (1 sesión):
- Aprobación por Nicolás de: tabla C.1 (mapeo), fórmula objetivo `C_j` y forma del drive `d_j` ❓.
- Crear `research/movement-consonance/scripts/compute_metrics.py` (nuevo ❓; propuesta: leer .jsonl con stdlib, reimplementar las ventanas trailing con Δt real de `captured_at_us` igual que HarMoCAP, emitir por clip un CSV de agregados + un .jsonl/parquet por frame con las métricas).
- Planilla de rating: `ratings.csv` con columnas `rater_id, clip_id, pass, score_consonance (1-7), score_effort_fluido (1-7, opcional), comentario_libre`.

**Fase 1 — Corpus de video** (recolección):
- **12-18 clips, 20-60 s cada uno, un solo sujeto por clip**, en tres categorías balanceadas ❓:
  - **(a) Consonante-experto** (~6): bailarín/a (material que el equipo identifique como "placer visual por eficacia y sensualidad" — el criterio fenomenológico de Nicolás), artista marcial (forma de taichi/kata fluida; la práctica de rope-flow del propio Nicolás es candidata — el manuscrito HIT ya la nombra como archivo físico del Jpsh!, ✅ L900).
  - **(b) Neutro/cotidiano** (~4-6): caminar, estirar, tareas domésticas — el centro de la escala.
  - **(c) Disonante deliberado** (~4-6): el mismo performer ejecuta movimientos torpes, frenados, contra-resistencia imaginaria, arrítmicos a propósito. Que (a) y (c) sean del mismo performer cuando sea posible controla el factor "cuerpo/estilo" ❓.
- **Requisitos de captura** (heredados del dominio operativo verificado ✅ FEATURES.md L28-33): cámara fija, ~frontal, cuerpo entero visible, torso ≥ 15% del alto del frame, ≥ 30 fps, iluminación estable.
- **Privacidad** ✅ (record_session.py L4-7): consentimiento documentado por performer; videos y .jsonl fuera de git (outputs gitignored); el corpus de investigación no se publica sin consentimiento. Clips de terceros sólo con licencia que lo permita y registro de procedencia.

**Fase 2 — Captura a .jsonl** (por clip, comandos verificados ✅):

```bash
cd ~/Projects/HarMoCAP
python scripts/run_realtime.py \
  --source videos/clip01_danza.mp4 \
  --record outputs/sessions/consonance/clip01.jsonl \
  --mode group --warmup 2 [--show]
```

(`--source` acepta ruta de video ✅ run_realtime.py L92-93, L118; `--record` escribe el .jsonl ✅ L98; `--mode group` = identidad reforzada por slot ✅ L101-103; `--warmup 2` para no perder 10 s de un clip de 30 — el default es 10 ✅ L96-97; efecto exacto del warmup sobre la grabación: verificar en la corrida ❓.) Atajo equivalente: `scripts/record_session.py --source <video> --seconds <N> --name clip01` ✅. Validación por clip: contar frames, histograma de `present`, fracción de keypoints OBSERVED (descartar clips con < 80% observed en las articulaciones de la tabla ❓).

**Fase 3 — Métricas offline** (por clip):

```bash
cd ~/Projects/harmonic-weaver
python research/movement-consonance/scripts/compute_metrics.py \
  --session ~/Projects/HarMoCAP/outputs/sessions/consonance/clip01.jsonl \
  --out research/movement-consonance/data/clip01.metrics.jsonl
```

(script nuevo ❓). Por frame y articulación: v, a, jerk, P_j (potencia firmada), brake_j rodante, PLV_j vs beat_phase, straight_j, smooth_j, C_j con pesos provisionales. Por clip (agregado para la correlación con ratings): mediana y P10/P90 de `C_j` promediado sobre las 9 zonas de la tabla C.1; fracción de tiempo con `d_j < −θ` y `d_j > +θ`; PLV medio global; tasa de eventos de frenado por minuto. Salida también en CSV `data/clip_metrics.csv` (una fila por clip).

**Fase 4 — Protocolo de rating humano (ciego)**:
- **Preparación**: recortar cada clip a su ventana válida (sin warmup), quitar audio original (evita sesgo musical), renombrar a IDs ciegos (`C01..C18`), barajar con semilla fijada y registrada. Opcional ❓: segunda condición con video de esqueleto (overlay) para reducir sesgo por apariencia del performer — HarMoCAP ya dibuja esqueletos con `--show` ✅ run_realtime.py L111-113.
- **Evaluadores**: ≥ 3 (miembros del equipo/tribe + Nicolás). Independientes: no ven los scores de los demás ni las métricas.
- **Escala 1-7** ❓, con anclas verbales derivadas del pedido original: *"¿Cuán consonante te resulta este movimiento? 1 = torpe, frenado, ruidoso, ineficaz — 7 = eficaz, fluido, sensual, da placer visual mirarlo"*. Una segunda pasada (mismo orden interno, re-barajado entre pasadas) para consistencia intra-rater.
- **Instrucción de anclaje**: antes de puntuar el corpus, cada rater ve 2 clips de calibración (uno claramente fluido, uno claramente torpe, fuera del corpus) para fijar los extremos de la escala ❓.
- Registro: `ratings.csv` (rater, clip, pass, score, timestamp).

**Fase 5 — Análisis** (la "matemática de la consonancia", primera aproximación):
- Confiabilidad: ICC(2,k) o α de Krippendorff entre raters; Spearman intra-rater entre pasadas.
- **Correlación de Spearman ρ entre el rating medio por clip y cada métrica agregada** (n = 12-18 clips: sólo asociaciones gruesas, no inferencia fina — el baseline es exploratorio por construcción ❓).
- Ranking de métricas candidatas; refit de los pesos `w` de `C_j` por regresión ordinal simple (rating ~ métricas) si n lo permite.
- Criterio de éxito del baseline ❓: al menos una métrica (o combinación) con ρ ≥ 0.6 contra el rating medio y acuerdo inter-rater ICC ≥ 0.6. Si ninguna llega, el resultado *es* el hallaje: la matemática candidata está mal especificada y se itera sobre C.2.
- Artefacto: `research/movement-consonance/data/baseline_results.md` con tabla de correlaciones + los .jsonl/.csv crudos + semilla de barajado.

**Fase 6 — Sonificación (fase 2 del proyecto, después de que aterrice la capability de detuneo)** ❓:
1. Implementar en el shaper: capability `/digital/harmonic/{N}/detune` (cents, rango por n según tabla C.3) + store (multiplicador que NO sea pisado por `f1·N`) + bump de contrato + safety default 0.
2. Escena weaver `consonance-v1.scene.json`: expander de geometría nuevo con la tabla C.1 (topología) + rutas de activación: presencia → `harmonic_source_envelope` (patrón bands-v1 ✅) y `d_j` → `detune` con gate-histéresis + slew_limiter (snap según C.3). Relajar el assert `arp_*` del replay offline (✅ weaver_runtime.py L741-744) o incluir una ruta arp de compatibilidad.
3. Replay offline de los .jsonl del corpus (comando verificado ✅):

```bash
cd ~/Projects/harmonic-weaver
PYTHONPATH=src:. .venv/bin/python -m rehearsal.weaver_runtime \
  --replay ~/Projects/HarMoCAP/outputs/sessions/consonance/clip01.jsonl \
  --scene rehearsal/scenes/consonance-v1.scene.json --run-id cons-clip01
# artefactos: rehearsal/artifacts/cons-clip01/instrument_outputs.jsonl + offline_replay_summary.json
```

4. Para escucha en vivo con el stack completo: `./scripts/start-live-stack.sh ...` (✅ MEMORY.md L39-47) alimentado con el replay del kit: `python harmocap-nico-kit/replay.py <session.jsonl> --host 127.0.0.1 --port 9100` (✅ replay.py L14-15; el listener harmocap del weaver escucha en 9100 ✅ weaver_runtime.py L588-589; el replay respeta los Δt de captura ✅ replay.py L8-12).
5. **Test perceptual de cierre** ❓: reproducción ciega sólo-audio de las sonificaciones del corpus; los raters puntúan "¿suena afinado/consonante?" 1-7; se correlaciona con el rating de movimiento de la Fase 4. Predicción del diseño: clips de categoría (a) → detuneo bajo y consonancia auditiva alta; categoría (c) → detuneo audible. Ese experimento cierra el bucle cuerpo→campo armónico y es la validación mínima del modo.

**Reproducibilidad**: semilla de barajado + versión de los 4 repos (`git rev-parse HEAD` de cada uno) + configs de features/calibración del .jsonl (viajan en el archivo ✅ schema.py L129-134) + script de métricas versionado en `research/`. El .jsonl de sesión es el dato primario inmutable: cualquier reanálisis futuro parte de ahí sin recapturar.

---

## Sources

**Fuentes primarias locales (leídas en esta sesión, ✅):**
- `/home/nicolas/Documents/Harmonic_Information_Theory_Foundations_AlterMundi_for-Ai-agents.md` — caps. 3 (L259-335), 4 (L337-403), 5 (L405-470), 8 (L682-761), 9 (L762-838), 10 (L840-924), y L261/L2680
- `/home/nicolas/Projects/HarMoCAP/src/harmocap/schema.py` (completo)
- `/home/nicolas/Projects/HarMoCAP/src/harmocap/smoothing.py` (completo)
- `/home/nicolas/Projects/HarMoCAP/src/harmocap/tempo.py` (L11-127)
- `/home/nicolas/Projects/HarMoCAP/src/harmocap/features.py` (L1-206, ventanas y buffers)
- `/home/nicolas/Projects/HarMoCAP/src/harmocap/capture.py` (L5-75)
- `/home/nicolas/Projects/HarMoCAP/src/harmocap/pipeline.py` (L1-46, L179-185)
- `/home/nicolas/Projects/HarMoCAP/docs/FEATURES.md` (completo)
- `/home/nicolas/Projects/HarMoCAP/docs/INTERFACE_SPEC.md` (L1-120)
- `/home/nicolas/Projects/HarMoCAP/scripts/run_realtime.py` (L88-123), `scripts/record_session.py` (completo)
- `/home/nicolas/Projects/HarMoCAP/harmocap-nico-kit/replay.py` (L1-60)
- `/home/nicolas/Projects/HarMoCAP/configs/features.yaml`
- `/home/nicolas/Projects/HarMoCAP/examples/fixtures/two_persons.jsonl` (estructura verificada programáticamente)
- `/home/nicolas/Projects/harmonic-weaver/MEMORY.md` (completo), `BITACORA.md` (tail)
- `/home/nicolas/Projects/harmonic-weaver/src/harmonic_weaver/engine/geometry_toolkit.py` (completo), `geometry_bands.py` (completo), `compiler.py` (L117-207, L241-252, L485-660, L700-960, L1031-1110, L1248-1346)
- `/home/nicolas/Projects/harmonic-weaver/src/harmonic_weaver/drivers/harmocap_driver.py` (L21-140, L250-264, L614-628)
- `/home/nicolas/Projects/harmonic-weaver/docs/CORE_DESIGN.md` (completo)
- `/home/nicolas/Projects/harmonic-weaver/rehearsal/weaver_runtime.py` (L1-60, L42-115, L440-560, L566-751, L858-938), `run_rehearsal.sh`, `README.md`, `push_scene.py` (completos)
- `/home/nicolas/Projects/harmonic-weaver/rehearsal/scenes/bands-v1.scene.json` (completo)
- `/home/nicolas/Projects/harmonic-weaver/scripts/start-live-stack.sh` (L1-77, opciones)
- `/home/nicolas/Projects/harmonic-shaper/src/harmonic_shaper/config.py` (completo), `state.py` (L128-360, L355-420, L1190-1266, L1305-1320), `audio_engine.py` (L150-272), `api.py` (L80-220), `osc_receiver.py` (L1-167, L185-210), `midi_control.py` (selección), `contracts/shaper.contract.json` (parseado: 24 capabilities)
- `/home/nicolas/Projects/beacon-spatial/beacon.scd` (L14-34, L87-209, L339-450), `beacon_spatial.contract.json` (parseado: 9 capabilities)
- HMK librarian (workspace `~/agents/compaii`): `hybrid-pack` query "Harmonic Information Theory consonance interval interference" → `[mem:22]`, `[mem:14]`; `expand --id 22` ✅

**URLs:** ninguna (investigación interna; no se hizo web search).

**Nota de honestidad**: los cómputos de cents/rangos de detuneo y de amplificación de ruido fueron verificados con Python en esta sesión (aritmética mostrada en el cuerpo). No se ejecutó ningún pipeline (HarMoCAP/weaver/shaper) — los comandos citados están verificados contra los parsers de argumentos y docs de cada script, pero no corridos end-to-end. Todo lo marcado ❓ es propuesta de este agente, no capacidad existente.
