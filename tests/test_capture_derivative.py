"""Capture derivatives are invariant to receipt jitter; incompatible frames never mix."""

from dataclasses import replace
import pytest
from harmonic_weaver.engine.compiler import RouteRuntime, evaluate_route
from harmonic_weaver.engine.model import ValueEnvelope, OBSERVED, HELD
from test_transforms_derivative import _compile, _deriv


def value(frame, time, number, *, stream="stream", received=9000000000):
    return ValueEnvelope(
        number,
        OBSERVED,
        1.0,
        received,
        time,
        "producer_monotonic_us_unmapped",
        "engine_configured_us",
        ("sensor", stream, "contract", 1, "calibration", frame),
    )


def capture_route(**kwargs):
    return _compile(_deriv(clock="source_capture", max_gap_ms=500.0, **kwargs))


def test_capture_slope_ignores_receipt_jitter_and_does_not_clamp_valid_capture_delta():
    route = capture_route(max_dt_ms=1.0)
    for receipt_times in [(0, 10), (9000000000, 19000000000)]:
        runtime = RouteRuntime()
        assert (
            evaluate_route(
                route, runtime, {"sensor.pos": value(1, 1000000, 1.0)}, receipt_times[0]
            )[0]
            == 0.0
        )
        result = evaluate_route(
            route, runtime, {"sensor.pos": value(2, 1200000, 2.0)}, receipt_times[1]
        )
        assert result == (pytest.approx(5.0), "usable")
        assert runtime.derivative_at_us[0] == 1200000


def test_repeat_backward_frame_and_clock_do_not_replace_baseline():
    route = capture_route()
    runtime = RouteRuntime()
    first = value(1, 1000000, 1.0)
    evaluate_route(route, runtime, {"sensor.pos": first}, 0)
    for sample in [first, value(0, 1050000, 99.0), value(2, 900000, 99.0)]:
        assert evaluate_route(route, runtime, {"sensor.pos": sample}, 100) == (
            None,
            "suppress",
        )
        assert runtime.sample_reason == "capture_not_new"
    result = evaluate_route(route, runtime, {"sensor.pos": value(3, 1200000, 2.0)}, 200)
    assert result[0] == pytest.approx(5.0)


def test_gap_epoch_and_held_resume_warm_without_velocity_spike():
    route = capture_route()
    runtime = RouteRuntime()
    evaluate_route(route, runtime, {"sensor.pos": value(1, 1000000, 1.0)}, 0)
    assert (
        evaluate_route(route, runtime, {"sensor.pos": value(2, 2000000, 100.0)}, 1)[0]
        == 0.0
    )
    assert runtime.sample_reason == "capture_gap_warming"
    assert (
        evaluate_route(
            route, runtime, {"sensor.pos": value(1, 50000, 500.0, stream="another")}, 2
        )[0]
        == 0.0
    )
    assert runtime.sample_reason == "capture_epoch_warming"
    held = replace(value(2, 100000, 500.0, stream="another"), state=HELD)
    assert evaluate_route(route, runtime, {"sensor.pos": held}, 3) == (None, "suppress")
    assert (
        evaluate_route(
            route, runtime, {"sensor.pos": value(3, 150000, 600.0, stream="another")}, 4
        )[0]
        == 0.0
    )


def test_untagged_legacy_capture_never_falls_back_to_engine_clock():
    route = capture_route()
    runtime = RouteRuntime()
    legacy = ValueEnvelope(1.0, OBSERVED, 1.0, 999999, 50000)
    assert evaluate_route(route, runtime, {"sensor.pos": legacy}, 100) == (
        None,
        "suppress",
    )
    assert runtime.sample_reason == "capture_metadata_required"
    assert not runtime.derivative_values


def test_multiple_inputs_require_identical_producer_epoch_frame_and_time():
    route = replace(capture_route(), inputs=("sensor.pos", "sensor.other"))
    route.definition["transforms"].insert(
        0, {"type": "combine", "operator": "difference"}
    )
    runtime = RouteRuntime()
    left = value(1, 1000000, 2.0)
    for right in [
        value(2, 1000000, 1.0),
        value(1, 999999, 1.0),
        value(1, 1000000, 1.0, stream="other"),
        replace(
            value(1, 1000000, 1.0),
            capture_identity=(
                "other-source",
                "stream",
                "contract",
                1,
                "calibration",
                1,
            ),
        ),
    ]:
        assert evaluate_route(
            route, runtime, {"sensor.pos": left, "sensor.other": right}, 0
        ) == (None, "suppress")
        assert runtime.sample_reason == "capture_inputs_not_aligned"
    assert (
        evaluate_route(
            route,
            runtime,
            {"sensor.pos": left, "sensor.other": value(1, 1000000, 1.0)},
            1,
        )[0]
        == 0.0
    )
    result = evaluate_route(
        route,
        runtime,
        {"sensor.pos": value(2, 1200000, 4.0), "sensor.other": value(2, 1200000, 2.0)},
        2,
    )
    assert result[0] == pytest.approx(5.0)


@pytest.mark.parametrize(
    "params", [{"clock": "wall"}, {"clock": "source_capture", "max_gap_ms": 0.0}]
)
def test_reject_invalid_clock_configuration(params):
    with pytest.raises(Exception):
        _compile(_deriv(**params))


def test_alignment_guard_obeys_hold_reset_without_renewing_hold_deadline():
    route = capture_route()
    route.definition["validity"] = {
        "held": "reject",
        "min_confidence": 0.0,
        "invalid": "hold_then_reset",
        "hold_ms": 100.0,
    }
    runtime = RouteRuntime()
    evaluate_route(route, runtime, {"sensor.pos": value(1, 1000000, 1.0)}, 0)
    absent = ValueEnvelope(2.0, OBSERVED, 1.0, 50000, 1100000)
    assert evaluate_route(route, runtime, {"sensor.pos": absent}, 50000) == (
        0.0,
        "usable",
    )
    assert runtime.last_usable_at_us == 0
    assert evaluate_route(route, runtime, {"sensor.pos": absent}, 100001) == (
        None,
        "reset",
    )
    assert evaluate_route(route, runtime, {"sensor.pos": absent}, 200000) == (
        None,
        "suppress",
    )


def test_engine_aligned_pair_waits_without_resampling_and_resets_if_peer_frame_never_arrives(
    monkeypatch,
):
    from engine_fixtures import route, scene
    from test_engine_driver_observations import setup, event

    engine, recorder, _, now = setup(monkeypatch)
    pair = route(
        "pair",
        channel="sensor.slot_0_pos",
        transforms=[
            {"type": "combine", "operator": "difference"},
            {
                "type": "derivative",
                "window_ms": 40.0,
                "max_abs": 10.0,
                "max_dt_ms": 1000.0,
                "clock": "source_capture",
                "max_gap_ms": 500.0,
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
    pair["inputs"].append({"channel": "sensor.slot_1_pos"})
    engine.upsert_scene(scene(routes=[pair], version=2), engine.stage_revision, expected_scene_version=1)
    engine.switch_scene("main", 2, engine.stage_revision)
    engine.ingest_driver_observation(event(value=0.2))
    engine.ingest_driver_observation(event(slot=1, value=0.1))
    assert engine._route_runtime["pair"].last_usable_output == pytest.approx(0.5)
    now[0] += 50000
    engine.ingest_driver_observation(event(frame=2, value=0.4))
    assert engine._route_runtime["pair"].sample_reason == "capture_inputs_not_aligned"
    assert engine._route_runtime["pair"].derivative_at_us[1] == 50000
    now[0] += 1000
    engine.ingest_driver_observation(event(slot=1, frame=2, value=0.1))
    assert engine._route_runtime["pair"].last_usable_output == pytest.approx(0.7)
    now[0] += 1000
    engine.ingest_driver_observation(event(frame=3, value=0.5))
    now[0] += 150000
    engine.tick()
    assert any(r.reason == "route_reset" for r in recorder.records)
    assert engine._route_runtime["pair"].sample_reason == "capture_inputs_not_aligned"
