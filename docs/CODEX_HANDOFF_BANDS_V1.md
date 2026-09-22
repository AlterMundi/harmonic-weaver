# Codex Handoff — bands-v1 stabilization and polyphony proof

## Mission

Continue the HarMoCAP-controlled `bands-v1` body instrument for two bounded iterations. The current live sound path works; preserve that baseline while making runtime evidence trustworthy and multi-person polyphony reproducible.

Canonical issue: https://github.com/AlterMundi/harmonic-weaver/issues/4

Read this file, the issue, `MEMORY.md`, `BITACORA.md`, and `rehearsal/scenes/bands-v1.scene.json` before editing.

## Repository and branch state

- Workspace: `~/Projects/harmonic-weaver`
- Branch: `feat/geometry-activation`
- HEAD at handoff: `274c343`
- Geometry implementation commit: `5ac44df`
- Current branch is local and has not been published remotely.
- Generated `rehearsal/artifacts/` directories are intentionally untracked. Do not add, delete or normalize them.
- Adjacent repositories contain unrelated work; treat them as read-only unless an interface defect is proven.

## Verified baseline

Live command used successfully on the workstation:

```bash
./scripts/start-live-stack.sh \
  --camera 2 \
  --scene bands-v1 \
  --beacon-mute \
  --pads-view harmocap \
  --shaper-device "R24 Analog Stereo"
```

Relevant run evidence:

```text
rehearsal/artifacts/live-20260922T015050/
```

Observed:

- all runtime readiness checks completed;
- HarMoCAP produced 1,044 valid frames;
- person-count histogram was `{0: 387, 1: 650, 2: 7}`;
- instrument audit contained 508 events;
- non-zero harmonic activity was recorded for source slots 0, 1, 2 and 3;
- baseline tests: `162 passed, 4 subtests passed`.

This is encouraging but not sufficient to close sustained simultaneous two-person verification: only seven frames contained two tracked people.

## Known defect

The live sound path continued, but the background status writer died:

```text
Exception in thread rehearsal-status
KeyError: 'routes'
  rehearsal/weaver_runtime.py:847 -> engine.snapshot()
  src/harmonic_weaver/engine/core.py:1299
```

The active geometry scene has `geometry_routes`, while `Engine.snapshot()` indexes `active["routes"]` unconditionally.

## Audited implementation status

The Codex candidate was reviewed before integration. The audit retained the
bounded production changes and restored four unrelated HTTP/WebSocket tests
that Codex had weakened while working around its sandbox:

- geometry-scene snapshots/status payloads no longer crash on `bands-v1`; route
  snapshots for geometry scenes are built from active compiled routes and
  include the same runtime fields as conventional route scenes;
- conventional route-scene, HTTP and WebSocket behavior retains its original
  integration coverage;
- deterministic two-person × two-hand coverage proves S0–S3 can activate
  independently, one hand can move N1→N3 without cross-talk, and removing
  person slot 1 releases only S2/S3;
- `python -m rehearsal.analyze_bands_artifact <artifact-dir>` emits compact
  evidence by batching writes per frame timestamp and tracking `(S, N)` state;
  scene initialization resets are not misreported as harmonic transitions;
- synthetic analyzer fixtures contain no participant data.

The orchestrator ran the corrected analyzer on `live-20260922T015050`: 1,044
frames (0:387, 1:650, 2:7), 508 Shaper events, activity on all four intended
source slots, 172 true frame-level harmonic transitions, 18 route-reset zeros,
and zero ambiguous state changes. No new live camera, OSC, audio, or listening
verification is claimed.

## Iteration 1 — trustworthy geometry-scene status

1. Reproduce the failure in a focused automated test.
2. Update snapshot/runtime-status behavior so geometry scenes remain observable without regressing conventional route scenes.
3. Represent geometry-route runtime state meaningfully. Do not hide the bug behind a broad exception handler or an empty fabricated success.
4. Add coverage for the actual status-writer call path.
5. Run focused tests, then the full suite.
6. Commit this iteration as a coherent change with documentation/evidence updates.

Exit conditions:

- no snapshot exception with `bands-v1` or an equivalent geometry fixture;
- status output can continue refreshing;
- conventional `routes` snapshots retain their tested behavior;
- full suite passes.

## Iteration 2 — deterministic two-person polyphony evidence

1. Build a deterministic two-person × two-hand test or replay fixture at the harmonic-weaver boundary.
2. Prove four independent source slots, no cross-talk and selective release when one person disappears.
3. Add a small artifact-analysis command or script that accepts a live-run artifact directory and emits compact JSON evidence: frame totals, person-count histogram, active person/hand/source slots, harmonic transitions and reset/release outcomes.
4. Keep camera/pose/calibration ownership in HarMoCAP and synthesis ownership in harmonic-shaper.
5. Run focused tests, then the full suite.
6. Commit this iteration separately and update the issue with exact evidence.

Exit conditions:

- automated coverage proves independent four-source behavior;
- the analyzer is documented and tested;
- no participant images or personal data are copied into fixtures or commits;
- live-human/audio confirmation remains listed as a human gate, not claimed by automation.

## Delivery

At the end, provide:

- the commits produced per iteration;
- files changed and why;
- focused and full test results;
- analyzer invocation and output from the existing run artifact;
- any interface changes needed in HarMoCAP or harmonic-shaper;
- exact remaining manual live test, preferably a 30–60 second two-person protocol;
- an update/comment on issue #4.

Do not merge, push, close the issue or rewrite existing history without Nicolás's explicit approval.
