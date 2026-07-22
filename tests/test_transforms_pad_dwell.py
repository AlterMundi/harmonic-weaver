"""pad_dwell transform: debounce a discrete (or pseudo-discrete) value.

Holds the committed output until the input has been different for at
least `dwell_ms`, then commits the new value in a single step. On cold
start, emits the input immediately (no artificial latency on first
sample). Optional `min_change_ms` rejects commits arriving too soon
after the previous commit (sub-frame noise guard).
"""

from __future__ import annotations

import pytest

from harmonic_weaver.engine.compiler import (
    RouteRuntime,
    compile_route,
    destination_key,
    evaluate_route,
)
from harmonic_weaver.engine.model import OBSERVED, ValueEnvelope

from engine_fixtures import instrument_manifest


INSTRUMENT = instrument_manifest()
MANIFESTS = {"synth": INSTRUMENT}
CHANNELS = {"sensor.pad": (0.0, 31.0)}
TOL = 1e-9


def _destination() -> dict:
    # voice_phase accepts [0, 360], so the wider pad index range fits without
    # triggering the route's output-range check.
    return {
        "instrument_id": "synth",
        "capability": "voice_phase",
        "bindings": {"N": 0},
        "argument": "phase_degrees",
    }


def _safety() -> dict:
    return {destination_key(_destination()): 0.0}


def _compile(transforms: list[dict] | None = None, validity: dict | None = None):
    return compile_route(
        {
            "route_id": "dwell",
            "route_version": 1,
            "enabled": True,
            "inputs": [{"channel": "sensor.pad"}],
            "transforms": transforms or [{"type": "pad_dwell", "dwell_ms": 80.0}],
            "destination": _destination(),
            "validity": validity
            or {"held": "accept", "min_confidence": 0.0, "invalid": "suppress"},
        },
        CHANNELS,
        MANIFESTS,
        _safety(),
        "scene.routes[0]",
    )


def _values(v: float, now_us: int) -> dict:
    return {"sensor.pad": ValueEnvelope(v, OBSERVED, 1.0, now_us, now_us)}


def test_static_range_preserved():
    compiled = _compile()
    assert compiled.static_range == (0.0, 31.0)


def test_zero_dwell_accepted_only_min_change_active():
    # dwell_ms=0 is allowed: the debounce window collapses; only the
    # min_change_ms anti-bounce remains. Confirm compile accepts it.
    compiled = _compile(
        [{"type": "pad_dwell", "dwell_ms": 0.0, "min_change_ms": 20.0}]
    )
    assert compiled.static_range == (0.0, 31.0)


def test_rejects_negative_dwell():
    with pytest.raises(Exception):
        _compile([{"type": "pad_dwell", "dwell_ms": -1.0}])


def test_rejects_negative_min_change_ms():
    with pytest.raises(Exception):
        _compile(
            [{"type": "pad_dwell", "dwell_ms": 80.0, "min_change_ms": -1.0}]
        )


def test_cold_start_emits_input_immediately():
    # First sample: no history → emit immediately, do NOT wait dwell_ms.
    compiled = _compile()
    rt = RouteRuntime()
    value, reason = evaluate_route(compiled, rt, _values(7.0, 0), 0)
    assert reason == "usable"
    assert value == 7.0


def test_held_value_persists_when_input_unchanged():
    compiled = _compile()
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(7.0, 0), 0)
    v2, _ = evaluate_route(compiled, rt, _values(7.0, 50_000), 50_000)
    v3, _ = evaluate_route(compiled, rt, _values(7.0, 100_000), 100_000)
    assert v2 == 7.0
    assert v3 == 7.0


def test_change_held_until_dwell_elapses():
    # Flip 7 → 12: output must remain 7 for at least 80 ms after the change
    # is first observed, then commit to 12.
    compiled = _compile()
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(7.0, 0), 0)
    v1, _ = evaluate_route(compiled, rt, _values(12.0, 10_000), 10_000)
    v2, _ = evaluate_route(compiled, rt, _values(12.0, 50_000), 50_000)
    v3, _ = evaluate_route(compiled, rt, _values(12.0, 80_001), 80_001)
    assert v1 == 7.0  # still held
    assert v2 == 7.0  # still held
    assert v3 == 12.0  # committed


def test_rapid_oscillation_does_not_flicker():
    # Jitter inside the dwell window: input flips every 5 ms for 30 ticks
    # (150 ms) but the dwell is 200 ms → held value must remain stable the
    # entire time. Then a sustained value commits once the dwell elapses.
    compiled = _compile([{"type": "pad_dwell", "dwell_ms": 200.0}])
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(5.0, 0), 0)
    held = 5.0
    for tick in range(1, 30):
        target = 25.0 if tick % 2 == 1 else 5.0
        now = tick * 5_000
        ret = evaluate_route(compiled, rt, _values(target, now), now)
        v = ret[0]
        reason = ret[1]
        assert v == held, f"tick={tick} target={target} v={v!r} reason={reason!r} held={held!r}"
    # After dwelling 200 ms from the last commit (which was at t=0),
    # a sustained value commits.
    final_target = 25.0
    ret = evaluate_route(
        compiled, rt, _values(final_target, 5_000 * 30 + 200_000), 5_000 * 30 + 200_000
    )
    assert ret[0] == final_target


def test_min_change_ms_blocks_bounce():
    # Two commits 5 ms apart, min_change_ms=20 → second blocked.
    compiled = _compile(
        [{"type": "pad_dwell", "dwell_ms": 0.0, "min_change_ms": 20.0}]
    )
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(1.0, 0), 0)         # cold → commit 1
    v1, _ = evaluate_route(compiled, rt, _values(2.0, 5_000), 5_000)   # 5 ms < 20 → hold
    v2, _ = evaluate_route(compiled, rt, _values(2.0, 25_000), 25_000)  # 20 ms ok → commit 2
    v3, _ = evaluate_route(compiled, rt, _values(3.0, 28_000), 28_000)  # 3 ms after 2 → hold
    v4, _ = evaluate_route(compiled, rt, _values(3.0, 50_000), 50_000)  # 25 ms after 2 → commit 3
    assert v1 == 1.0
    assert v2 == 2.0
    assert v3 == 2.0
    assert v4 == 3.0


def test_min_change_ms_default_is_zero():
    # No min_change_ms → equivalent to 0; commit as soon as dwell is over.
    compiled = _compile([{"type": "pad_dwell", "dwell_ms": 50.0}])
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(3.0, 0), 0)
    v1, _ = evaluate_route(compiled, rt, _values(9.0, 60_000), 60_000)
    assert v1 == 9.0


def test_no_smoothing_in_output_chain():
    # Two consecutive different values within the dwell: output does NOT
    # interpolate; it stays exactly on the held integer until commit.
    compiled = _compile([{"type": "pad_dwell", "dwell_ms": 100.0}])
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.0, 0), 0)
    for tick, val in enumerate([5.5, 7.7, 9.3, 11.0], start=1):
        v, _ = evaluate_route(compiled, rt, _values(val, tick * 10_000), tick * 10_000)
        assert v == 0.0  # held, never interpolated
    v_final, _ = evaluate_route(compiled, rt, _values(11.0, 200_000), 200_000)
    assert v_final == 11.0  # commit only after dwell elapsed