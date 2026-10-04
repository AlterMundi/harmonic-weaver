# Frozen-body Fourier controls — 2026-10-03

Result: **preserving coordinate cross-spectra does not preserve articulated
geometry or finite-history descriptors**. The bank characterizes controls and
descriptor sensitivity, not HIT, intention, causal coupling, bodily efficiency
or human perceptual acceptance. No captured human data is used or published.

## Reproduce and reuse

Starting point: #36/#97 as integrated by CompAII in #98, frozen at
`94536702b568641ba0e22c2668130877d6bdd99d`. From the repository root with laboratory
dependencies installed:

```sh
PYTHONPATH=src:. python -m research.laboratory.sai_bridge.body_fourier > /tmp/sai-body-fourier.json
```

The JSON includes the configuration, retained/excluded support, all seeds,
spectral checks, paired temporal differences, missing reasons, geometry, full
descriptive preset, runtime and selected **effectively imported** module paths
and hashes. Reference commit and effective code are separate. Source hashes
identify provenance; equal hashes between environments are not required.

Public fixtures: `fixtures/body_fourier_public.json` freezes the full experiment
recipe (60 Hz; seeds 7/19/41; every algorithm setting explicit, plucks disabled);
`body_fourier_boundary_frames.json` contains 17
serialized synthetic MotionFrames with multiple people, epochs, invalid joints
and a skipped sample. The larger recipe is generated once into deep-copied,
frozen-input snapshots before Fourier transforms. Both fixtures are synthetic.
The small snapshot tests ingestion/boundaries, not descriptor-effect magnitude.

Reusable API in `body_fourier.py`:

```python
blocks, support = prepare_blocks(frozen_frames, explicit_body_config,
                                 provenance={"kind": "local recording", "id": "..."})
controls, spectral = control_frames(blocks[0], seed=7)
result = compare_blocks(blocks, seeds=(7, 19, 41), preset=explicit_descriptive_preset)
```

Callers select a nonempty person ID and ordered `(joint, axis)` scalar channels.
Only those coordinates of that person are transformed; other coordinates,
other people, source/stream, source and availability times, sequence, units and
capture metadata are retained. No person is selected by list position. Inputs
are copied, not mutated. Each condition/block gets a fresh model history with
the same preset and scale; no history crosses a cut. Existing bridge APIs are
unchanged. Web execution/visualization belongs to CompAII, not this PR.

## Support and conventions

Preparation accepts 2D only and requires declared Hz, positive scale in the
input unit, scale provenance, confidence threshold and minimum block length.
Default timing tolerance is `1e-8 + 1e-6/60 = 2.67e-8 s`, applied to both each
interval and the complete block's expected index grid. It allows floating-point
timestamp rounding, not camera jitter. Real clocks may need a justified explicit
tolerance; this bank does not silently infer one. No interpolation, filling,
reordering or resampling occurs. Contract-invalid input is a hard error.

Gaps, identity/coordinate-metadata changes and irregular intervals split blocks.
Missing/held/low-confidence selected joints, absent selected people, mismatched
scale units and nonincreasing times within an epoch are excluded explicitly.
Short blocks are excluded and counted. Invalid **unselected** joints remain in
the frozen frame; model/geometry coverage reports their consequences rather
than repairing them. Geometry requires observed endpoints above the declared
confidence threshold. Duplicate/backward times cannot become matched epochs.

The upper-body selection retains **800/910 supplied frames** in blocks of
240, 240, 100, 92 and 128. Exclusions: one invalid selected joint, one absent
person, 108 frames in short blocks. The recipe's 18 omitted frames never enter
the input count; their temporal gap is reported, not filled. The one-scalar
selection retains all 128 frames. The explicit scale `.26 frame_height` is a
synthetic normalization reference, not physical calibration or an inferred
body size. No energetic or metric-3D interpretation follows from it.

`phase_surrogate` is reused unchanged: shared means one random phase per
interior positive-frequency bin across **all selected scalar channels**;
independent means one phase per bin per channel. DC and real Nyquist (even N)
are preserved. Complex cross-spectra are preserved among selected channels by
shared phase cancellation; relations to untransformed moving channels need not
be. Fluctuation spectra are reported separately so absolute-position DC cannot
hide changes. No window, clipping or length normalization is applied.

Each finite block is treated as a periodic N-sample Fourier record. Cropped
blocks need not be physically cyclic: circular spectral identities do not imply
finite-window invariance or smooth physical closure. No endpoint is silently
removed. Both transformations need the whole block and are **offline/noncausal**;
a changed future alters earlier surrogate coordinates. Retaining availability
timestamps enables replay, not live availability of transformed samples.

## Observations and counterexamples

Local environment: Python 3.12.13 / NumPy 2.5.1 / Pydantic 2.13.4. Numerical tests
use `1e-12` spectral/geometric tolerances and broad descriptor inequalities:
roundoff identities are different from platform-sensitive rank/validity gates.
Every descriptor uses its own single three-condition observed identity
intersection, never unmatched marginal means. All six bilateral local I/R pairs
plus collective residual/change are reported, including missing support.

Coupled 240-frame multitone body: individual spectra are preserved; shared
fluctuation cross-spectrum changes are below `1e-12`, while independent changes
are approximately 1.96/2.00/1.93 (normalized complex differences, not bounded
quality scores). Collective residual distinguishes these constructed conditions:

| Seed | Original mean | Shared mean | Independent mean | Common / total |
|---|---:|---:|---:|---:|
| 7 | ~0 | .00191 | .35709 | 231 / 240 |
| 19 | ~0 | ~0 | .37755 | 205 / 240 |
| 41 | ~0 | ~0 | .43535 | 231 / 240 |

But local wrist–elbow I is **not invariant** under shared phases: paired temporal
MAE from original is .592/.531/.587. Independent-phase MAE is .506/.453/.328,
so temporal deviation is not a monotonic amount of lost organization.

Rigid articulated arms are the geometric counterexample. Original forearm
length is exactly `.14 frame_height`; its std is below `1e-12`. Maximum relative
forearm-length change after shared phases is **7.9% / 12.7% / 14.0%**, and after
independent phases **55.0% / 70.8% / 94.0%**. Shared cross-spectra are nevertheless
preserved. Geometry is measured against the same-time frozen lengths, not
silently repaired or classified with invented anatomical plausibility bounds.
Collective residual also changes under shared phases (.106→.150, .107→.118,
.106→.133), and collective change increases; the full common-support values and
temporal differences are in JSON. These changes cannot be attributed uniquely
to relational loss rather than changed geometry and finite-history statistics.

One moving scalar channel gives **identical shared/independent controls**;
collective paired difference is exactly zero on 119/128 frames, while bilateral
wrist I/R have no valid support because the other side has no established mode.
Static I/R and collective outputs are missing, not neutral zero. Gapped blocks
test support loss and reset behavior, not physiological robustness or a clean
periodic null distribution. Three seeds are sensitivity examples, not p-values.

## Verification and next useful experiment

```sh
PYTHONPATH=src:. python -m pytest -q tests/research/test_sai_bridge_*.py
```

**58 tests pass** against the #98 imports, including the prior 34 regressions.
The full new command executes successfully. Tests cover deep-copy/identity
preservation, explicit person selection, gaps/epochs, invalidity, strict timing
and accumulated drift, odd/even Fourier records, geometric distortion, paired
common support, fresh histories, offline future dependence and effective code.

Next: extend the **synthetic** articulated bank with matched-length angle-space
or geometry-constrained controls and quantify their spectrum trade-off before
attributing descriptor changes to relation alone. Those are distinct controls,
not post-hoc corrections to this Fourier bank. Later local body recordings need
explicit calibration, consent and timing/support checks; keep poses, images,
tracking and private result JSON local. No automatic merge is performed.
