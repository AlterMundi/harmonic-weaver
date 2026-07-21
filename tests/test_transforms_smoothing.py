"""smoothing transforms: one_pole / ramp with optional max_dt_ms gap clamp.

Exercises compiler validation (max_dt_ms > 0 when provided, None/absent ok),
and the stateful runtime: a large gap with max_dt_ms set must not jump toward
the target the way raw-dt (legacy) does.
"""

from __future__ import annotations

import math

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
CHANNELS = {"sensor.target": (0.0, 10.0)}
TOL = 1e-6


def _destination() -> dict:
    return {
        "instrument_id": "synth",
        "capability": "voice_phase",
        "bindings": {"N": 0},
        "argument": "phase_degrees",
    }


def _safety() -> dict:
    return {destination_key(_destination()): 0.0}


def _compile(transforms: list[dict], validity: dict | None = None):
    route = {
        "route_id": "target-smooth",
        "route_version": 1,
        "enabled": True,
        "inputs": [{"channel": "sensor.target"}],
        "transforms": transforms,
        "destination": _destination(),
        "validity": validity
        or {"held": "accept", "min_confidence": 0.0, "invalid": "suppress"},
    }
    return compile_route(route, CHANNELS, MANIFESTS, _safety(), "scene.routes[0]")


def _values(target: float, now_us: int, state: str = OBSERVED) -> dict:
    return {
        "sensor.target": ValueEnvelope(target, state, 1.0, now_us, now_us),
    }


def _smooth(kind: str = "one_pole", **params) -> list[dict]:
    params.setdefault("time_ms", 100.0)
    return [{"type": "smoothing", "kind": kind, **params}]


def _expected_one_pole(prev: float, target: float, dt_ms: float, time_ms: float) -> float:
    alpha = 1.0 - math.exp(-dt_ms / time_ms)
    return prev + alpha * (target - prev)


def _expected_ramp(prev: float, target: float, dt_ms: float, time_ms: float) -> float:
    alpha = min(1.0, dt_ms / time_ms)
    return prev + alpha * (target - prev)


def test_rejects_max_dt_ms_zero():
    with pytest.raises(Exception):
        _compile(_smooth(kind="one_pole", max_dt_ms=0.0))


def test_rejects_max_dt_ms_negative():
    with pytest.raises(Exception):
        _compile(_smooth(kind="ramp", max_dt_ms=-1.0))


def test_accepts_absent_max_dt_ms():
    compiled = _compile(_smooth(kind="one_pole", time_ms=50.0))
    assert compiled.static_range == (0.0, 10.0)


def test_one_pole_gap_clamped_by_max_dt_ms():
    # Seed at 0, then jump target to 10 after a 200 ms gap with max_dt_ms=50.
    # Alpha uses 50 ms, not 200 ms → no near-jump to 10.
    time_ms = 100.0
    max_dt_ms = 50.0
    compiled = _compile(
        _smooth(kind="one_pole", time_ms=time_ms, max_dt_ms=max_dt_ms)
    )
    rt = RouteRuntime()
    v0, reason0 = evaluate_route(compiled, rt, _values(0.0, 0), 0)
    assert reason0 == "usable"
    assert abs(v0 - 0.0) < TOL

    gap_us = 200_000  # 200 ms
    v1, reason1 = evaluate_route(compiled, rt, _values(10.0, gap_us), gap_us)
    assert reason1 == "usable"
    expected = _expected_one_pole(0.0, 10.0, max_dt_ms, time_ms)
    assert abs(v1 - expected) < TOL
    # Without clamp, dt=200 would almost reach target (alpha≈0.86); with clamp
    # alpha≈0.39 — output stays well below the unclamped result.
    unclamped = _expected_one_pole(0.0, 10.0, 200.0, time_ms)
    assert v1 < unclamped - 1.0
    assert v1 < 5.0  # no jump toward 10


def test_ramp_gap_clamped_by_max_dt_ms():
    time_ms = 100.0
    max_dt_ms = 50.0
    compiled = _compile(_smooth(kind="ramp", time_ms=time_ms, max_dt_ms=max_dt_ms))
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.0, 0), 0)
    gap_us = 200_000
    v1, reason = evaluate_route(compiled, rt, _values(10.0, gap_us), gap_us)
    assert reason == "usable"
    expected = _expected_ramp(0.0, 10.0, max_dt_ms, time_ms)
    assert abs(v1 - expected) < TOL
    # Unclamped ramp with dt=200ms and time_ms=100 → alpha=1, full jump to 10.
    assert abs(v1 - 10.0) > 1.0
    assert abs(v1 - 5.0) < TOL  # alpha = 50/100 = 0.5


def test_without_max_dt_ms_uses_raw_dt_one_pole():
    # Regression: absent max_dt_ms keeps legacy raw-dt behaviour.
    time_ms = 100.0
    compiled = _compile(_smooth(kind="one_pole", time_ms=time_ms))
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.0, 0), 0)
    gap_us = 200_000
    v1, reason = evaluate_route(compiled, rt, _values(10.0, gap_us), gap_us)
    assert reason == "usable"
    expected = _expected_one_pole(0.0, 10.0, 200.0, time_ms)
    assert abs(v1 - expected) < TOL


def test_without_max_dt_ms_uses_raw_dt_ramp():
    # Ramp with dt=200ms, time_ms=100 → alpha=1 → full jump (legacy).
    time_ms = 100.0
    compiled = _compile(_smooth(kind="ramp", time_ms=time_ms))
    rt = RouteRuntime()
    evaluate_route(compiled, rt, _values(0.0, 0), 0)
    gap_us = 200_000
    v1, reason = evaluate_route(compiled, rt, _values(10.0, gap_us), gap_us)
    assert reason == "usable"
    assert abs(v1 - 10.0) < TOL
