# Offline Fourier contrast — 2026-10-03

## Question and construction

Can existing relational descriptors distinguish between preserved individual
coordinate spectra with preserved versus changed second-order channel relations?
This is a controlled synthetic contrast, not a human performance experiment,
causal-coupling identification, perceptual acceptance result or validation of HIT.

The construction and formula are in [README](README.md#offline-fourier-controls).
The new extension starts at PR #36 follow-up `2767df10b2e6aa728e2f355203c896e94b8ac9fc`,
which itself references Weaver PR #30. No Sai source code is copied; these are
independently implemented controls motivated by the shared Sai/Anni questions.

Three scenarios × three declared seeds × original/shared/independent = 27
descriptive replays, each with 480 regularly sampled 2D frames at 60 Hz:

- **Coupled multitone:** both elbow/wrist pairs have proportional displacement
  across eight scalar coordinate channels. Frequencies 3, 7 and 10 cycles per
  record include a cross-frequency triad. Wrist amplitude is twice elbow
  amplitude, so wrist–elbow relative velocity is not identically zero.
- **One active scalar channel:** only the left wrist's x coordinate moves.
  Shared and independent randomization coincide exactly with the same seed:
  there is no second moving channel whose relative phase could be randomized.
- **Static:** all coordinate displacements are zero. Randomizing phase creates
  no motion and must not create an observed relational score.

Each condition is run through the unchanged public `MotionModel` facade with
the same `relational` preset settings and fixed torso scale `.26`. The facade
also emits angular/local/collective descriptors; this is not evidence from
independent model estimators. The bridge changes no production settings or code.

## Observed results

Local run: Python 3.12.13, NumPy 2.5.1, Pydantic 2.13.4. Numbers below are
rounded observations, not required cross-platform bit patterns. The JSON emits
the effective imported module paths/hashes and runtime versions. Tests use
tolerances and broad scenario-specific inequalities.

In the coupled scenario, maximum individual periodogram error normalized by
the largest original power is below `8e-16` for both controls. Shared complex
cross-spectrum change is below `6e-16`; independent change is `1.84`, `2.00`,
`1.54` for seeds 7, 19, 41. Values above one are allowed for this normalized
complex difference; it is not a bounded coupling score.

Mean `collective.residual` on a **single three-way observed intersection**:

| Seed | Original | Shared phases | Independent phases | Common / total |
|---|---:|---:|---:|---:|
| 7 | .00061 | .00384 | .54862 | 471 / 480 |
| 19 | .00062 | .00107 | .53290 | 466 / 480 |
| 41 | .00061 | .00110 | .31569 | 471 / 480 |

For this low-dimensional construction, the collective descriptor distinguishes
conditions despite matched individual spectra. Shared filtering preserves the
linear channel dependencies; independent filtering changes them. This does
not establish that the descriptor measures all organization, that independent
surrogates are disorganized in every sense, or that these values imply better
movement. Near-zero is not a generic target for real motion.

Local `zone.6.I` means on its own three-way common support:

| Seed | Original | Shared phases | Independent phases | Common / total |
|---|---:|---:|---:|---:|
| 7 | -.62940 | -.61106 | -.51421 | 272 / 480 |
| 19 | -.61831 | -.66803 | -.57236 | 304 / 480 |
| 41 | -.63588 | -.66067 | -.43532 | 304 / 480 |

The temporal paired MAE of shared versus original I is `.427`, `.394`, `.408`.
Thus shared Fourier cross-spectrum preservation does **not** preserve the
finite-window nonlinear I trace. Independent versus original MAE is `.390`,
`.332`, `.556`: it is not even consistently larger than shared versus original.
Do not interpret MAE as a monotonic amount of lost organization, or pooled
I as a pure inter-hand coupling detector. `zone.6.R`, angular and local error
descriptors, their standard deviations and direct shared–independent MAE are
also emitted without selectively promoting whichever metric separates best.

The one-channel control gives **identical** shared/independent coordinates for
all three seeds. Their collective residuals are identical and approximately
zero (`~1e-11`; common support 467, 467, 471). Bilateral `zone.6.I/R` have no
observed support because the other wrist–elbow edge has no established motion
mode; this is an interface/coverage limit, not a measured neutral relationship.
Static I/R and collective residual have no observed support. Their summaries
remain `null`, not zero. The original/static coordinate spectra remain unchanged.

## Numerical controls and possible refutations

- Test both odd and even record lengths on nonzero-mean random inputs: preserve
  each rFFT magnitude, DC, real Nyquist where present, variance and circular
  autocorrelation. Use `1e-12`/`1e-10` numerical tolerances, not hash equality.
- Shared phase cancellation is checked on the **complex** cross-spectrum and
  lagged circular cross-covariance. A violation would refute the implemented
  preservation claim. Higher-order third moments change on the multitone triad,
  explicitly refuting any claim that all relational structure is preserved.
- Independent phase changes are checked on the declared coupled example for
  every seed. They do not guarantee changed relations for static, one-channel,
  disjoint spectral support or arbitrary other signals. These are not hypothesis
  tests or surrogate p-values; three seeds are sensitivity examples, not a null
  distribution with calibrated significance.
- Every descriptor uses one three-condition intersection of exact
  `(source, stream, person, time)` identities with observed validity and matching
  units. All observed counts and common counts are reported. Different
  descriptors have different support; do not compare them as if support matched.
- Prefix and fixed-duration future-tail tests demonstrate the transform's
  offline/noncausal character. This is separate from the existing prefix test
  of Weaver's causal model. Synthetic replay availability is not live causality.
- Source-manifest regression points a loaded module to an alternate source
  file and confirms the manifest follows that module, not the bridge checkout.
  The historical reference commit is separate from actual imported source.

If a broader prespecified bank fails to retain the collective separation, the
result must remain a scenario-specific sensitivity, not a general discriminator.
Changes in body geometry, scalar channel grouping, signal amplitude, mode/noise
thresholds or camera frame can alter the scores and observed coverage. The bank
does not identify a biological mechanism or assess energetic efficiency.

## Reproduce and reuse

From the repository root with laboratory dependencies installed:

```sh
PYTHONPATH=src:. python -m research.laboratory.sai_bridge.run > /tmp/sai-fourier-result.json
```

Tests:

```sh
PYTHONPATH=src:. python -m pytest -q tests/research/test_sai_bridge_*.py
```

Local verification: **34 tests passed**, including the earlier bridge/identity
tests and the new odd/even spectral, support, descriptor, offline and provenance
regressions. The complete one-command report also executed successfully.

`FourierConfig` fixes sample count, sampling rate and seeds. `scenario` emits
finite arrays plus an explicit coordinate map; `phase_surrogate` can be reused
for other regularly sampled synthetic arrays; `frames_from_channels` creates
portable MotionFrames. No dependency on CompAII's comparator, runtime changes,
private videos, UI, cache, Shaper or HarMoCAP is introduced.

The JSON's whole-report digest includes environment and absolute effective
module paths. No matching digest across environments is required, and no claim
is made about equivalence to the historical `7d865d...` or Nico's `37f610...`.
The limited provenance correction resolves module paths at import origin; it
does not open a new exhaustive dependency audit.
