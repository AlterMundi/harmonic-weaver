# harmonic-weaver — Project Memory

> Last updated: 2026-07-24. Pads v2 on integration branch `feat/pads-v2`.

## Status

Critical-path engine of the beacon ecosystem. All core tasks complete (T1.1–T4.5).
**Pads v2** (cuerpo-como-instrumento with retrigger/pluck) on integration branch `feat/pads-v2`:
- Single-slot symmetric per-hand grid (hand_r → odd N, hand_l → even N).
- 64 routes: 16 envelope + 16 trigger per hand.
- New engine transforms: `radial_velocity`, `peak_detector`, `pad_dwell`.
- New Shaper capability: `harmonic_trigger` (pluck envelope on deceleration peak, contract id `cac459b4`).
- `--pads-view` flag on the launcher.
- Audio path switched from pw-jack to ALSA directly (R24 USB Audio stable).
- Orphan process reclaim on boot (no more manual port cleanup).
- 150 tests green. branch `feat/pads-v2` (NOT merged to main — pending user review).

## Key paths

| File | Role |
|------|------|
| `src/harmonic_weaver/engine/core.py` | WeaverEngine: sources, instruments, routes, aggregators, panic, stage WS |
| `src/harmonic_weaver/engine/compiler.py` | Scene/route/aggregator compilation, `bin_2d` operator |
| `src/harmonic_weaver/server.py` | FastAPI + Stage WS protocol + `/api/pads` endpoint |
| `src/harmonic_weaver/static/` | Patchbay + overlay (vanilla JS) |
| `src/harmonic_weaver/drivers/` | HarMoCAP, MIDI, ECG source drivers |
| `rehearsal/` | e2e rehearsal harness (runner, scenes, weaver_runtime, ecg_simulator) |
| `rehearsal/weaver_runtime.py` | Live runtime: installs instruments+gates+drivers, serves Stage WS |
| `rehearsal/scenes/pads_v1.scene.json` | Pads spatial grid: 4×8 serpentine→32 harmonics, 64 routes, 6 aggregators |

## Quick-start

```bash
# Shaper with pluck capability (MUST be on feat/pads-v2)
cd ~/Projects/harmonic-shaper && git checkout feat/pads-v2
# Weaver with all transforms + scene v2 + launcher fixes
cd ~/Projects/harmonic-weaver && git checkout feat/pads-v2

# Live stack with pads-v2 scene (harmonic switching + retrigger on deceleration)
./scripts/start-live-stack.sh --scene pads-v2 --beacon-mute --pads-view harmocap

# Stop
./scripts/start-live-stack.sh --stop latest
```

```bash
# Tests
PYTHONPATH=src /tmp/weaver-audit/bin/python -m pytest tests/ -q
# 150 passed, 1 skipped, 4 subtests
```

## Pads v1 — spatial grid mode (2026-07-22)

### Architecture
- **bin_2d aggregator**: maps (X,Y) → pad index 0..31 with serpentine layout (cols=4, rows=8)
- **Scene `pads-v1`**: 6 aggregators (hand positions + pad indices), 64 routes (32 per hand)
- **Right hand** → `harmonic_envelope` (voice activation with attack/release)
- **Left hand** → `harmonic_gain` (gain control)
- **Safety profile**: extended to N=1..32 for both envelope and gain
- **Shaper poly gain**: 1/√N ducking prevents saturation regardless of active voice count

### HarMoCAP overlay
- `scripts/run_realtime.py` renders 4×8 serpentine grid directly on camera window
- Uses same pixel-space coordinate math as skeleton for perfect alignment
- Only shows focused person (matches Weaver's focus gate)
- Camera C920e: v4l2 fast-mode applied after first frame (30fps, short exposure)

### Coordinate alignment notes
- HarMoCAP normalises X relative to height: `kp.x * h = pixel X` (NOT unit-normalised)
- `pad_from_xy()` in HarMoCAP uses pixel coords to match skeleton rendering exactly
- Weaver bin_2d uses `x_min=1.0, x_max=0.0` (X flip for mirror) and `y_min=1.0, y_max=0.0` (Y flip)
- Overlay grid renders with flipped rows: grid_row 0 (bottom of model) → canvas bottom

### Known issues / future
- Engine source lease no auto-recovery (STILL OPEN from S14)
- Smoothing 60ms + slew_limiter adds ~100ms latency between visual and audio
- Per-pad velocity/onset via hand acceleration (future card)
- Master gain route removed — poly gain handles clipping in Shaper

## bin_2d aggregator operator (2026-07-21)

- New aggregator operator mapping 2D spatial position → discrete bin index
- Parameters: `cols`, `rows`, `serpentine` (bool, default true), `x_min/x_max`, `y_min/y_max`
- Supports inverted ranges (min > max = axis flip)
- Exactly 2 input channels required
- Validation: `x_min ≠ x_max`, `y_min ≠ y_max`, `cols > 0`, `rows > 0`
- Tests: `tests/test_engine_derived_scenes.py` (5 bin_2d tests)

## Stateful transform resources

| Transform | Role | Docs/Tests |
|-----------|------|------------|
| `phase_accumulator` | velocity→wrapped phase (Latido laser/cymatics) | `docs/TRANSFORM_PHASE_ACCUMULATOR.md`, `tests/test_phase_accumulator.py` |
| `slew_limiter` | rate-limited chase (convergence primitive) | `tests/test_transforms_slew.py` |
| `derivative` | causal trailing diff (signed velocity from position) | `tests/test_transforms_derivative.py` |
| `beat_envelope` | trigger→decaying pulse | `tests/test_beat_envelope.py` |

## Live test findings (S13/S14)

- ROOT CAUSE of shaper voices not firing: `harmocap_manifest()` declared all features (0,1) but producer `verticality` is signed (-1,1). Fixed S14.
- LiveOSCTransport: fixed (dict serialization instead of asdict on mappingproxy).
- Engine source lease: expires permanently after 2500ms, no auto-recovery. STILL OPEN.
- RTX 2060 CUDA unstable: `CUDA_LAUNCH_BLOCKING=1` + supervised restart in start-live-stack.sh.

## Sibling repos

| Repo | Role | Key files |
|------|------|-----------|
| `harmonic-shaper` | Additive synth (OSC :9002, HTTP :8080) | `src/harmonic_shaper/state.py` (poly gain, voice mgmt), `config.py` (attack/release defaults) |
| `HarMoCAP` | Pose detection (camera→OSC :9100) | `scripts/run_realtime.py` (pad overlay), `src/harmocap/capture.py` (v4l2 fast mode) |
| `harmonic-beacon-tines` | Nature sound engine | — |
| `beacon-spatial` | Spatializer (SuperCollider) | — |
