"""radial_velocity transform: clip01( sqrt((x1-x2)^2 + (y1-y2)^2) ).

Consumes the 4 route inputs as (x1, y1, x2, y2). No state. Output range
is always [0, 1] regardless of the input channels' declared ranges.

Replaces the need for an explicit `combine` operator in front of the
4-input route; the transform itself collapses the four channels into a
single scalar that downstream transforms can read as a float.
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
# Pixel-space style ranges; radial_velocity is range-agnostic.
CHANNELS = {
    "sensor.x1": (0.0, 1280.0),
    "sensor.y1": (0.0, 720.0),
    "sensor.x2": (0.0, 1280.0),
    "sensor.y2": (0.0, 720.0),
}
TOL = 1e-6


def _destination() -> dict:
    return {
        "instrument_id": "synth",
        "capability": "voice_gain",
        "bindings": {"N": 0},
        "argument": "gain",
    }


def _safety() -> dict:
    return {destination_key(_destination()): 0.0}


def _compile():
    return compile_route(
        {
            "route_id": "radial",
            "route_version": 1,
            "enabled": True,
            "inputs": [
                {"channel": "sensor.x1"},
                {"channel": "sensor.y1"},
                {"channel": "sensor.x2"},
                {"channel": "sensor.y2"},
            ],
            "transforms": [{"type": "radial_velocity"}],
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


def _values(x1: float, y1: float, x2: float, y2: float, now_us: int) -> dict:
    return {
        "sensor.x1": ValueEnvelope(x1, OBSERVED, 1.0, now_us, now_us),
        "sensor.y1": ValueEnvelope(y1, OBSERVED, 1.0, now_us, now_us),
        "sensor.x2": ValueEnvelope(x2, OBSERVED, 1.0, now_us, now_us),
        "sensor.y2": ValueEnvelope(y2, OBSERVED, 1.0, now_us, now_us),
    }


def test_static_range_is_zero_one():
    compiled = _compile()
    assert compiled.static_range == (0.0, 1.0)


def test_rejects_non_four_inputs():
    with pytest.raises(Exception):
        compile_route(
            {
                "route_id": "r",
                "route_version": 1,
                "enabled": True,
                "inputs": [{"channel": "sensor.x1"}],
                "transforms": [{"type": "radial_velocity"}],
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


def test_zero_distance_when_overlapping():
    compiled = _compile()
    rt = RouteRuntime()
    value, reason = evaluate_route(compiled, rt, _values(640.0, 360.0, 640.0, 360.0, 0), 0)
    assert reason == "usable"
    assert abs(value - 0.0) < TOL


def test_distance_3_4_5_triangle():
    # (x1,y1)=(0,0), (x2,y2)=(3,4) → sqrt(25)=5, clipped to 1.0.
    compiled = _compile()
    rt = RouteRuntime()
    value, reason = evaluate_route(compiled, rt, _values(0.0, 0.0, 3.0, 4.0, 0), 0)
    assert reason == "usable"
    assert abs(value - 1.0) < TOL


def test_unit_distance_in_pixel_space():
    # dx=1, dy=0 → 1.0 → clipped to 1.0 (large pixel ranges, small distance).
    compiled = _compile()
    rt = RouteRuntime()
    value, reason = evaluate_route(compiled, rt, _values(100.0, 50.0, 101.0, 50.0, 0), 0)
    assert reason == "usable"
    assert abs(value - 1.0) < TOL


def test_no_state_between_samples():
    # Re-evaluating with different inputs must NOT use prior state.
    compiled = _compile()
    rt = RouteRuntime()
    v1, _ = evaluate_route(compiled, rt, _values(0.0, 0.0, 0.0, 0.0, 0), 0)
    v2, _ = evaluate_route(compiled, rt, _values(10.0, 0.0, 0.0, 0.0, 100_000), 100_000)
    assert abs(v1 - 0.0) < TOL
    # 10 px in a 720-range axis → ~0.0139 (clipped to 0..1, not clipped).
    expected = min(1.0, 10.0 / math.sqrt(1.0))
    # Actually sqrt(dx^2+dy^2) = sqrt(100) = 10 → clipped to 1.
    assert abs(v2 - 1.0) < TOL


def test_known_distance_in_unit_square():
    # Both points inside [0,1]^2: dx=0.5, dy=0.5 → sqrt(0.5) ≈ 0.707.
    square_channels = {k: (0.0, 1.0) for k in CHANNELS}
    compiled = compile_route(
        {
            "route_id": "radial",
            "route_version": 1,
            "enabled": True,
            "inputs": [
                {"channel": "sensor.x1"},
                {"channel": "sensor.y1"},
                {"channel": "sensor.x2"},
                {"channel": "sensor.y2"},
            ],
            "transforms": [{"type": "radial_velocity"}],
            "destination": _destination(),
            "validity": {
                "held": "accept",
                "min_confidence": 0.0,
                "invalid": "suppress",
            },
        },
        square_channels,
        MANIFESTS,
        _safety(),
        "scene.routes[0]",
    )
    rt = RouteRuntime()
    value, _ = evaluate_route(
        compiled, rt,
        _values(0.0, 0.0, 0.5, 0.5, 0),
        0,
    )
    assert abs(value - math.sqrt(0.5)) < TOL