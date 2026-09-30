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
reviewed. The program imports the pinned Weaver laboratory model facade,
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
- The JSON contains SHA-256 hashes of the imported Weaver model/contract
  files. These document exact producer code even if this research branch later
  moves beyond its PR #30 base.

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
frames. Comparisons over missing features use identical observed timestamps and
units. Values in the JSON retain IEEE-754 precision; interpret near-zero and
cross-platform differences with numerical tolerances (typically `1e-6`), not
bitwise equality. The digest verifies repeats in the **same pinned environment**.

## Scope and next interface questions

No production module, schema, UI, preset, cache, or audio code is modified.
The [report](REPORT.md) separates expected results, observed results, limits,
and proposed interface changes. In particular, a single wrist can have a valid
per-edge diagnostic while the bilateral zone signal is missing; the frozen
baseline's public `FeatureFrame` does not expose raw surprise or `a·v`.
