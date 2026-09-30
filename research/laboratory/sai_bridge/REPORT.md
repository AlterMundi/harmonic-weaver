# Synthetic contrast report — 2026-09-29

Status: software/methodology result on **constructed data only**. No video,
human judgments, physiological measurements, or HIT validation. This report
records a negative result and several counterexamples as first-class outcomes.

## Provenance and reproduction

The bridge starts from Weaver PR #30 `6bdb47af935e58bb3a4e0cfe22f967a134de6464`.
Sai's five original scripts were run **unmodified, only in a temporary external
checkout** at `f6b96da041bbe95e35ab865d2a07d082d2adba29`, with Python
3.9.6. From that checkout's root the commands were:

```sh
python3 research/laban_hit_marginales_igualados.py
python3 research/prediccion_relacional_sintetica.py
python3 research/geometria_tiempo_sintetica.py
python3 research/proyeccion_2d_ambigua.py
python3 research/fase_causal_sintetica.py
```

All exited 0. Key Sai outputs: aligned/opposed `R_phase=1/0.077246` with
`Q_right=(.5,.5,0)` or `(.5,0,.5)`; null prediction linear/+relation
`RMSE=.2981/.2982`; related prediction linear/+relation/matched nonlinear
`1.5504/.2979/.2975`; time occupancy `.5/.32461` but both arc halves `~.5`;
identical image projection with 3D lengths `2.513266/5.690778`; causal event
phase error `-36°` on acceleration, plus warmup/expired/future guard.
These reproduce Sai's examples, not an empirical effect. GitHub reports no
repository licence; no Sai code or fixtures are copied into this PR.

The independent bridge command (see [README](README.md)) ran using Python
3.12.13, NumPy 2.5.1, Pydantic 2.13.4. Its JSON `result_sha256` was
`7d865d2994a0ba40faff9d1afee6bbd339ea43b391075aa55777b9d995b6ecd6`.
Imported production files' hashes are emitted in JSON. Eight bridge tests
passed. Numerical comparisons have tolerances; the digest is for reruns in
this pinned environment, not a promise of bitwise equality on other BLAS/OS
stacks.

## Expected → observed → interpretation/limit

| Contrast | Expected | Observed | Limit / counterexample |
|---|---|---|---|
| Same circle, different timing | Arc occupancy stable; dwell time changes. | First semicircle time `.501` vs `.325`, arc `.501` vs `.500`; 2D signed speed-half-plane analogue `~0` vs `-.681`. | The analogue is **not** Sai's 3D body-frame C; no energy inference. |
| Matched individual movement marginals, altered pairing | Single-hand distributions and 3D truth Q stable; phase relation changes. | `R_phase=1` vs `.077246`; event-only R stays `1` in both. The left wrist speed series matches exactly; sorted right speeds match within floating precision. | Event endpoints erase within-cycle timing. Phase is known simulation truth, not recovered from camera. |
| Weaver on those same 2D MotionFrames | Different descriptors may distinguish different relations. | Local wrist–elbow `I` common-support means `-.388/-.417` (229/241 frames); `R_e=.455/.438`. Collective residual `~0/.337` on only 83/241 common observed frames. | **Negative for this local I as an inter-hand coupling discriminator.** Collective coverage collapses in the opposed condition and cannot be compared on its full marginal. Neither score is human quality. |
| Baselines and angular signal | Existing signals are useful comparators but not interchangeable. | Local constant-velocity error `.259/.265` on 229 common frames; angular error `.443/~0` degrees on 229; frozen baseline wrist-zone speed `1.563/2.458` on 241. | Baseline's bilateral energy-max selection is nonlinear pooling: even matched *individual* marginals need not produce matched *pooled* output. Angle means over unwrapped cycles are not a meaningful outcome. |
| Null and constructed relational future | No gain in null; relation helps a linear summary but not beyond adequate nonlinear capacity. | Null linear/+relation `.2526/.2528`; constructed related world `1.272/.2456`, matched nonlinear `.2455` RMSE on 4 held-out sessions (480 units). Persistence/constant-velocity errors are also emitted. | Product relation is deterministic from left/right. It adds representation, not sensory information; target is synthetic and not a movement outcome. |
| Unequal-support negative control | Selecting easy clips manufactures advantage. | Invalid full-base/easy-relation `1.402/.246`; same easy rows `.235/.246`. Guard rejects unequal row IDs or altered targets. | Any future comparison must report coverage and use the same units/targets. |
| Common rhythm without pair coupling | In-phase appearance need not establish direct coupling. | Eight sessions have within-session R≈1; pooled prespecified offsets give R≈0. | Constructed shared driver and offsets are a counterexample, not a causal-identification method for recordings. |
| 2D ambiguity and moving frame | Projection and coordinate choice limit physical claims. | Same image to `<1e-12`; 3D arcs `2.513/5.691`. Translation changes relative edge by `0`; rigid 90° rotation yields camera edge arc `.225` but co-moving edge arc `~0`. | A 2D descriptor cannot infer depth or distinguish internal change from frame rotation without a declared reference. |
| Q versus full direction tensor | Q may erase directional covariance. | Rank-one `(+x,+y)` and `(+x,-y)` paths both Q `(.5,.5,0)` but tensor Frobenius gap `1.414`. | Q is a diagonal summary, not a plane/subspace. The rank-one case is deliberately degenerate; Weaver marks an isotropic component boundary missing. |
| Tracking quality | Gaps reduce support; noise changes descriptors. | On 100 frames, `I` observed 94 clean vs 91 with seeded jitter and one held/missing gap; means `-.241/-.309`. | The difference is not an accuracy estimate. No camera calibration or independent ground truth for pose error was supplied. |

The synthetic generator uses its own deterministic functions, not Sai's files.
Its paired clips pass the **same** validated 2D frames to baseline/local/
relational/angular/collective Weaver facades. The newer facade computes many
descriptors regardless of selected audio mapping; their repeated diagnostic
values under different preset IDs are **not independent model victories**.
We compare descriptive signals before synthesis, not tuned/detuned sound.

## Causality, availability, and failure conditions

- Prefix test: appending a changed future leaves each model's first 30 outputs
  identical. This checks these sequences and APIs, not all possible future leaks.
- Availability: the generator's logical availability is source time +10 ms;
  the prediction guard rejects a feature available after its origin. Real
  source/monotonic clock mapping and latency are unmeasured.
- Sessions 0–5 train; 6–9 evaluate. The comparison rejects unequal/duplicate
  keys and changed targets. It does not establish cross-person transfer.
- Held/missing wrists are not zero-padded into an observed score. Changing
  stream/person or seeking resets model history. A degenerate collective plane
  is explicitly missing rather than assigned an arbitrary axis.

## Interface findings and proposed bridge (not implemented here)

1. **Expose per-edge validity and source time in a stable research interface.**
   `FeatureFrame.diagnostics.regions["6"].relations` can contain a valid left
   wrist–elbow score while `zone.6.I` is missing because the right edge has no
   established mode. A versioned per-edge signal plus support IDs would allow
   unilateral tests without treating missing as neutral.
2. **Expose frozen raw baseline terms** (`surprise`, signed `a·v`, prediction
   horizon/defaults) through a read-only offline accessor or diagnostic version.
   The current `FrozenBaseline` public signals expose speed, acceleration,
   gain/detune/phase, not those raw terms. Reverse-engineering them from sound
   would confound the comparison.
3. **Declare a per-signal window and availability** for strong live/replay
   claims. The current `FeatureFrame` has frame availability and lookahead,
   but not every diagnostic's support window, calibration, or missing reason.
   This bench uses synthetic clocks and does not alter contracts.
4. **Proposed tensor→subspace→Q bridge:** retain the ordered 3D direction
   sequence and arc weights; calculate the full positive semidefinite
   `D=Σ ds·ttᵀ/Σds`; compare its eigenspaces/projector only when eigenvalue
   gaps and support permit; take `Q=diag(D)` in a declared body frame.
   Compare full D against Q under sign-flipped diagonals, rotation, missing
   arcs, and equal eigenvalues. Do not call Q a Grassmannian point or infer a
   3D D from monocular 2D. This is a next experiment, not a live algorithm.

These findings suggest a second synthetic bridge focused on **inter-hand**
relations if the research question is phase coupling; Anni's v0 was defined
for adjacent segments and should not be relabelled as a failed universal HIT
test. Real footage, perceptual judgments, and task outcomes require separate
consent, instruments, controls, and held-out sessions.
