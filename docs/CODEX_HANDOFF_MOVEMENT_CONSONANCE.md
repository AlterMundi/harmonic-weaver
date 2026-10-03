# Codex Handoff — movement-consonance research and driver v1

## Mission

Continue the `movement-consonance` lane: a NEW control mode for the Beacon
instrument where movement QUALITY (not position over virtual keyboards) drives
the sound. Per-zone kinematics produce a detune value `d ∈ [-1,1]` per harmonic
of the natural series; `d` slides each partial between the tuned harmonic
(`d=0`, series of `f1`) and the odd multiples of `f1/2` (`|d|=1` — just
intervals: 3/2, 5/4, 7/4 ...). A configurable "snap" well keeps small
deviations on the natural series; the movement deviation must exceed an escape
threshold to leave it. This is Nicolás' explicit requirement: continuous, NOT
a grid, with a tunable snap level.

Read, in order, before editing anything:

1. `research/movement-consonance/README.md` — pack index
2. `research/movement-consonance/ADDENDUM-f1-2-grid.md` — the f1/2-grid
   discovery + Nicolás' clarifications (inertia-relative dissonance, detune as
   "other note", snap semantics). THIS is the design ground truth.
3. `research/movement-consonance/consonance/README.md` — driver v1 docs,
   pipeline, verified evidence, known compromises
4. `MEMORY.md` §Movement-consonance and `BITACORA.md` tail

Deeper context (only as needed): `SYNTHESIS.md` (2-page distillate),
`CROSS_REPORT.md` (dense, tagged [R1..R5]), `NARRATED_REPORT.md` (prose),
`agent_reports/01..05` (raw research, ~55 KB each).

## Repository and branch state

- Workspace: `~/Projects/harmonic-weaver`
- Branch: `feat/geometry-activation` (local; bands-v1 work shares this branch —
  do not rebase or clean it)
- The whole research pack lives under `research/movement-consonance/` and is
  committed; generated `rehearsal/artifacts/` dirs are intentionally untracked —
  do not add, delete or normalize them.
- Driver v1 prototype: `research/movement-consonance/consonance/` (metrics.py +
  driver.py, Python stdlib only, no deps).
- Adjacent repos are read-only unless an interface defect is proven:
  `~/Projects/harmonic-shaper`, `~/Projects/HarMoCAP`, `~/Projects/beacon-spatial`.

## Verified baseline (reproduce before changing anything)

Driver v1 was verified end-to-end on 2026-09-27 (no audio; state-inspection):

```bash
# terminal 1 — shaper in silent slave mode (entry point, NOT python -m:
# harmonic_shaper/main.py has no __main__ block and exits 0 silently)
cd ~/Projects/harmonic-shaper && \
  .venv/bin/harmonic-shaper --no-audio --slave --api-port 8124

# terminal 2 — replay a recorded HarMoCAP session through the driver
cd ~/Projects/harmonic-weaver/research/movement-consonance/consonance && \
  python3 driver.py --source ~/Projects/HarMoCAP/examples/session_v1.jsonl \
    --snap 0.6 --f1 40.4 --rate 5.0

# terminal 3 — observe detuned voices live
curl -s http://127.0.0.1:8124/api/state | \
  python3 -c "import json,sys; d=json.load(sys.stdin); \
  print({k: round(v['freq'],2) for k,v in d['voices'].items() if v['active']})"
```

Expected: 9 voices (H1..H9) with frequencies OFF the nominal `n·f1` grid
(e.g. H6 ≈ 249.9 Hz vs nominal 242.4 at f1=40.4), gains tracking movement,
`voice_off` releasing zones, `/beacon/panic` cleaning on driver exit.
Dry table (no shaper needed): add `--dry` to the driver.

## Architecture decision already made (do not re-litigate without Nicolás)

v1 drives the shaper through its EXISTING optional `/beacon/*` slave port
(9001, flag `--slave`) using `voice_on`/`voice_freq` with arbitrary frequencies
and stable `voice_id = 7000+n`. The shaper engine already renders
`params.freq` per block with continuous phase (`audio_engine.py` L242,
L268-270), and the `f1·n` resets only touch envelope-owned voices
(`voice_id = -10000-n`). So the external driver owns its voices with continuous
detune: ZERO shaper changes, no contract bump, goldens untouched.
A native `/digital/harmonic/{n}/detune` capability is phase 2 (contract +
golden + tests), only after the design settles through exploration.

## Open design decisions (need Nicolás, not you)

1. Anatomical mapping: current table is midline-virtual (hip_mid=H1,
   under_navel=H2, navel=H3 interpolated; shoulders=H4, head=H5; limbs by
   distality knees=H6, ankles=H7, elbows=H8, wrists=H9). The documented
   alternative is kinetic-chain ordering (ankles→knees→pelvis→spine→...→wrists
   by energy-flow distance). ADDENDUM §B argues the chain variant aligns
   harmonics with impulse propagation — Nicolás has NOT chosen yet.
2. Snap modes: `off | series | grid | both` are implemented; which becomes the
   default scene behavior is an exploration outcome.
3. Metric weights (`--w-surprise`, `--w-brake`, `--theta`) are to be CALIBRATED
   by the baseline experiment (Spearman ρ against blind human ratings), not
   hand-tuned. Do not "improve" them a priori.

## Next steps (in priority order)

1. **Listen to it.** Run the baseline with real audio (shaper WITHOUT
   `--no-audio`, R24 or built-in output) against `session_v1.jsonl` and a live
   camera (`--source osc` while HarMoCAP runs). Musical judgment first, code
   second.
2. **Baseline experiment protocol** (ADDENDUM §C / agent_reports/05 §C.4):
   collect 12-18 clips in 3 categories (expert consonant / neutral /
   deliberately dissonant by the SAME performer), run them offline through
   HarMoCAP `run_realtime.py --source video --record`, compute candidate
   metrics per clip, collect blind 1-7 ratings from ≥3 raters, Spearman ρ.
   The rope-flow footage is the nominated Jpsh! material (HIT manuscript L900).
3. Phase 2 only after Nicolás approves: native detune capability in the shaper
   contract; `consonance` scene in the weaver respecting the architecture rule
   (geometry returns TOPOLOGY only; activation owns routes and gains).

## Guardrails and known pitfalls

- OSC strings are NUL-terminated THEN padded to 4 bytes. The minimal encoder in
  `driver.py` had this bug (address decoded as `/beacon/voice/on,iffi`, message
  silently swallowed by the shaper's default handler — zero error, zero effect).
  If you touch `enc_msg`, decode-test with the kit codec:
  `sys.path.insert(0, '~/Projects/HarMoCAP/harmocap-nico-kit'); import osc_codec`.
- Velocities are in torso units T/s; accelerations are `dv/dt` — do NOT divide
  by T twice (past bug).
- Brake/pump character MODULATES deviation magnitude; it must never add a
  constant offset (quiet zones must sit at d≈0) — past bug.
- `voice_on` calls `record_strum()` in the shaper; gain updates are therefore
  throttled via `--gain-eps`. Do not raise voice_on rate to frame rate.
- Live wire mode implements stream_id reset + monotonic seq + 2 s lease, but
  NOT the strict hello/calibration handshake (the kit's
  `osc_receiver_example.py` does). Acceptable for exploration; flagged.
- 2D pose only: depth is lost; surprise/power are projections. The baseline
  will show how much this hurts.
- The research pack (`research/movement-consonance/*.md`) is a closed record:
  append new findings as new dated files or ADDENDUM sections; do not rewrite
  the agent_reports.
- Standing rule from Nicolás (NOW.md): preparing a handoff does NOT authorize
  launching external agents or creating clones; Codex normally works in this
  same workspace.

## Durable memory (shared being-level pool)

HMK pool `~/.agents/memory/compaii/agent-memory` — query on demand:

```bash
hmk memoryctl.py hybrid-pack --query "movement consonance driver f1/2 grid" --budget 1500 --limit 5
```

Key chapters: 187 (research pack closed + findings + pending decisions),
189 (ADDENDUM f1/2-grid discovery), 190 (driver v1 implementation + verification
+ the 4 bugs fixed). These chapters are visible to every CompAII embodiment.
