"""Per-slot ingestion, engine scheduling and raw producer provenance stay separate."""

from dataclasses import replace
import json
import pytest
from harmonic_weaver.drivers.observations import ObservationEvent
from harmonic_weaver.engine import WeaverError
from harmonic_weaver.engine.reporting import ReportWriter
from engine_fixtures import ready_engine, route, scene


def event(slot=0, frame=1, *, state=0, value=0.2, kind="slot_update"):
    return ObservationEvent(
        source_id="sensor",
        stream_id="producer-stream",
        slot=slot,
        event_kind=kind,
        reason="person_bundle" if kind == "slot_update" else "lease_expired",
        contract_id="producer-contract",
        calibration_generation=1,
        calibration_hash="calibration",
        captured_frame_id=frame,
        bundle_seq=frame * 2 + slot,
        captured_at_us=frame * 50000,
        processed_at_us=frame * 50000 + 100,
        queued_for_send_at_us=frame * 50000 + 200,
        received_at_us=1000000 + frame * 1000 + slot * 100,
        channel_values={
            f"slot_{slot}_pos": (
                0.0 if state == 2 else value,
                state,
                0.0 if state == 2 else 1.0,
            )
        },
    )


def setup(monkeypatch, *, derivative=False):
    engine, recorder, source, _ = ready_engine(
        channels={"slot_0_pos": (0.0, 1.0), "slot_1_pos": (0.0, 1.0)}
    )
    now = [9000000000]
    monkeypatch.setattr(engine, "_clock_us", lambda: now[0])
    transforms = (
        [
            {
                "type": "derivative",
                "window_ms": 40.0,
                "max_abs": 10.0,
                "max_dt_ms": 1000.0,
            },
            {
                "type": "scale_range",
                "in": [-10.0, 10.0],
                "out": [0.0, 1.0],
                "clamp": True,
            },
        ]
        if derivative
        else []
    )
    routes = [
        route(
            f"person-{s}",
            channel=f"sensor.slot_{s}_pos",
            voice=s,
            transforms=transforms,
            validity={
                "held": "accept",
                "min_confidence": 0.0,
                "invalid": "hold_then_reset",
                "hold_ms": 100.0,
            },
        )
        for s in (0, 1)
    ]
    engine.upsert_scene(scene(routes=routes), engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    recorder.clear()
    return engine, recorder, source, now


def test_other_person_and_engine_ticks_do_not_resample_first_person(monkeypatch):
    engine, recorder, source, now = setup(monkeypatch, derivative=True)
    assert engine.ingest_driver_observation(event())
    first = engine.source_value("sensor.slot_0_pos")
    first_history = dict(engine._route_runtime["person-0"].derivative_at_us)
    now[0] += 10000
    assert engine.ingest_driver_observation(event(slot=1))
    assert engine.source_value("sensor.slot_0_pos") == first
    assert engine._route_runtime["person-0"].derivative_at_us == first_history
    now[0] += 10000
    engine.tick()
    assert engine._route_runtime["person-0"].derivative_at_us == first_history
    assert first.received_at_us == 9000000000 and first.captured_at_us == 50000
    snapshot = engine._channel_snapshot(first)
    assert snapshot["capture_clock"] == "producer_monotonic_us_unmapped"
    assert snapshot["receipt_clock"] == "engine_configured_us"
    accepted = engine.metrics["frames_accepted"]
    assert not engine.ingest_driver_observation(event())
    assert engine.metrics["frames_accepted"] == accepted
    # Complete Source Frame v1 is still strict, not silently made partial.
    with pytest.raises(WeaverError, match="every declared channel"):
        engine.ingest_source_frame(
            "sensor",
            "0000000000000001",
            source["contract_id"],
            20,
            {"slot_0_pos": (0.2, 0, 1.0)},
        )


def test_held_invalid_and_recovery_do_not_continue_derivative_history(monkeypatch):
    engine, recorder, source, now = setup(monkeypatch, derivative=True)
    engine.ingest_driver_observation(event())
    now[0] += 50000
    engine.ingest_driver_observation(event(frame=2, value=0.4))
    assert engine._route_runtime["person-0"].derivative_values
    now[0] += 50000
    engine.ingest_driver_observation(event(frame=3, state=1, value=0.4))
    assert engine.source_value("sensor.slot_0_pos").captured_at_us is None
    assert not engine._route_runtime["person-0"].derivative_values
    now[0] += 50000
    engine.ingest_driver_observation(event(frame=4, value=0.9))
    assert engine._route_runtime["person-0"].last_usable_output == pytest.approx(0.5)
    invalid = replace(
        event(),
        event_kind="slot_invalidated",
        reason="lease_expired",
        captured_frame_id=None,
        bundle_seq=None,
        captured_at_us=None,
        processed_at_us=None,
        queued_for_send_at_us=None,
        channel_values={"slot_0_pos": (0.0, 2, 0.0)},
    )
    now[0] += 1000
    assert engine.ingest_driver_observation(invalid)
    now[0] += 200000
    engine.tick()
    assert any(
        r.bindings["N"] == 0 and r.reason == "route_reset" for r in recorder.records
    )
    assert not engine.ingest_driver_observation(event(frame=4, value=0.9))
    # Receiver expiry is not a producer frame and does not erase the watermark.
    now[0] += 1000
    assert engine.ingest_driver_observation(event(frame=5, value=0.7))
    assert engine._route_runtime["person-0"].last_usable_output == pytest.approx(0.5)


def test_trace_preserves_producer_and_adapter_ids_without_clock_conversion(
    monkeypatch, tmp_path
):
    engine, _, source, now = setup(monkeypatch)
    report = ReportWriter(tmp_path, run_id="observation")
    engine.report_writer = report
    sample = event()
    assert engine.ingest_driver_observation(sample)
    rows = [
        json.loads(s)
        for s in (report.path / "state_timestamps.jsonl").read_text().splitlines()
    ]
    row = next(r for r in rows if r["phase"] == "driver_observation_received")
    assert row["observation"] == json.loads(json.dumps(sample.to_dict()))
    assert row["adapter_contract_id"] == source["contract_id"] != sample.contract_id
    assert row["adapter_stream_id"] == "0000000000000001" != sample.stream_id
    assert row["engine_applied_at_us"] == now[0] != sample.received_at_us
    assert row["engine_clock"] == "engine_configured_us"
    source_trace = next(r for r in rows if r["phase"] == "source_received")
    assert source_trace["capture_clock"] == sample.capture_clock
    assert source_trace["receipt_clock"] == "engine_configured_us"


def test_invalid_payload_is_atomic_and_source_gate_remains_required(monkeypatch):
    engine, _, source, now = setup(monkeypatch)
    with pytest.raises(WeaverError, match="every declared channel of its slot"):
        engine.ingest_driver_observation(replace(event(), channel_values={}))
    assert not engine._driver_observation_watermarks
    with pytest.raises(WeaverError, match="outside"):
        engine.ingest_driver_observation(event(value=2.0))
    assert not engine._driver_observation_watermarks
    assert engine.ingest_driver_observation(event())
    assert not engine.source_hello("sensor", "0000000000000001", "wrong-contract")
    assert not engine.ingest_driver_observation(event(frame=2))


@pytest.mark.parametrize("mode", ["legacy", "v2"])
def test_launcher_choice_and_real_wire_two_person_ingestion(monkeypatch, mode):
    from argparse import Namespace
    from harmonic_weaver.engine import WeaverEngine
    from rehearsal.weaver_runtime import (
        make_harmocap_driver,
        harmocap_manifest,
        build_parser,
    )
    from test_harmocap_observation_events import fixture
    from test_harmocap_driver import frame_to_wire, handshake_bytes

    assert build_parser().parse_args([]).harmocap_events == "legacy"
    now = [9000000000]
    engine = WeaverEngine(clock_us=lambda: now[0])
    manifest = harmocap_manifest()
    contract = engine.install_source(manifest)
    engine.source_hello("harmocap", "0000000000000001", contract)
    driver = make_harmocap_driver(
        engine, Namespace(harmocap_events=mode), lease_ms=100.0
    )
    hello, frame = fixture()
    for packet in handshake_bytes(hello):
        driver.handle_datagram(packet, now_ms=1000)
    packets = frame_to_wire(frame, 10)
    driver.handle_datagram(packets[0], now_ms=1000)
    slot = frame["persons"][0]["slot_id"]
    address = f"harmocap.slot_{slot}_present"
    before = engine.source_value(address)
    now[0] += 1000
    driver.handle_datagram(packets[1], now_ms=1001)
    after = engine.source_value(address)
    assert (before == after) == (mode == "v2")
    assert engine.metrics["frames_accepted"] == 2 and driver.stats.callback_errors == 0
    if mode == "v2":
        assert after.captured_at_us == frame["captured_at_us"]
        driver.tick(now_ms=1102)
        assert engine.metrics["frames_accepted"] == 4
        assert engine.source_value(address).captured_at_us is None


def test_new_capture_epoch_warms_derivative_even_if_invalidation_was_lost(monkeypatch):
    engine, _, _, now = setup(monkeypatch, derivative=True)
    engine.ingest_driver_observation(event())
    now[0] += 50000
    engine.ingest_driver_observation(event(frame=2, value=0.4))
    now[0] += 10000
    assert engine.ingest_driver_observation(
        replace(event(frame=1, value=0.9), calibration_generation=2)
    )
    assert engine._route_runtime["person-0"].last_usable_output == pytest.approx(0.5)
