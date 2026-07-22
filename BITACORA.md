# Bitácora — harmonic-weaver

- 2026-07-22: **Pads v1 live-working**. `bin_2d` spatial aggregator operator (cols×rows serpentine grid). Scene `pads-v1`: 6 aggregators (hand X/Y positions + `hand_r_pad`/`hand_l_pad` via bin_2d), 64 routes (right→`harmonic_envelope`, left→`harmonic_gain`). Safety profile extended to N=1..32. Overlay HTML page + HarMoCAP window overlay with 4×8 grid. `start-live-stack.sh` auto-refreshes Shaper editable install; pgrp-based cleanup prevents orphaned subprocesses. 120 tests pass. Branch `main`.
- 2026-07-22: **Shaper polyphonic gain**: 1/√N ducking prevents saturation when multiple harmonics active. Attack 30ms, release 250ms. Voice deactivation no longer zeroes gain instantly — lets release envelope fade out. Branch `main` (harmonic-shaper repo).
- 2026-07-22: **HarMoCAP pad overlay**: 4×8 serpentine grid rendered directly on camera window via OpenCV. `pad_from_xy()` uses pixel-space coords matching skeleton rendering. Only focused person shown (matches Weaver's focus gate). Camera C920e v4l2 fast-mode re-applied after first frame for 30fps low-latency. Branch `main` (HarMoCAP repo).
- 2026-07-22: Merge Annie's PR #3: safety defaults for `harmonic_phase` (N=1..5→0.0) + `master_gain` (→0.8). Clean merge from `feat/shaper-safety-phase-master`.
- 2026-07-21: extend `shaper_safety_profile` with reset defaults for `harmonic_phase` (N=1..5 → 0.0) and `master_gain` (→ 0.8). Branch `feat/shaper-safety-phase-master`.
- 2026-07-21: multi-body scene for `instrumento_v1_mvp`: `all_bodies_nose_y`→ceiling; `all_bodies_tempo`→clock; focused body→arp H=0 (R) + H=1 (L); slot_1→arp H=2 (R) + H=3 (L). 104 tests + 4 subtests. Branch `main`.
- 2026-07-21: add `instrumento_v1_mvp` scene + offline `--scene`/`--replay` path. 95 tests + 4 subtests. Branch `main`.
- 2026-07-21: add `derivative` transform (causal trailing difference → signed velocity). Tests in `tests/test_transforms_derivative.py`. Branch `main`.
- 2026-07-21: add `slew_limiter` transform (rate-limited chase). 8 tests in `tests/test_transforms_slew.py`. Branch `main`.
- 2026-07-19: add `phase_accumulator` transform (velocity→wrapped phase integrator). 10 tests, docs. Branch `feat/phase-accumulator-transform`.
- 2026-07-19: Event-demo and sparse scenes route HarMoCAP through `harmonic_envelope`.
- 2026-07-19: T4.5 rehearsal PASS (46/46 assertions, 125s, 96% non-silence).
- 2026-07-19: Live camera→HarMoCAP→Weaver→Shaper/R24 audibly confirmed.
- 2026-07-18: repo scaffolded.
