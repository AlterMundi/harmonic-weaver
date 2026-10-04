# Sai × Anni × Weaver: synthetic contrast bridge

This is a **synthetic-only**, read-only bench. It is based on the questions in
[Goal Oliva](../../../docs/laboratory/NEXT_ITERATION.md), not a human study or
a validation of HIT, Laban, biomechanics, perception, or physical 3D capture.
It does not use video, audio, Shaper, HarMoCAP, or CompAII's comparator.

## Run

From the repository root, with Weaver's `lab` dependencies installed (Python
3.12, NumPy, Pydantic):

```sh
PYTHONPATH=src:. python -m research.laboratory.sai_bridge.run > sai-bridge-result.json
```

That **one command** generates deterministic JSON. The output path is an
example; keep generated result files outside the PR unless deliberately
reviewed. The program imports the Weaver laboratory model facade selected by
the Python environment (the historical reference is pinned below),
constructs validated 2D `MotionFrame`s, and compares descriptors before audio.
It prints source hashes and a result digest. For tests:

```sh
PYTHONPATH=src:. python -m pytest -q tests/research/test_sai_bridge_*.py
```

`fixtures/observation.json` is a small version-1 `MotionFrame`; the separate
`fixtures/truth.json` demonstrates two synthetic 3D points projecting to the
same image point. Generated longer fixtures are deterministic functions in
`synthetic.py`. A 2D frame **never contains** the 3D truth sidecar.

## Fixed provenance

- Weaver PR #30 base: `6bdb47af935e58bb3a4e0cfe22f967a134de6464`.
- Sai: [`f6b96da041bbe95e35ab865d2a07d082d2adba29`](https://github.com/SairaAsua/movimiento-armonico-investigacion/tree/f6b96da041bbe95e35ab865d2a07d082d2adba29).
- Five Sai scripts reproduced independently before implementing this bridge:
  `laban_hit_marginales_igualados.py`, `prediccion_relacional_sintetica.py`,
  `geometria_tiempo_sintetica.py`, `proyeccion_2d_ambigua.py`, and
  `fase_causal_sintetica.py`. Exact commands and observations are in [REPORT](REPORT.md).
- GitHub lists no licence for Sai's repository at that SHA. No Sai code or
  files are redistributed here. The mathematical scenarios are independently
  implemented and attributed; this is not a licence determination.
- `source_sha` declares historical reference commits, not the effective checkout.
  `production_source_sha256` records resolved `module.__file__` paths and SHA-256
  hashes for six selected, effectively imported Weaver model/contract modules.
  It therefore follows imports from another checkout via `PYTHONPATH`, rather
  than hashing files relative to the bridge. It is not a complete dependency,
  dynamically loaded baseline-driver, or in-memory bytecode audit. Do not change
  source files during a run; the manifest hashes their bytes at report time.

## What each representation means

| Name in output | Source | Meaning | Not equivalent to |
|---|---|---|---|
| `phase_r_*` | Known synthetic latent phase | Concentration of pair phase difference | Anni's `zone.6.R` |
| `plane_q` | Known 3D truth | Diagonal of arc-weighted direction tensor, summing to 1 | A plane, a Grassmannian subspace, or a 2D observation |
| `q_tensor_counterexample` | Known 3D truth | Full directional tensor and its diagonal Q | A live body reconstruction |
| `spacetime_c_2d_analogue` | Ideal 2D path | Arc-weighted speed difference between image half-planes | Sai's body-frame 3D C contract |
| `zone.6.I/R` | Weaver 2D wrist–elbow edges, then bilateral aggregation | Local reinforcement/transverse change | Inter-hand phase or task quality |
| `collective.residual/change` | Weaver causal subspace on observed 2D joint velocities | Projected novelty and subspace change on valid support | Harmonicity or causality |

Every source frame has a synthetic source time and a later logical availability
time. `read_models` resets on stream/person discontinuities through the
production facade. Prediction rows record origin, latest feature, availability,
and target start. The held-out units are whole synthetic sessions, not random
frames. Comparisons require matching observation identities, observed validity,
and measurement units. Values in the JSON retain IEEE-754 precision; interpret near-zero and
cross-platform differences with numerical tolerances (typically `1e-6`), not
bitwise equality. The whole-report digest includes runtime, source hashes and
absolute paths. No equal hashes between environments are required; compare
numerical fields with tolerances and inspect effective provenance separately.

## Offline Fourier controls

The same one-command report now includes `fourier_controls`. Reusable APIs in
`fourier.py` are `FourierConfig`, `scenario`, `phase_surrogate`,
`frames_from_channels`, `spectral_checks` and `common_three`. Defaults are
480 samples at 60 Hz and three declared seeds `(7, 19, 41)`; every seed is
reported, not selected for its outcome. `frames_from_channels` returns ordinary
COCO-17 2D `MotionFrame`s suitable for other offline Weaver banks. No comparator
or private video is needed.

For each finite N×C regularly sampled coordinate-displacement array, let
`X[k,c] = rFFT(x[:,c])`. At interior positive-frequency bins:

```text
shared:      Y[k,c] = X[k,c] * exp(i * phi[k])
independent: Y[k,c] = X[k,c] * exp(i * phi[k,c])
y = irFFT(Y, n=N)
```

Phases are uniform on `[-pi, pi)`. DC and the real Nyquist coefficient (even N)
are unchanged; negative frequencies are implied by real reconstruction.
Each scalar channel is a declared joint coordinate, not a whole limb, joint,
person, speed magnitude or signal descriptor. Constant pose offsets are added
after reconstruction. No clipping, padding, windowing or rescaling is applied.
Do not supply missing samples, uneven timestamps or a repeated periodic endpoint.

| Property | Shared phases | Independent phases |
|---|---|---|
| Individual coordinate periodogram, mean, variance, circular autocorrelation | Preserved | Preserved |
| Complex cross-spectrum and circular lag cross-covariance between channels | Preserved | Generally changed where channels share spectral support; not guaranteed to change every relation |
| Higher-order/cross-frequency relations, trajectories and finite-window temporal organization | Not generally preserved | Not generally preserved |
| Individual speed distributions, articulated geometry, biomechanics | Not guaranteed | Not guaranteed |

The shared-phase control retains `X_c * conjugate(X_d)` because its phase
factors cancel. Independent phases add a relative phase to this product.
This is **not** a test of coupling causation or a claim that shared phases
preserve all relational organization. Per-bin magnitude-only periodogram
coherence is not used as a discriminator.

Three scenarios are evaluated: proportional multitone elbow/wrist motion,
one active scalar wrist channel, and a static pose. For each descriptor,
`common_three` takes one exact identity/observed intersection across original,
shared and independent outputs; all means, standard deviations and paired
MAEs use that same support. Full observed counts are also reported. No support
means `null`, never a neutral zero. These are existing facade descriptors,
not newly implemented models or independent wins for different audio mappings.

Both transforms require the **whole record** and are noncausal offline controls.
A future-tail perturbation changes earlier surrogate samples, as tested.
Synthetic availability clocks describe replay of the completed fixture, not
when a live transform could know its samples. The causal Weaver facade remains
unchanged; a causal model receiving an offline surrogate does not make that
surrogate causal. See [FOURIER_REPORT](FOURIER_REPORT.md) for results and limits.

## Epoch identity in the research adapter

`read_models` preserves `source_id`, `stream_id`, `person_id`, `sequence`, and
source time in every output record. A loop or backward seek within one source
needs a distinct `stream_id`; reusing an earlier epoch with a repeated or
backward time is rejected even if other epochs intervene. Source changes also
reset the adapter's model history when different sessions reuse a stream name.

`common_observed` aligns by the exact tuple
`(source_id, stream_id, person_id, source_time_s)` and returns
`(identity_tuple, left_value, right_value)` for each common observed signal.
`sequence` is retained for inspection; timestamps identify observations within
their declared epoch. Both inputs are checked for duplicate identities before
filtering missing signals. Ambiguous duplicates and legacy records lacking
identity raise `ValueError`. There is no fallback to time alone or epoch order.

Compared conditions must preserve shared observation identities. For separately
named sessions, the caller must establish correspondence explicitly before
comparison. These IDs describe a source and its epoch, not an algorithm or
condition label. Reordered or omitted epochs therefore cannot cross-match.

## Scope and next interface questions

No production module, schema, UI, preset, cache, or audio code is modified.
The [report](REPORT.md) separates expected results, observed results, limits,
and proposed interface changes. In particular, a single wrist can have a valid
per-edge diagnostic while the bilateral zone signal is missing; the frozen
baseline's public `FeatureFrame` does not expose raw surprise or `a·v`.
