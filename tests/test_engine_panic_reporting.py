from __future__ import annotations

import json

from harmonic_weaver.engine import OBSERVED, ReportWriter, WeaverError, WeaverEngine

from engine_fixtures import instrument_manifest, ready_engine, route, safety_profile, scene, source_manifest


def test_panic_is_latched_suppresses_routes_and_requires_explicit_recovery() -> None:
    engine, recorder, source, _instrument = ready_engine()
    engine.upsert_scene(scene(routes=[route()]), engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    recorder.clear()
    engine.ingest_source_frame("sensor", "0000000000000001", source["contract_id"], 0, {"modulation": (0.8, OBSERVED, 1.0)}, now_us=0)
    assert recorder.records[-1].value == 0.8

    ack = engine.trigger_panic("operator test")
    assert ack["status"] == "latched"
    generation = ack["panic_generation"]
    panic_record_count = len(recorder.records)
    assert engine.trigger_panic()["status"] == "already_latched"
    engine.ingest_source_frame("sensor", "0000000000000001", source["contract_id"], 1, {"modulation": (0.2, OBSERVED, 1.0)}, now_us=10)
    assert len(recorder.records) == panic_record_count

    recovered = engine.clear_panic(generation, "main", 1)
    assert recovered["status"] == "recovered"
    assert not engine.panic_active
    before = len(recorder.records)
    engine.ingest_source_frame(
        "sensor", "0000000000000001", source["contract_id"], 2,
        {"modulation": (0.5, OBSERVED, 1.0)}, now_us=engine._clock_us() + 300_000,
    )
    assert len(recorder.records) == before + 1
    assert recorder.records[-1].value == 0.5


def test_report_writer_contains_measured_engine_evidence(tmp_path) -> None:
    report = ReportWriter(tmp_path, run_id="engine-evidence", run_config={"test": True})
    engine = WeaverEngine(report_writer=report)
    source = source_manifest()
    instrument = instrument_manifest()
    engine.install_source(source)
    engine.source_hello("sensor", "0000000000000001", source["contract_id"])
    engine.install_instrument(instrument, safety_profile(instrument))
    engine.instrument_hello("synth", "0000000000000002", instrument["contract_id"])
    engine.instrument_sync_complete("synth", "0000000000000002", instrument["contract_id"])
    engine.upsert_scene(scene(routes=[route()]), engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    engine.ingest_source_frame("sensor", "0000000000000001", source["contract_id"], 0, {"modulation": (0.25, OBSERVED, 1.0)})
    engine.close()

    path = tmp_path / "engine-evidence"
    expected = {
        "run_config.json", "accepted_contract_ids.json", "scene_snapshot.json",
        "behavior_events.jsonl", "state_timestamps.jsonl",
        "latency_summary.json", "summary.json",
    }
    assert expected.issubset({item.name for item in path.iterdir()})
    latency = json.loads((path / "latency_summary.json").read_text())
    assert latency["weaver_receipt_to_instrument_send"]["sample_count"] == 1
    assert latency["audio"]["status"] == "not_measured"
