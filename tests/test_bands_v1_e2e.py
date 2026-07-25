"""End-to-end compilation tests for the vertical-bands geometry."""

from __future__ import annotations

import json
from pathlib import Path

from harmonic_weaver.engine.compiler import compile_scene

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT
SHAPER_DIR = ROOT.parent / "harmonic-shaper"


def _shaper_manifest() -> dict:
    return json.loads(
        (SHAPER_DIR / "contracts" / "shaper.contract.json").read_text()
    )


def _bands_scene() -> dict:
    return json.loads(
        (REPO / "rehearsal" / "scenes" / "bands-v1.scene.json").read_text()
    )


def _harmocap_manifest() -> dict:
    return json.loads(
        (REPO / "contracts" / "source_frame.template.json").read_text()
    )


def _build_ranges():
    ranges = {}
    for slot in range(8):
        ranges[f"harmocap.slot_{slot}_present"] = (0.0, 1.0)
        for kp in ("nose", "left_wrist", "right_wrist"):
            for axis in ("x", "y"):
                ranges[f"harmocap.slot_{slot}_keypoint_{kp}_{axis}"] = (0.0, 1.8)
    return ranges


def _safety_defaults():
    from harmonic_weaver.engine.compiler import destination_key

    safety = {}
    shaper = _shaper_manifest()
    for cap in shaper["capabilities"]:
        name = cap["name"]
        if name not in (
            "harmonic_envelope",
            "harmonic_gain",
            "harmonic_trigger",
            "harmonic_source_envelope",
            "master_gain",
        ):
            continue
        arg = cap["arguments"][0]["name"]
        if name == "harmonic_source_envelope":
            for n in range(1, 33):
                for s in range(16):
                    d = {
                        "instrument_id": "shaper",
                        "capability": name,
                        "bindings": {"N": n, "S": s},
                        "argument": arg,
                    }
                    safety[destination_key(d)] = 0.0
        elif name == "master_gain":
            d = {
                "instrument_id": "shaper",
                "capability": name,
                "bindings": {},
                "argument": arg,
            }
            safety[destination_key(d)] = 0.0
        else:
            for n in range(1, 33):
                d = {
                    "instrument_id": "shaper",
                    "capability": name,
                    "bindings": {"N": n},
                    "argument": arg,
                }
                safety[destination_key(d)] = 0.0
    return safety


def test_bands_v1_scene_compiles():
    scene = _bands_scene()
    result = compile_scene(
        scene,
        _build_ranges(),
        {"harmocap": _harmocap_manifest(), "shaper": _shaper_manifest()},
        _safety_defaults(),
    )
    # 8 slots × 2 hands × (pos_x + pos_y + band) + 8 × head_x + 8 × head_y = 48+16=64 agg
    # 8 slots × 2 hands × 8 subdivisions = 128 match_value routes
    # + (potentially head-y effect routes if effects included)
    assert len(result.aggregators) >= 48
    assert len(result.routes) >= 128
    band_routes = [
        r for r in result.routes
        if r.destination.definition["capability"] == "harmonic_source_envelope"
    ]
    assert len(band_routes) == 128


def test_bands_v1_rejects_too_few_subdivisions():
    from harmonic_weaver.engine.errors import WeaverError
    import pytest

    scene = _bands_scene()
    scene["geometry"]["subdivisions"] = 1
    with pytest.raises((WeaverError, Exception)):
        compile_scene(
            scene,
            _build_ranges(),
            {"harmocap": _harmocap_manifest(), "shaper": _shaper_manifest()},
            _safety_defaults(),
        )
