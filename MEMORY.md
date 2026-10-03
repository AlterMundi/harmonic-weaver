# Harmonic Weaver — Project Memory

## Current State (2026-09-27)

### Movement-consonance lane (research closed, driver v1 verified)

- Research pack COMPLETE at `research/movement-consonance/` (5 raw reports +
  CROSS_REPORT + SYNTHESIS + NARRATED + ADDENDUM + bibliography, ~330 KB).
  Topic: new control mode where movement QUALITY drives detuning of the
  natural harmonic series; `f'(n,d) = f1·(n + d/2)`, `|d|=1` lands on the
  odd multiples of `f1/2` (just intervals). Snap = finite potential well,
  continuous escape (Nicolás: "continuo con nivel de snap, NO rejilla").
- Driver v1 prototype at `research/movement-consonance/consonance/`
  (metrics.py + driver.py, stdlib only). Verified end-to-end 2026-09-27:
  720 frames of HarMoCAP `session_v1.jsonl` → shaper `--no-audio --slave`
  → 9 detuned voices live in `/api/state` (−498 to +80 cents). Drives the
  shaper through the EXISTING `/beacon/*` slave port (voice_id 7000+n):
  zero shaper changes, no contract bump.
- Current mapping: hips F1, shoulders F2, knees F3, elbows F4, ankles F5,
  wrists F6. Six sustained shared voices; replaces the original nine zones.
- Current raw experiment supersedes the sustained-at-rest revision: snap=0,
  gain floor=0, no 200 ms output smoothing, no One-Euro pose filtering or
  held sound for missing joints. Shaper attack/release=0. Speed drives gain;
  stationary samples silence each zone immediately. Independent limb-side
  histories avoid fake motion when selecting a different side.
- Isolated experiment: `scripts/start-kinetic-consonance.sh` runs only
  HarMoCAP, consonance and Shaper; no spatializer, MIDI, ECG or Stage runtime.
  Recording is opt-in.
- Live launcher integration: `--scene kinetic-consonance` (alias `consonance`)
  runs the consonance controller INSTEAD OF the pads/bands runtime. Existing
  HarMoCAP camera window uses skeleton + external H1–H6 state, without pads.
  See `docs/KINETIC_CONSONANCE.md` for invocation and verification.
- Nicolás reports hearing the prior prototype test; source of that specific
  audible run is not independently established by the saved handoff.
- Codex handoff for this lane: `docs/CODEX_HANDOFF_MOVEMENT_CONSONANCE.md`
- HMK chapters (shared pool `~/.agents/memory/compaii`): 187, 189, 190.
- Open decisions for Nicolás: anatomical mapping (midline-virtual vs
  kinetic-chain), default snap mode, and metric weights — these are to be
  CALIBRATED by the baseline experiment (blind ratings + Spearman ρ), not
  hand-tuned.

## Previous State (2026-09-22)

### Branch: feat/geometry-activation

**Completed:**
- Vertical bands geometry (bands-v1) with symmetric activation
- `abs` operator in compiler for symmetric band computation
- Per-slot `band_span` calibration from shoulder width (×2.5)
- Lazy calibration update (only when shoulders change >10%)
- `raw_keypoints` field in PersonState for correct skeleton overlay
- PAD_HUES color scheme for bands (same as pads mode)
- Active harmonic highlighting (alpha 0.50 + white border)
- 169 weaver tests + 4 subtests passing
- Live `bands-v1` sound path verified through HarMoCAP → Weaver → Shaper/R24
- Geometry-scene snapshots/status payloads now expose compiled geometry routes
  with real runtime state instead of crashing on missing raw `routes`
- Deterministic two-person × two-hand engine-boundary coverage proves four
  independent `harmonic_source_envelope` source slots, a harmonic transition,
  and selective release
- Privacy-safe analyzer command:
  `python -m rehearsal.analyze_bands_artifact rehearsal/artifacts/<run-id>`
- Audited artifact analysis: 172 true frame-level transitions, 18 route-reset
  zeros, and no ambiguous source-state changes

**HarMoCAP Changes:**
- Pipeline computes per-slot `band_span` from shoulder distance
- Normalizes wrist X in bands mode: `abs(wrist_x - nose_x) / band_span`
- Overlay uses `raw_keypoints` for skeleton drawing (original coords)
- Bands overlay uses PAD_HUES colors, labels H1-H8

**Audio Routing:**
- 128 routes (8 slots × 16 routes: 2 hands × 8 bands)
- Source ID: `S = slot*2 + hand_side` (0=r, 1=l)
- Presence gate: `include_when: slot_N_present == 1`
- Shaper handles polyphony: max of source gains per harmonic

**Known-good live command:**
```bash
./scripts/start-live-stack.sh \
  --camera 2 \
  --scene bands-v1 \
  --beacon-mute \
  --pads-view harmocap \
  --shaper-device "R24 Analog Stereo"
```

**Latest evidence:**
- `rehearsal/artifacts/live-20260922T015050/`
- 1,044 HarMoCAP frames: 387 with 0 people, 650 with 1, 7 with 2
- 508 instrument output events; non-zero output observed on source slots 0–3
- Corrected analyzer: 172 frame-level harmonic transitions, 18 route-reset
  zeros, no ambiguous source-state changes
- Full canonical-tree suite: 169 tests + 4 subtests independently green after integration repair
- The original run's audio remained functional, but its `rehearsal-status`
  thread crashed in `Engine.snapshot()` because geometry scenes expose
  `geometry_routes`, not `routes`; the regression now has automated coverage

### Remaining Work

- Repeat a sustained 30–60 second two-person live/audio verification with
  camera, OSC, Shaper/R24 audio, and human/orchestrator confirmation
- Consider adding y_effect back (currently disabled in bands-v1)

Canonical engineering task: https://github.com/AlterMundi/harmonic-weaver/issues/4

Codex handoff: `docs/CODEX_HANDOFF_BANDS_V1.md`

### Key Files

- `src/harmonic_weaver/engine/geometry_bands.py` — vertical bands expander
- `src/harmonic_weaver/engine/geometry_toolkit.py` — shared toolkit (band_zone_aggregator_symmetric)
- `src/harmonic_weaver/engine/compiler.py` — abs operator, geometry dispatch
- `rehearsal/scenes/bands-v1.scene.json` — 8-band symmetric scene
- `rehearsal/analyze_bands_artifact.py` — compact JSON live-artifact analyzer
- `docs/CODEX_HANDOFF_BANDS_V1.md` — bounded two-iteration continuation
- `HarMoCAP/src/harmocap/pipeline.py` — band_span calibration, wrist normalization
- `HarMoCAP/scripts/run_realtime.py` — bands overlay rendering

### Architecture Notes

**Geometry/Activation Orthogonality:**
- Geometry returns topology only (zone layout)
- Activation owns routes and gains
- `mirror: bool` explicit in schema (bands are symmetric)

**Band Computation:**
- H1 = center (near nose), H8 = outermost (full arm reach)
- Both arms produce same harmonic (symmetric: `abs(offset)`)
- band_span adapts to person's position/size (shoulder width × 2.5)

**Visual/Audio Coordination:**
- Same `band_span` used for overlay rendering and audio routing
- Person plays same note regardless of distance from camera
- Calibration is lazy (updates only when torso size changes >10%)
