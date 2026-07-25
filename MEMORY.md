# Harmonic Weaver — Project Memory

## Current State (2026-07-25)

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

**Test Command:**
```bash
./scripts/start-live-stack.sh --scene bands-v1 --beacon-mute --pads-view harmocap
```

### Pending / Tomorrow

- Verify polyphony with multiple people (user asked about this)
- Check if HarMoCAP detects multiple skeletons correctly
- Verify shaper receives activations from multiple slots
- Consider adding y_effect back (currently disabled in bands-v1)

### Key Files

- `src/harmonic_weaver/engine/geometry_bands.py` — vertical bands expander
- `src/harmonic_weaver/engine/geometry_toolkit.py` — shared toolkit (band_zone_aggregator_symmetric)
- `src/harmonic_weaver/engine/compiler.py` — abs operator, geometry dispatch
- `rehearsal/scenes/bands-v1.scene.json` — 8-band symmetric scene
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
