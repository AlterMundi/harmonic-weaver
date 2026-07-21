"""derivative transform: causal trailing difference → signed velocity.

Exercises compiler validation (window_ms > 0, max_abs > 0, max_dt_ms >= 0),
static range [-max_abs, +max_abs], and the stateful runtime in evaluate_route.

Destination is voice_pan with an expanded argument range so signed velocities
with |v| > 1 fit the instrument argument without a post scale_range.
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

# Widen pan so derivative max_abs can exceed the stock [-1, 1] for unit tests.
INSTRUMENT = instrument_manifest()
for _cap in INSTRUMENT["capabilities"]:
    if _cap["name"] == "voice_pan":
        _cap["arguments"][0]["range"] = [-100.0, 100.0]
MANIFESTS = {"synth": INSTRUMENT}
CHANNELS = {"sensor.pos": (0.0, 10.0)}
TOL = 1e-6


def _destination() -> dict:
    return {
        "instrument_id": "synth",
        "capability": "voice_pan",
        "bindings": {"N": 0},
        "argument": "pan",
    }


def _safety() -> dict:
    return {destination_key(_destination()): 0.0}


def _compile(transforms: list[dict], validity: dict | None = None):
    route = {
        "route_id": "pos-derivative",
        "route_version": 1,
        "enabled": True,
        "inputs": [{"channel": "sensor.pos"}],
        "transforms": transforms,
        "destination": _destination(),
        "validity": validity
        or {"held": "accept", "min_confidence": 0.0, "invalid": "suppress"},
    }
    return compile_route(route, CHANNELS, MANIFESTS, _safety(), "scene.routes[0]")


def _values(pos: float, now_us: int, state: str = OBSERVED) -> dict:
    return {
        "sensor.pos": ValueEnvelope(pos, state, 1.0, now_us, now_us),
    }


def _deriv(**params) -> list[dict]:
    params.setdefault("window_ms", 40.0)
    params.setdefault("max_abs", 10.0)
    params.setdefault("max_dt_ms", 1000.0)
    return [{"type": "derivative", **params}]


def test_static_range_is_plus_minus_max_abs():
    compiled = _compile(_deriv(max_abs=2.5))
    assert compiled.static_range == (-2.5, 2.5)


def test_rejects_max_abs_zero():
    with pytest.raises(Exception):
        _compile(_deriv(max_abs=0.0))


def test_rejects_negative_max_abs():
    with pytest.raises(Exception):
        _compile(_deriv(max_abs=-1.0))


def test_rejects_window_ms_zero():
    with pytest.raises(Exception):
        _compile(_deriv(window_ms=0.0))


def test_rejects_negative_max_dt_ms():
    with pytest.raises(Exception):
        _compile(_deriv(max_dt_ms=-1.0))


def test_first_input_emits_zero():
    compiled = _compile(_deriv(max_abs=10.0))
    rt = RouteRuntime()
    value, reason = evaluate_route(compiled, rt, _values(3.0, 0), 0)
    assert reason == "usable"
    assert abs(value - 0.0) < TOL


def test_linear_ramp_slope_two():
    # Position advances by 0.2 every 100 ms → slope 2.0 units/s.
    compiled = _compile(_deriv(max_abs=10.0, max_dt_ms=10_000.0))
    rt = RouteRuntime()
    step_us = 100_000  # 0.1 s
    pos = 0.0
    now = 0
    # Seed history on the first sample (output 0).
    v0, reason = evaluate_route(compiled, rt, _values(pos, now), now)
    assert reason == "usable"
    assert abs(v0 - 0.0) < TOL
    for _ in range(5):
        now += step_us
        pos += 0.2
        value, reason = evaluate_route(compiled, rt, _values(pos, now), now)
        assert reason == "usable"
        assert abs(value - 2.0) < TOL


def test_step_spike_clamped_by_max_abs():
    # Step 0 → 5 over 100 ms: raw derivative = 5 / 0.1 = 50, clamped by max_abs.
    compiled = _compile(_deriv(max_abs=8.0, max_dt_ms=10_000.0))
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.0, 0), 0)
    value, reason = evaluate_route(compiled, rt, _values(5.0, 100_000), 100_000)
    assert reason == "usable"
    assert abs(value - 8.0) < TOL


def test_gap_clamps_dt_no_unbounded_spike():
    # Gap of 500 ms with max_dt_ms=100: dt used is 0.1 s, not 0.5 s.
    # Position jump 0 → 5 → raw with clamped dt = 50; max_abs bounds the spike.
    compiled = _compile(_deriv(max_abs=12.0, max_dt_ms=100.0))
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.0, 0), 0)
    value, reason = evaluate_route(compiled, rt, _values(5.0, 500_000), 500_000)
    assert reason == "usable"
    # dt clamp → 50, then max_abs → 12. Must not report the unclamped 5/0.5 = 10
    # as if it ignored max_abs, and must stay within ±max_abs.
    assert abs(value - 12.0) < TOL
    assert abs(value) <= 12.0 + TOL
