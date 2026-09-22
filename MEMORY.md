# Harmonic Weaver — Project Memory

## Current State (2026-09-21)

### Branch: feat/geometry-activation

**Completed:**
- Vertical bands geometry (bands-v1) with symmetric activation
- `abs` operator in compiler for symmetric band computation
- Per-slot `band_span` calibration from shoulder width (×2.5)
- Lazy calibration update (only when shoulders change >10%)
- `raw_keypoints` field in PersonState for correct skeleton overlay
- PAD_HUES color scheme for bands (same as pads mode)
- Active harmonic highlighting (alpha 0.50 + white border)
- 162 weaver tests passing
- Live `bands-v1` sound path verified through HarMoCAP → Weaver → Shaper/R24

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
- Full suite: 162 passed, 4 subtests passed
- Audio remained functional, but the `rehearsal-status` thread crashed in
  `Engine.snapshot()` because geometry scenes expose `geometry_routes`, not
  `routes`

### Current Work

- Fix geometry-scene runtime snapshots/status refresh without regressing route scenes
- Add deterministic two-person × two-hand polyphony and selective-release coverage
- Add a machine-readable analyzer for live-run polyphony evidence
- Repeat a sustained 30–60 second two-person live/audio verification
- Consider adding y_effect back (currently disabled in bands-v1)

Canonical engineering task: https://github.com/AlterMundi/harmonic-weaver/issues/4

Codex handoff: `docs/CODEX_HANDOFF_BANDS_V1.md`

### Key Files

- `src/harmonic_weaver/engine/geometry_bands.py` — vertical bands expander
- `src/harmonic_weaver/engine/geometry_toolkit.py` — shared toolkit (band_zone_aggregator_symmetric)
- `src/harmonic_weaver/engine/compiler.py` — abs operator, geometry dispatch
- `rehearsal/scenes/bands-v1.scene.json` — 8-band symmetric scene
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
