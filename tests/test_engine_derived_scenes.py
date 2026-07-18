from __future__ import annotations

import copy

import pytest

from harmonic_weaver.engine import HELD, OBSERVED, WeaverError

from engine_fixtures import ready_engine, route, scene


def crowd_aggregator(cadence: dict | None = None) -> dict:
    return {
        "aggregator_id": "crowd-energy",
        "aggregator_version": 1,
        "derived_source_id": "crowd",
        "output_channel": "mean_energy",
        "inputs": [
            {
                "channel": f"sensor.slot_{slot}_energy",
                "include_when": {"channel": f"sensor.slot_{slot}_focused", "op": "eq", "value": 0.0},
            }
            for slot in range(3)
        ],
        "operator": "mean",
        "cadence": cadence or {"mode": "fixed_hz", "rate_hz": 30.0},
        "validity": {
            "min_valid_count": 2,
            "min_observed_count": 2,
            "max_age_ms": 100.0,
            "include_held": True,
            "held_max_ms": 100.0,
            "confidence": "minimum",
        },
    }


CHANNELS = {
    **{f"slot_{slot}_energy": (0.0, 1.0) for slot in range(3)},
    **{f"slot_{slot}_focused": (0.0, 1.0) for slot in range(3)},
}


def test_fixed_hz_derived_crowd_aggregation_from_explicit_slots() -> None:
    engine, recorder, source, _instrument = ready_engine(channels=CHANNELS)
    mapping = route("crowd-to-bed", channel="crowd.mean_energy", voice=2)
    preset = scene(routes=[mapping], aggregators=[crowd_aggregator()])
    engine.upsert_scene(preset, engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    recorder.clear()

    frame = {
        "slot_0_energy": (0.9, OBSERVED, 0.9),
        "slot_0_focused": (1.0, OBSERVED, 1.0),
        "slot_1_energy": (0.2, OBSERVED, 0.8),
        "slot_1_focused": (0.0, OBSERVED, 1.0),
        "slot_2_energy": (0.6, OBSERVED, 0.7),
        "slot_2_focused": (0.0, OBSERVED, 1.0),
    }
    engine.ingest_source_frame("sensor", "0000000000000001", source["contract_id"], 0, frame, now_us=0)

    derived = engine.source_value("crowd.mean_energy")
    assert derived is not None
    assert derived.value == pytest.approx(0.4)
    assert derived.state == OBSERVED
    assert derived.confidence == pytest.approx(0.7)
    assert recorder.records[-1].value == pytest.approx(0.4)


def test_on_input_aggregator_coalesces_and_propagates_held() -> None:
    engine, _recorder, source, _instrument = ready_engine(channels=CHANNELS)
    aggregator = crowd_aggregator({"mode": "on_input", "max_rate_hz": 10.0})
    engine.upsert_scene(scene(aggregators=[aggregator]), engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    base = {
        "slot_0_energy": (0.1, OBSERVED, 1.0), "slot_0_focused": (0.0, OBSERVED, 1.0),
        "slot_1_energy": (0.3, OBSERVED, 1.0), "slot_1_focused": (0.0, OBSERVED, 1.0),
        "slot_2_energy": (0.7, HELD, 0.5), "slot_2_focused": (1.0, OBSERVED, 1.0),
    }
    engine.ingest_source_frame("sensor", "0000000000000001", source["contract_id"], 0, base, now_us=0)
    assert engine.source_value("crowd.mean_energy").value == pytest.approx(0.2)
    changed = dict(base)
    changed["slot_1_energy"] = (0.9, OBSERVED, 1.0)
    engine.ingest_source_frame("sensor", "0000000000000001", source["contract_id"], 1, changed, now_us=50_000)
    assert engine.source_value("crowd.mean_energy").value == pytest.approx(0.2)
    engine.tick(now_us=100_000)
    assert engine.source_value("crowd.mean_energy").value == pytest.approx(0.5)


def test_atomic_batch_and_scene_switch_generation() -> None:
    engine, _recorder, _source, _instrument = ready_engine()
    engine.upsert_scene(scene(routes=[]), engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    revision = engine.stage_revision
    generation = engine.activation_generation
    operations = [
        {"type": "route.create", "payload": {"scene_id": "main", "route": route("one", voice=0)}},
        {"type": "route.create", "payload": {"scene_id": "main", "route": route("collision", voice=0)}},
    ]
    with pytest.raises(WeaverError) as raised:
        engine.route_batch(operations, revision)
    assert raised.value.code == "destination_collision"
    assert engine.stage_revision == revision
    assert engine.activation_generation == generation
    assert engine.snapshot(["routes"])["routes"] == []

    operations[1]["payload"]["route"] = route("two", voice=1)
    ack = engine.route_batch(operations, revision)
    assert ack["activation_generation"] == generation + 1
    assert {item["route_id"] for item in engine.snapshot(["routes"])["routes"]} == {"one", "two"}

    other = scene("other", routes=[route("other-route", voice=3)], updated_at_us=1)
    engine.upsert_scene(other, engine.stage_revision)
    switch = engine.switch_scene("other", 1, engine.stage_revision)
    assert switch["activation_generation"] == generation + 2
    assert engine.active_scene_id == "other"
