from __future__ import annotations

from engine_fixtures import ready_engine


def test_registry_snapshot_contains_patchbay_manifest_metadata() -> None:
    engine, _recorder, source_manifest, instrument_manifest = ready_engine()

    snapshot = engine.snapshot(["sources", "instruments"])

    source = snapshot["sources"][0]
    instrument = snapshot["instruments"][0]
    assert source["channel_specs"] == source_manifest["channels"]
    assert source["description"] == source_manifest["source"]["description"]
    assert instrument["capabilities"] == instrument_manifest["capabilities"]
    assert instrument["description"] == instrument_manifest["instrument"]["description"]
