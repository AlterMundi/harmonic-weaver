"""Derived signals retain capture provenance only when dependencies share a frame."""

from dataclasses import replace
import pytest
from harmonic_weaver.engine.compiler import (
    AggregatorRuntime,
    compile_aggregators,
    evaluate_aggregator,
)
from harmonic_weaver.engine.model import HELD, OBSERVED, ValueEnvelope
from test_capture_derivative import value, capture_route
from harmonic_weaver.engine.compiler import RouteRuntime, evaluate_route


def aggregator(*, predicate=False, minimum=2):
    inputs = [{"channel": "sensor.x"}, {"channel": "sensor.y"}]
    if predicate:
        inputs[1]["include_when"] = {
            "channel": "sensor.enabled",
            "op": "eq",
            "value": 1.0,
        }
    raw = {
        "aggregator_id": "pair",
        "aggregator_version": 1,
        "derived_source_id": "pair",
        "output_channel": "mean",
        "inputs": inputs,
        "operator": "mean",
        "cadence": {"mode": "fixed_hz", "rate_hz": 30.0},
        "validity": {
            "min_valid_count": minimum,
            "min_observed_count": minimum,
            "max_age_ms": 1000.0,
            "include_held": True,
            "held_max_ms": 100.0,
            "confidence": "minimum",
        },
    }
    compiled, _ = compile_aggregators(
        [raw],
        {"sensor.x": (0.0, 1.0), "sensor.y": (0.0, 1.0), "sensor.enabled": (0.0, 1.0)},
    )
    return compiled[0]


def test_aligned_mean_retains_capture_through_nested_aggregation_and_derivative():
    first = aggregator()
    runtime = AggregatorRuntime()
    route = capture_route()
    route_runtime = RouteRuntime()
    for frame, x, y, expected in [(1, 0.2, 0.4, 0.0), (2, 0.4, 0.6, 4.0)]:
        envs = {
            "sensor.x": value(frame, frame * 50000, x),
            "sensor.y": value(frame, frame * 50000, y),
        }
        result = evaluate_aggregator(first, runtime, envs, 9000000000 + frame * 1000)
        assert result.value == pytest.approx((x + y) / 2)
        assert result.captured_at_us == frame * 50000
        assert result.capture_identity == envs["sensor.x"].capture_identity
        nested = evaluate_aggregator(
            first,
            AggregatorRuntime(),
            {"sensor.x": result, "sensor.y": result},
            9000000000 + frame * 2000,
        )
        assert nested.capture_identity == result.capture_identity
        assert evaluate_route(
            route, route_runtime, {"sensor.pos": nested}, frame * 1000
        )[0] == pytest.approx(expected)
        # Fixed-hz reevaluation is not a new capture and cannot modify the derivative.
        repeated = evaluate_aggregator(first, runtime, envs, 9000000000 + frame * 3000)
        assert evaluate_route(
            route, route_runtime, {"sensor.pos": repeated}, frame * 3000
        ) == (None, "suppress")


@pytest.mark.parametrize(
    "change", [{"frame": 2}, {"stream": "other"}, {"held": True}, {"legacy": True}]
)
def test_mixed_dependencies_keep_numeric_behavior_without_inventing_capture(change):
    x = value(1, 50000, 0.2)
    y = value(
        change.get("frame", 1),
        change.get("frame", 1) * 50000,
        0.4,
        stream=change.get("stream", "stream"),
    )
    if change.get("held"):
        y = replace(y, state=HELD)
    if change.get("legacy"):
        y = ValueEnvelope(0.4, OBSERVED, 1.0, 9000000000, 50000)
    result = evaluate_aggregator(
        aggregator(minimum=1),
        AggregatorRuntime(),
        {"sensor.x": x, "sensor.y": y},
        9000000000,
    )
    assert result.value == pytest.approx(0.3)
    assert result.capture_identity is None
    assert result.captured_at_us is None


def test_predicate_timing_and_subset_changes_cannot_claim_shared_capture():
    agg = aggregator(predicate=True, minimum=1)
    envs = {
        "sensor.x": value(1, 50000, 0.2),
        "sensor.y": value(1, 50000, 0.4),
        "sensor.enabled": value(1, 50000, 1.0),
    }
    assert (
        evaluate_aggregator(agg, AggregatorRuntime(), envs, 9000000000).capture_identity
        is not None
    )
    envs["sensor.enabled"] = value(2, 100000, 1.0)
    assert (
        evaluate_aggregator(agg, AggregatorRuntime(), envs, 9000000000).capture_identity
        is None
    )
    envs["sensor.enabled"] = value(1, 50000, 0.0)
    result = evaluate_aggregator(agg, AggregatorRuntime(), envs, 9000000000)
    assert result.value == pytest.approx(0.2)
    assert result.capture_identity is None


def test_engine_partial_person_events_align_derived_capture_before_deriving(
    monkeypatch,
):
    from test_engine_driver_observations import setup, event
    from engine_fixtures import route, scene

    engine, recorder, _, now = setup(monkeypatch)
    raw = dict(aggregator().definition)
    raw["inputs"] = [{"channel": "sensor.slot_0_pos"}, {"channel": "sensor.slot_1_pos"}]
    raw["cadence"] = {"mode": "fixed_hz", "rate_hz": 1000.0}
    mapping = route(
        "pair-speed",
        channel="pair.mean",
        transforms=[
            {
                "type": "derivative",
                "window_ms": 40.0,
                "max_abs": 10.0,
                "max_dt_ms": 1000.0,
                "clock": "source_capture",
            },
            {
                "type": "scale_range",
                "in": [-10.0, 10.0],
                "out": [0.0, 1.0],
                "clamp": True,
            },
        ],
        validity={
            "held": "accept",
            "min_confidence": 0.0,
            "invalid": "hold_then_reset",
            "hold_ms": 100.0,
        },
    )
    engine.upsert_scene(
        scene(routes=[mapping], aggregators=[raw], version=2),
        engine.stage_revision,
        expected_scene_version=1,
    )
    engine.switch_scene("main", 2, engine.stage_revision)
    engine.ingest_driver_observation(event(slot=0, frame=1, value=0.2))
    now[0] += 2000
    engine.ingest_driver_observation(event(slot=1, frame=1, value=0.4))
    runtime = engine._route_runtime["pair-speed"]
    assert runtime.derivative_at_us[0] == 50000
    now[0] += 2000
    engine.ingest_driver_observation(event(slot=0, frame=2, value=0.4))
    assert engine.source_value("pair.mean").capture_identity is None
    assert runtime.derivative_at_us[0] == 50000
    now[0] += 2000
    engine.ingest_driver_observation(event(slot=1, frame=2, value=0.6))
    assert runtime.derivative_at_us[0] == 100000
    assert runtime.last_usable_output == pytest.approx(0.7)
    now[0] += 2000
    engine.tick()
    assert runtime.derivative_at_us[0] == 100000
    assert runtime.sample_reason == "capture_not_new"
    assert runtime.last_usable_output == pytest.approx(0.7)


def test_bin_2d_propagates_aligned_capture_but_not_mismatched_timestamp():
    from test_engine_derived_scenes import bin_2d_aggregator

    raw = bin_2d_aggregator()
    compiled, _ = compile_aggregators(
        [raw], {"sensor.x": (0.0, 1.0), "sensor.y": (0.0, 1.0)}
    )
    envs = {"sensor.x": value(1, 50000, 0.2), "sensor.y": value(1, 50000, 0.4)}
    result = evaluate_aggregator(compiled[0], AggregatorRuntime(), envs, 9000000000)
    assert result.capture_identity == envs["sensor.x"].capture_identity
    envs["sensor.y"] = value(1, 50001, 0.4)
    result = evaluate_aggregator(compiled[0], AggregatorRuntime(), envs, 9000000000)
    assert result.value == 0.0
    assert result.capture_identity is None
