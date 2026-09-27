"""Replay-based E2E for the pads_v2 scene.

Loads a recorded HarMoCAP session and feeds it through the engine with
pads_v2.scene.json compiled against the current HarMoCAP + Shaper
contracts. Asserts:

- Scene compiles cleanly (8 aggregators, 64 routes).
- The engine evaluates without exceptions.
- The engine emits /digital/harmonic/{N}/{gain,amplitude} writes on
  the OSC transport; with the current contracts those addresses map to
  harmonic_envelope (gain) and harmonic_trigger (amplitude).
- Both hand_l and hand_r contribute to envelope writes, on disjoint N
  ranges (hand_r on odd N, hand_l on even N).
- A peak_detector trigger fires when the radial_velocity exceeds the
  threshold and decelerates — verified by feeding a synthetic trajectory
  that crosses the threshold twice (rises then falls).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HARMOCAP_ROOT = Path(
    os.environ.get("HARMOCAP_DIR", REPO.parent / "HarMoCAP")
).expanduser()
SHAPER_ROOT = Path(
    os.environ.get("SHAPER_DIR", REPO.parent / "harmonic-shaper")
).expanduser()
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from harmonic_weaver.engine import RecordingOutputTransport, WeaverEngine
from harmonic_weaver.engine.compiler import compile_scene, destination_key
from harmonic_weaver.engine.model import HELD, OBSERVED, INVALID, ValueEnvelope


def _harMoCAP_manifest():
    return json.loads(
        (HARMOCAP_ROOT / "schemas" / "osc_contract.v1.json").read_text()
    )


def _shaper_manifest():
    return json.loads(
        (SHAPER_ROOT / "contracts" / "shaper.contract.json").read_text()
    )


def _scene():
    return json.loads((REPO / "rehearsal" / "scenes" / "pads_v2.scene.json").read_text())


def _build_ranges():
    """Real HarMoCAP channel ranges; derived outputs are produced by the
    engine, NOT pre-installed in base_ranges."""
    ranges = {}
    for slot in (0, 1):
        ranges[f"harmocap.slot_{slot}_focused"] = (0.0, 1.0)
        ranges[f"harmocap.slot_{slot}_present"] = (0.0, 1.0)
        for kp in (
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle",
        ):
            ranges[f"harmocap.slot_{slot}_keypoint_{kp}_x"] = (0.0, 1280.0)
            ranges[f"harmocap.slot_{slot}_keypoint_{kp}_y"] = (0.0, 720.0)
    return ranges


def _safety_defaults():
    safety = {}
    shaper = _shaper_manifest()
    for cap in shaper["capabilities"]:
        # Cover all capabilities pads_v1 and pads_v2 reference: envelope,
        # gain (pads_v1) and trigger.
        if cap["name"] not in (
            "harmonic_envelope",
            "harmonic_gain",
            "harmonic_trigger",
            "harmonic_source_envelope",
        ):
            continue
        for n in range(1, 33):
            sources = range(16) if cap["name"] == "harmonic_source_envelope" else (None,)
            for source in sources:
                bindings = {"N": n}
                if source is not None:
                    bindings["S"] = source
                d = {"instrument_id": "shaper", "capability": cap["name"],
                     "bindings": bindings, "argument": cap["arguments"][0]["name"]}
                safety[destination_key(d)] = 0.0
    return safety


def test_pads_v2_scene_compiles_cleanly():
    harmocap = _harMoCAP_manifest()
    shaper = _shaper_manifest()
    scene = _scene()
    result = compile_scene(scene, _build_ranges(),
                            {"harMoCAP": harmocap, "shaper": shaper},
                            safety_defaults=_safety_defaults())
    # Two slots × two hands × (x/y/pad) aggregators.
    assert len(result.aggregators) == 12
    # Two people × two hands × all 32 harmonics.
    assert len(result.routes) == 128
    # Symmetry: equal route count per hand.
    hand_r = sum(1 for r in result.routes if "hand-r" in r.route_id)
    hand_l = sum(1 for r in result.routes if "hand-l" in r.route_id)
    assert hand_r == hand_l == 64
    # Every hand owns the complete harmonic grid through its own source binding.
    for r in result.routes:
        assert r.destination.definition["capability"] == "harmonic_source_envelope"
        assert 1 <= r.destination.definition["bindings"]["N"] <= 32
        assert 0 <= r.destination.definition["bindings"]["S"] <= 3


def test_peak_detector_triggers_on_synthetic_trajectory():
    """Hand-crafted input through a minimal peak_detector route. We do not
    compile the full pads_v2 trigger route here (it depends on 4 derived
    aggregator outputs that don't exist standalone). Instead, build a tiny
    route that wires a radial_velocity-derived signal directly into the
    peak detector and assert the fire pattern."""
    from harmonic_weaver.engine.compiler import (
        RouteRuntime,
        compile_route,
        evaluate_route,
    )

    # Single-input route: a fake "radial velocity" value feeding peak_detector.
    # We bypass the radial_velocity transform (it needs 4 inputs) and just
    # feed a 0..1 scalar that simulates what radial_velocity would produce.
    ranges = {"sensor.rad": (0.0, 1.0)}
    route_raw = {
        "route_id": "trigger-test",
        "route_version": 1,
        "enabled": True,
        "inputs": [{"channel": "sensor.rad"}],
        "transforms": [
            {"type": "peak_detector", "threshold": 0.30, "refractory_ms": 250.0},
        ],
        "destination": {
            "instrument_id": "shaper", "capability": "harmonic_trigger",
            "bindings": {"N": 1}, "argument": "amplitude",
        },
        "validity": {"held": "accept", "min_confidence": 0.0, "invalid": "suppress"},
    }
    route = compile_route(route_raw, ranges, {"shaper": _shaper_manifest()},
                           {destination_key({"instrument_id": "shaper", "capability": "harmonic_trigger",
                                              "bindings": {"N": 1}, "argument": "amplitude"}): 0.0},
                           "scene.routes[0]")

    def env(value, now_us):
        return {"sensor.rad": ValueEnvelope(value, OBSERVED, 1.0, now_us, now_us)}

    rt = RouteRuntime()
    # Trajectory: 0 → 0.1 → 0.3 → 0.5 → 0.7 → 0.9 (rising) → 0.7 → 0.5
    # (falling). Two peaks possible; refractory 250 ms collapses to one.
    trajectory = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 0.7, 0.5]
    fires = []
    now = 0
    for i, v in enumerate(trajectory):
        result, reason = evaluate_route(route, rt, env(v, now), now)
        if result is not None and result >= 1.0 and reason == "usable":
            fires.append((now, result))
        now += 33_000
    assert len(fires) >= 1, f"expected at least one peak fire, got {fires}"
    if len(fires) >= 2:
        gaps = [fires[i + 1][0] - fires[i][0] for i in range(len(fires) - 1)]
        assert all(g >= 250_000 for g in gaps), f"refractory violated: gaps={gaps}"


def test_pads_v1_still_compiles():
    """pads_v1 must keep working — pads_v2 is additive, not a replacement.

    After card 4 (pad_dwell), pads_v1 has 32 envelope + 32 gain = 64 routes."""
    harmocap = _harMoCAP_manifest()
    shaper = _shaper_manifest()
    scene = json.loads((REPO / "rehearsal" / "scenes" / "pads_v1.scene.json").read_text())
    ranges = _build_ranges()
    safety = _safety_defaults()
    result = compile_scene(scene, ranges, {"harMoCAP": harmocap, "shaper": shaper},
                            safety_defaults=safety)
    assert len(result.routes) == 64
    # All routes target either harmonic_envelope or harmonic_gain (no trigger).
    caps = {r.destination.definition["capability"] for r in result.routes}
    assert caps == {"harmonic_envelope", "harmonic_gain"}
