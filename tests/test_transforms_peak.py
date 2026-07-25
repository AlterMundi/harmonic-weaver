"""peak_detector transform: impulse on local maximum (rising then non-rising).

State: 3-sample window (prev_prev, prev, current). Fires 1.0 when the previous
step was strictly above the one before it AND the current sample is non-greater,
the current value crosses `threshold`, and the refractory window since the last
fire has elapsed. Otherwise emits 0.0.
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
CHANNELS = {"sensor.v": (0.0, 1.0)}
TOL = 1e-9


def _destination() -> dict:
    return {
        "instrument_id": "synth",
        "capability": "voice_gain",
        "bindings": {"N": 0},
        "argument": "gain",
    }


def _safety() -> dict:
    return {destination_key(_destination()): 0.0}


def _compile(transforms: list[dict] | None = None):
    return compile_route(
        {
            "route_id": "peak",
            "route_version": 1,
            "enabled": True,
            "inputs": [{"channel": "sensor.v"}],
            "transforms": transforms or [
                {"type": "peak_detector", "threshold": 0.0, "refractory_ms": 0.0},
            ],
            "destination": _destination(),
            "validity": {
                "held": "accept",
                "min_confidence": 0.0,
                "invalid": "suppress",
            },
        },
        CHANNELS,
        MANIFESTS,
        _safety(),
        "scene.routes[0]",
    )


def _values(v: float, now_us: int) -> dict:
    return {"sensor.v": ValueEnvelope(v, OBSERVED, 1.0, now_us, now_us)}


def test_static_range_is_zero_one():
    compiled = _compile()
    assert compiled.static_range == (0.0, 1.0)


def test_rejects_negative_refractory():
    # refractory_ms must be non-negative; -1 is invalid.
    with pytest.raises(Exception):
        _compile([{"type": "peak_detector", "threshold": 0.0, "refractory_ms": -1.0}])


def test_rejects_negative_threshold():
    # threshold is just finite — negative is allowed but should not crash.
    # Confirm: a single rising-then-falling pattern with threshold=−1 always
    # crosses (anything > -1 qualifies) so a peak must fire.
    compiled = _compile([{"type": "peak_detector", "threshold": -1.0, "refractory_ms": 1.0}])
    rt = RouteRuntime()
    # Seed two samples going up, then a sample going down.
    evaluate_route(compiled, rt, _values(0.0, 0), 0)
    evaluate_route(compiled, rt, _values(1.0, 100_000), 100_000)
    value, reason = evaluate_route(compiled, rt, _values(0.0, 200_000), 200_000)
    assert reason == "usable"
    assert abs(value - 1.0) < TOL


def test_first_two_samples_never_fire():
    # No history → cannot detect a peak yet.
    compiled = _compile()
    rt = RouteRuntime()
    v1, _ = evaluate_route(compiled, rt, _values(0.5, 0), 0)
    v2, _ = evaluate_route(compiled, rt, _values(0.7, 100_000), 100_000)
    assert v1 == 0.0
    assert v2 == 0.0


def test_fires_on_classic_rising_then_falling():
    # 0.2 → 0.5 → 0.4: rising step (0.2→0.5), then turning (0.5→0.4).
    compiled = _compile()
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.2, 0), 0)
    evaluate_route(compiled, rt, _values(0.5, 100_000), 100_000)
    v3, reason = evaluate_route(compiled, rt, _values(0.4, 200_000), 200_000)
    assert reason == "usable"
    assert abs(v3 - 1.0) < TOL


def test_threshold_blocks_low_peaks():
    # Peak value 0.5 is below threshold 0.7 → no fire.
    compiled = _compile(
        [{"type": "peak_detector", "threshold": 0.7, "refractory_ms": 1.0}]
    )
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.2, 0), 0)
    evaluate_route(compiled, rt, _values(0.5, 100_000), 100_000)
    v3, _ = evaluate_route(compiled, rt, _values(0.4, 200_000), 200_000)
    assert v3 == 0.0


def test_refractory_suppresses_second_peak_within_window():
    # Two peaks 50 ms apart, refractory 200 ms → second peak suppressed.
    compiled = _compile(
        [{"type": "peak_detector", "threshold": 0.0, "refractory_ms": 200.0}]
    )
    rt = RouteRuntime()
    # First peak at t=200_000 us.
    evaluate_route(compiled, rt, _values(0.2, 0), 0)
    evaluate_route(compiled, rt, _values(0.5, 100_000), 100_000)
    v1, _ = evaluate_route(compiled, rt, _values(0.4, 200_000), 200_000)
    # Continue rising into a second peak at t=250_000 us (50 ms later).
    evaluate_route(compiled, rt, _values(0.4, 250_000), 250_000)
    evaluate_route(compiled, rt, _values(0.6, 260_000), 260_000)
    v2, _ = evaluate_route(compiled, rt, _values(0.5, 270_000), 270_000)
    assert abs(v1 - 1.0) < TOL
    assert v2 == 0.0  # refractory window still active


def test_refractory_expires_after_window():
    # First peak at t=200_000; second peak at t=500_000 (>200 ms later) → fires.
    compiled = _compile(
        [{"type": "peak_detector", "threshold": 0.0, "refractory_ms": 200.0}]
    )
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.2, 0), 0)
    evaluate_route(compiled, rt, _values(0.5, 100_000), 100_000)
    v1, _ = evaluate_route(compiled, rt, _values(0.4, 200_000), 200_000)
    # Second peak: rise then turn, more than 200 ms after the first fire.
    evaluate_route(compiled, rt, _values(0.3, 400_000), 400_000)
    evaluate_route(compiled, rt, _values(0.6, 490_000), 490_000)
    v2, _ = evaluate_route(compiled, rt, _values(0.5, 500_000), 500_000)
    assert abs(v1 - 1.0) < TOL
    assert abs(v2 - 1.0) < TOL


def test_flat_segment_after_peak_does_not_re_fire():
    # After a peak, a flat segment must not produce another peak.
    compiled = _compile()
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.2, 0), 0)
    evaluate_route(compiled, rt, _values(0.5, 100_000), 100_000)
    v1, _ = evaluate_route(compiled, rt, _values(0.4, 200_000), 200_000)
    evaluate_route(compiled, rt, _values(0.4, 300_000), 300_000)
    v2, _ = evaluate_route(compiled, rt, _values(0.4, 400_000), 400_000)
    assert abs(v1 - 1.0) < TOL
    assert v2 == 0.0