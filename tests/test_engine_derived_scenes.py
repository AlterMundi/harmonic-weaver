from __future__ import annotations

import copy

import pytest

from harmonic_weaver.engine import HELD, INVALID, OBSERVED, WeaverError

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


BIN_2D_CHANNELS = {"x": (0.0, 1.0), "y": (0.0, 1.0)}


def bin_2d_aggregator(
    *,
    cols: int = 2,
    rows: int = 2,
    serpentine: bool = True,
    x_min: float = 0.0,
    x_max: float = 1.0,
    y_min: float = 0.0,
    y_max: float = 1.0,
    extra: dict | None = None,
) -> dict:
    aggregator = {
        "aggregator_id": "spatial-bin",
        "aggregator_version": 1,
        "derived_source_id": "grid",
        "output_channel": "bin",
        "inputs": [
            {"channel": "sensor.x"},
            {"channel": "sensor.y"},
        ],
        "operator": "bin_2d",
        "cols": cols,
        "rows": rows,
        "serpentine": serpentine,
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "cadence": {"mode": "on_input", "max_rate_hz": 60.0},
        "validity": {
            "min_valid_count": 2,
            "min_observed_count": 2,
            "max_age_ms": 1000.0,
            "include_held": True,
            "held_max_ms": 0.0,
            "confidence": "minimum",
        },
    }
    if extra:
        aggregator.update(extra)
    return aggregator


def _activate_bin_2d(engine, source, aggregator: dict) -> None:
    engine.upsert_scene(scene(aggregators=[aggregator]), engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)


def _ingest_xy(engine, source, x: float, y: float, *, seq: int = 0, now_us: int = 0, state=OBSERVED) -> None:
    frame = {
        "x": (x, state, 0.9),
        "y": (y, state, 0.8),
    }
    engine.ingest_source_frame(
        "sensor",
        "0000000000000001",
        source["contract_id"],
        seq,
        frame,
        now_us=now_us,
    )


def test_bin_2d_non_serpentine_2x2_column_major() -> None:
    engine, _recorder, source, _instrument = ready_engine(channels=BIN_2D_CHANNELS)
    _activate_bin_2d(engine, source, bin_2d_aggregator(serpentine=False))

    # index = col * rows + row (column-major)
    cases = [
        (0.25, 0.25, 0.0),
        (0.25, 0.75, 1.0),
        (0.75, 0.25, 2.0),
        (0.75, 0.75, 3.0),
    ]
    for seq, (x, y, expected) in enumerate(cases):
        _ingest_xy(engine, source, x, y, seq=seq, now_us=seq * 20_000)
        derived = engine.source_value("grid.bin")
        assert derived is not None
        assert derived.state == OBSERVED
        assert derived.value == pytest.approx(expected)
        assert isinstance(derived.value, float)
        assert derived.confidence == pytest.approx(0.8)


def test_bin_2d_serpentine_2x2_even_col_up_odd_col_down() -> None:
    engine, _recorder, source, _instrument = ready_engine(channels=BIN_2D_CHANNELS)
    _activate_bin_2d(engine, source, bin_2d_aggregator(serpentine=True))

    # even col: bottom->top (row as-is); odd col: top->bottom (row flipped)
    cases = [
        (0.25, 0.25, 0.0),  # col0 row0 -> 0
        (0.25, 0.75, 1.0),  # col0 row1 -> 1
        (0.75, 0.25, 3.0),  # col1 row0 -> 2 + (1-0) = 3
        (0.75, 0.75, 2.0),  # col1 row1 -> 2 + (1-1) = 2
    ]
    for seq, (x, y, expected) in enumerate(cases):
        _ingest_xy(engine, source, x, y, seq=seq, now_us=seq * 20_000)
        derived = engine.source_value("grid.bin")
        assert derived is not None
        assert derived.state == OBSERVED
        assert derived.value == pytest.approx(expected)


def test_bin_2d_boundary_clamps_to_last_bin() -> None:
    engine, _recorder, source, _instrument = ready_engine(channels=BIN_2D_CHANNELS)
    _activate_bin_2d(engine, source, bin_2d_aggregator(serpentine=False))

    _ingest_xy(engine, source, 1.0, 0.25, seq=0, now_us=0)
    derived = engine.source_value("grid.bin")
    assert derived is not None
    assert derived.value == pytest.approx(2.0)  # col clamped to 1, row 0

    _ingest_xy(engine, source, 0.25, 1.0, seq=1, now_us=20_000)
    derived = engine.source_value("grid.bin")
    assert derived is not None
    assert derived.value == pytest.approx(1.0)  # col 0, row clamped to 1

    _ingest_xy(engine, source, 1.0, 1.0, seq=2, now_us=40_000)
    derived = engine.source_value("grid.bin")
    assert derived is not None
    assert derived.value == pytest.approx(3.0)


def test_bin_2d_invalid_input_produces_invalid_output() -> None:
    engine, _recorder, source, _instrument = ready_engine(channels=BIN_2D_CHANNELS)
    _activate_bin_2d(engine, source, bin_2d_aggregator(serpentine=False))

    frame = {
        "x": (0.25, OBSERVED, 1.0),
        "y": (0.0, INVALID, 0.0),
    }
    engine.ingest_source_frame(
        "sensor",
        "0000000000000001",
        source["contract_id"],
        0,
        frame,
        now_us=0,
    )
    derived = engine.source_value("grid.bin")
    assert derived is not None
    assert derived.state == INVALID


def test_bin_2d_validation_rejects_bad_parameters() -> None:
    engine, _recorder, source, _instrument = ready_engine(channels=BIN_2D_CHANNELS)

    with pytest.raises(WeaverError) as raised:
        engine.upsert_scene(
            scene(aggregators=[bin_2d_aggregator(x_min=1.0, x_max=0.0)]),
            engine.stage_revision,
        )
    assert raised.value.code == "validation_failed"
    assert "x_min" in raised.value.message

    with pytest.raises(WeaverError) as raised:
        engine.upsert_scene(
            scene(aggregators=[bin_2d_aggregator(cols=0)]),
            engine.stage_revision,
        )
    assert raised.value.code == "validation_failed"
    assert "cols" in raised.value.message

    with pytest.raises(WeaverError) as raised:
        engine.upsert_scene(
            scene(aggregators=[bin_2d_aggregator(extra={"weights": [0.5, 0.5]})]),
            engine.stage_revision,
        )
    assert raised.value.code == "validation_failed"
    assert "weights" in raised.value.message

    bad_arity = bin_2d_aggregator()
    bad_arity["inputs"] = [{"channel": "sensor.x"}]
    with pytest.raises(WeaverError) as raised:
        engine.upsert_scene(scene(aggregators=[bad_arity]), engine.stage_revision)
    assert raised.value.code == "validation_failed"
    assert "two inputs" in raised.value.message
