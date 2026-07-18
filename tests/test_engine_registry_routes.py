from __future__ import annotations

import copy

import pytest

from harmonic_weaver.engine import HELD, INVALID, OBSERVED, WeaverEngine, WeaverError

from engine_fixtures import ready_engine, route, scene, source_manifest


def test_source_contract_mismatch_and_stream_restart_gate() -> None:
    engine = WeaverEngine()
    manifest = source_manifest()
    contract_id = engine.install_source(manifest)

    assert engine.source_hello("sensor", "0000000000000001", "0" * 32) is False
    assert engine.ingest_source_frame(
        "sensor", "0000000000000001", contract_id, 0,
        {"modulation": (0.5, OBSERVED, 1.0)}, now_us=0,
    ) is False

    assert engine.source_hello("sensor", "0000000000000001", contract_id, now_us=1)
    assert engine.ingest_source_frame(
        "sensor", "0000000000000001", contract_id, 8,
        {"modulation": (0.5, OBSERVED, 1.0)}, now_us=2,
    )
    assert not engine.ingest_source_frame(
        "sensor", "0000000000000001", contract_id, 8,
        {"modulation": (0.6, OBSERVED, 1.0)}, now_us=3,
    )

    assert engine.source_hello("sensor", "0000000000000002", contract_id, now_us=4)
    assert engine.source_value("sensor.modulation").state == INVALID
    assert not engine.ingest_source_frame(
        "sensor", "0000000000000001", contract_id, 9,
        {"modulation": (0.6, OBSERVED, 1.0)}, now_us=5,
    )
    assert engine.ingest_source_frame(
        "sensor", "0000000000000002", contract_id, 0,
        {"modulation": (0.7, OBSERVED, 1.0)}, now_us=6,
    )


def test_route_transform_chain_held_invalid_policy_and_native_bounds() -> None:
    engine, recorder, source, _instrument = ready_engine()
    mapping = route(
        transforms=[
            {"type": "scale_range", "in": [0.0, 1.0], "out": [0.0, 1.0], "clamp": True},
            {"type": "curve", "kind": "power", "gamma": 2.0},
            {"type": "smoothing", "kind": "one_pole", "time_ms": 0.0},
        ],
        validity={"held": "reject", "min_confidence": 0.25, "invalid": "hold_then_reset", "hold_ms": 100.0},
    )
    preset = scene(routes=[mapping])
    engine.upsert_scene(preset, engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    recorder.clear()

    engine.ingest_source_frame(
        "sensor", "0000000000000001", source["contract_id"], 0,
        {"modulation": (0.5, OBSERVED, 1.0)}, now_us=0,
    )
    assert recorder.records[-1].value == pytest.approx(0.25)

    engine.ingest_source_frame(
        "sensor", "0000000000000001", source["contract_id"], 1,
        {"modulation": (0.8, HELD, 0.8)}, now_us=50_000,
    )
    assert recorder.records[-1].value == pytest.approx(0.25)

    engine.ingest_source_frame(
        "sensor", "0000000000000001", source["contract_id"], 2,
        {"modulation": (0.0, INVALID, 0.0)}, now_us=150_001,
    )
    assert recorder.records[-1].reason == "route_reset"
    assert recorder.records[-1].value == 0.0

    bad = route(
        "bad-bounds",
        transforms=[{"type": "scale_range", "in": [0, 1], "out": [0, 2], "clamp": True}],
        voice=1,
    )
    with pytest.raises(WeaverError, match="exceeds destination range"):
        engine.upsert_scene(scene("bad", routes=[bad]), engine.stage_revision)


def test_destination_collision_rejected_without_mutation() -> None:
    engine, _recorder, _source, _instrument = ready_engine()
    first = route("first", voice=0)
    second = route("second", voice=0)
    revision = engine.stage_revision
    with pytest.raises(WeaverError) as raised:
        engine.upsert_scene(scene(routes=[first, second]), revision)
    assert raised.value.code == "destination_collision"
    assert engine.stage_revision == revision


def test_multi_input_combine_and_rising_edge_gate() -> None:
    channels = {"left": (0.0, 1.0), "right": (0.0, 1.0)}
    engine, recorder, source, _instrument = ready_engine(channels=channels)
    mapping = route("combined-edge", channel="sensor.left", voice=1)
    mapping["inputs"] = [
        {"channel": "sensor.left"},
        {"channel": "sensor.right"},
    ]
    mapping["transforms"] = [
        {"type": "combine", "operator": "weighted_sum", "weights": [0.5, 0.5]},
        {
            "type": "gate",
            "threshold": 0.5,
            "hysteresis": 0.0,
            "mode": "rising_edge",
            "closed": "suppress",
        },
    ]
    engine.upsert_scene(scene(routes=[mapping]), engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    recorder.clear()

    engine.ingest_source_frame(
        "sensor", "0000000000000001", source["contract_id"], 0,
        {"left": (0.2, OBSERVED, 1.0), "right": (0.2, OBSERVED, 1.0)}, now_us=0,
    )
    assert recorder.records == []
    engine.ingest_source_frame(
        "sensor", "0000000000000001", source["contract_id"], 1,
        {"left": (0.8, OBSERVED, 1.0), "right": (0.4, OBSERVED, 1.0)}, now_us=1,
    )
    assert recorder.records[-1].value == 1.0
    count = len(recorder.records)
    engine.ingest_source_frame(
        "sensor", "0000000000000001", source["contract_id"], 2,
        {"left": (0.8, HELD, 0.9), "right": (0.4, OBSERVED, 1.0)}, now_us=2,
    )
    assert len(recorder.records) == count


def test_held_confidence_cannot_increase_within_one_hold() -> None:
    engine = WeaverEngine()
    manifest = source_manifest()
    engine.install_source(manifest)
    engine.source_hello("sensor", "0000000000000001", manifest["contract_id"], now_us=0)
    engine.ingest_source_frame(
        "sensor", "0000000000000001", manifest["contract_id"], 0,
        {"modulation": (0.5, HELD, 0.4)}, now_us=0,
    )
    with pytest.raises(WeaverError, match="decay monotonically"):
        engine.ingest_source_frame(
            "sensor", "0000000000000001", manifest["contract_id"], 1,
            {"modulation": (0.5, HELD, 0.5)}, now_us=1,
        )
