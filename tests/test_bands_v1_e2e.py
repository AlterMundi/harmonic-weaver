"""End-to-end compilation tests for the vertical-bands geometry."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from harmonic_weaver.contract_codec import contract_id_from_manifest
from harmonic_weaver.engine import INVALID, OBSERVED, WeaverEngine
from harmonic_weaver.engine.compiler import compile_scene
from rehearsal.weaver_runtime import (
    harmocap_manifest,
    runtime_status_payload,
    shaper_safety_profile,
)

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


def _ready_bands_engine() -> tuple[WeaverEngine, dict]:
    engine = WeaverEngine()
    shaper = _shaper_manifest()
    shaper_contract = contract_id_from_manifest(shaper)
    engine.install_instrument(shaper, shaper_safety_profile(shaper_contract))
    assert engine.instrument_hello("shaper", "00000000000000c1", shaper_contract)
    assert engine.instrument_sync_complete("shaper", "00000000000000c1", shaper_contract)

    harmocap = harmocap_manifest(lease_ms=60_000.0)
    harmocap_contract = engine.install_source(harmocap)
    assert engine.source_hello("harmocap", "00000000000000a1", harmocap_contract)

    scene = _bands_scene()
    engine.upsert_scene(scene, engine.stage_revision)
    engine.switch_scene(scene["scene_id"], int(scene["scene_version"]), engine.stage_revision)
    return engine, harmocap


def _invalid_harmocap_frame(manifest: dict) -> dict[str, tuple[float, str, float]]:
    return {
        channel["name"]: (0.0, INVALID, 0.0)
        for channel in manifest["channels"]
    }


def _mark_person(
    frame: dict[str, tuple[float, str, float]],
    *,
    slot: int,
    right_band_x: float,
    left_band_x: float,
    nose_x: float = 0.5,
    nose_y: float = 0.5,
) -> None:
    frame.update(
        {
            f"slot_{slot}_present": (1.0, OBSERVED, 1.0),
            f"slot_{slot}_keypoint_right_wrist_x": (right_band_x, OBSERVED, 1.0),
            f"slot_{slot}_keypoint_right_wrist_y": (0.5, OBSERVED, 1.0),
            f"slot_{slot}_keypoint_left_wrist_x": (left_band_x, OBSERVED, 1.0),
            f"slot_{slot}_keypoint_left_wrist_y": (0.5, OBSERVED, 1.0),
            f"slot_{slot}_keypoint_nose_x": (nose_x, OBSERVED, 1.0),
            f"slot_{slot}_keypoint_nose_y": (nose_y, OBSERVED, 1.0),
        }
    )


def _snapshot_routes_by_source_harmonic(engine: WeaverEngine) -> dict[tuple[int, int], dict]:
    return {
        (
            route["destination"]["bindings"]["S"],
            route["destination"]["bindings"]["N"],
        ): route
        for route in engine.snapshot(["routes"])["routes"]
    }


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


def test_bands_v1_geometry_snapshot_exposes_runtime_routes() -> None:
    engine, _harmocap = _ready_bands_engine()

    snapshot = engine.snapshot(["routes", "sources"])

    routes = snapshot["routes"]
    assert len(routes) == 128
    assert {route["destination"]["capability"] for route in routes} == {
        "harmonic_source_envelope"
    }
    assert all(route["runtime"]["active"] for route in routes)
    assert all(route["runtime"]["instrument_ready"] for route in routes)
    assert all("last_output" in route["runtime"] for route in routes)
    source_ids = {item["source_id"] for item in snapshot["sources"]}
    assert {"slot_0_band_r", "slot_0_band_l", "slot_1_band_r", "slot_1_band_l"} <= source_ids
    engine.close()


def test_bands_v1_status_snapshot_survives_route_updates() -> None:
    engine, harmocap = _ready_bands_engine()
    frame = _invalid_harmocap_frame(harmocap)
    _mark_person(frame, slot=0, right_band_x=0.08, left_band_x=0.72)

    engine.ingest_source_frame(
        "harmocap",
        "00000000000000a1",
        harmocap["contract_id"],
        0,
        frame,
        now_us=1_000,
    )

    snapshot = engine.snapshot()
    routes = snapshot["routes"]
    assert snapshot["stage"]["active_scene_id"] == "bands-v1"
    assert len(routes) == 128
    by_source = {
        (route["destination"]["bindings"]["S"], route["destination"]["bindings"]["N"]): route
        for route in routes
    }
    assert by_source[(0, 1)]["runtime"]["last_output"] == 1.0
    assert by_source[(1, 6)]["runtime"]["last_output"] == 1.0
    engine.close()


def test_bands_v1_two_person_two_hand_polyphony_and_selective_release() -> None:
    engine, harmocap = _ready_bands_engine()
    frame = _invalid_harmocap_frame(harmocap)
    _mark_person(frame, slot=0, right_band_x=0.08, left_band_x=0.72)
    _mark_person(frame, slot=1, right_band_x=0.34, left_band_x=0.92)

    engine.ingest_source_frame(
        "harmocap",
        "00000000000000a1",
        harmocap["contract_id"],
        0,
        frame,
        now_us=1_000,
    )

    first = _snapshot_routes_by_source_harmonic(engine)
    expected_on = {(0, 1), (1, 6), (2, 3), (3, 8)}
    assert {key for key, route in first.items() if route["runtime"]["last_output"] == 1.0} == expected_on
    for source in range(4):
        active_harmonics = [
            harmonic
            for (slot_source, harmonic), route in first.items()
            if slot_source == source and route["runtime"]["last_output"] == 1.0
        ]
        assert len(active_harmonics) == 1

    transition_frame = _invalid_harmocap_frame(harmocap)
    _mark_person(transition_frame, slot=0, right_band_x=0.34, left_band_x=0.72)
    _mark_person(transition_frame, slot=1, right_band_x=0.34, left_band_x=0.92)
    engine.ingest_source_frame(
        "harmocap",
        "00000000000000a1",
        harmocap["contract_id"],
        1,
        transition_frame,
        now_us=150_000,
    )

    transitioned = _snapshot_routes_by_source_harmonic(engine)
    transitioned_on = {
        key
        for key, route in transitioned.items()
        if route["runtime"]["last_output"] == 1.0
    }
    assert transitioned_on == {(0, 3), (1, 6), (2, 3), (3, 8)}
    transition_writes = {
        (record.bindings["S"], record.bindings["N"], float(record.value))
        for record in engine.transport.records
        if record.sent_at_us == 150_000
        and record.reason == "route"
        and record.capability == "harmonic_source_envelope"
    }
    assert transition_writes == {(0, 1, 0.0), (0, 3, 1.0)}

    release_frame = _invalid_harmocap_frame(harmocap)
    _mark_person(release_frame, slot=0, right_band_x=0.34, left_band_x=0.72)
    release_frame["slot_1_present"] = (0.0, OBSERVED, 1.0)
    engine.ingest_source_frame(
        "harmocap",
        "00000000000000a1",
        harmocap["contract_id"],
        2,
        release_frame,
        now_us=300_000,
    )

    second = _snapshot_routes_by_source_harmonic(engine)
    still_on = {key for key, route in second.items() if route["runtime"]["last_output"] == 1.0}
    assert still_on == {(0, 3), (1, 6)}
    assert second[(2, 3)]["runtime"]["last_output"] == 0.0
    assert second[(3, 8)]["runtime"]["last_output"] == 0.0

    release_resets = {
        (record.bindings["S"], record.bindings["N"])
        for record in engine.transport.records
        if record.reason == "route_reset"
        and record.capability == "harmonic_source_envelope"
        and float(record.value) == 0.0
    }
    assert {(2, 3), (3, 8)} <= release_resets
    assert (0, 1) not in release_resets
    assert (1, 6) not in release_resets
    engine.close()


def test_bands_v1_runtime_status_payload_uses_geometry_snapshot() -> None:
    engine, _harmocap = _ready_bands_engine()

    class FakeECG:
        _frame_count = 0

        def stream_alive(self) -> bool:
            return True

    class FakeMIDI:
        connected = False
        port_name = None
        last_error = None

        def available_ports(self) -> list[str]:
            return []

        def snapshot(self) -> dict:
            return {}

    payload = runtime_status_payload(
        engine=engine,
        transport=engine.transport,
        harmocap=SimpleNamespace(
            stream_id="synthetic",
            hello=SimpleNamespace(contract_id="contract"),
            stats=SimpleNamespace(valid_frames=1),
        ),
        harmocap_listener_alive=True,
        ecg=FakeECG(),
        midi=FakeMIDI(),
        captured_at_us=123,
    )

    assert payload["captured_at_us"] == 123
    assert payload["engine"]["stage"]["active_scene_id"] == "bands-v1"
    assert len(payload["engine"]["routes"]) == 128
    assert payload["drivers"]["harmocap"]["listener_alive"] is True
    engine.close()


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
