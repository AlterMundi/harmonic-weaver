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
