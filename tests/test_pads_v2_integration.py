"""Integration tests for continuous source-owned Pads v2 routing."""

from __future__ import annotations

import json
from pathlib import Path

from harmonic_weaver.contract_codec import contract_id_from_manifest
from harmonic_weaver.engine import INVALID, OBSERVED, RecordingOutputTransport, WeaverEngine
from rehearsal.weaver_runtime import harmocap_manifest, shaper_safety_profile


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT.parent
SHAPER_MANIFEST = PROJECTS / "harmonic-shaper" / "contracts" / "shaper.contract.json"
PADS_V2 = ROOT / "rehearsal" / "scenes" / "pads_v2.scene.json"
HARMOCAP_X_SPAN = 16.0 / 9.0


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ready_engine() -> tuple[WeaverEngine, RecordingOutputTransport]:
    recorder = RecordingOutputTransport()
    engine = WeaverEngine(transport=recorder)
    shaper = _load_json(SHAPER_MANIFEST)
    contract_id = contract_id_from_manifest(shaper)
    engine.install_instrument(shaper, shaper_safety_profile(contract_id))
    engine.instrument_hello("shaper", "00000000000000c1", contract_id)
    engine.instrument_sync_complete("shaper", "00000000000000c1", contract_id)

    manifest = harmocap_manifest(lease_ms=600_000)
    engine.install_source(manifest)
    engine.source_hello("harmocap", "00000000000000a1", manifest["contract_id"])
    engine.upsert_scene(_load_json(PADS_V2), engine.stage_revision)
    engine.switch_scene("pads-v2", 1, engine.stage_revision)
    return engine, recorder


def _emit_hand(
    engine: WeaverEngine,
    slot: int,
    side: str,
    nx: float,
    ny: float,
    *,
    present: bool = True,
    now_us: int = 0,
) -> None:
    wrist = "right_wrist" if side == "r" else "left_wrist"
    # Source-frame payloads use manifest channel names; the engine adds the
    # ``harmocap.`` address prefix when ingesting them.
    prefix = f"slot_{slot}"
    values = {
        item["name"]: (0.0, INVALID, 0.0)
        for item in harmocap_manifest(lease_ms=600_000)["channels"]
    }
    values.update(
        {
            f"{prefix}_present": (1.0 if present else 0.0, OBSERVED, 1.0),
            f"{prefix}_keypoint_{wrist}_x": (nx, OBSERVED, 1.0),
            f"{prefix}_keypoint_{wrist}_y": (ny, OBSERVED, 1.0),
        }
    )
    engine.ingest_driver_frame("harmocap", values)


def _source_writes(records, harmonic: int, source: int):
    return [
        record
        for record in records
        if record.capability == "harmonic_source_envelope"
        and record.reason == "route"
        and record.bindings == {"N": harmonic, "S": source}
    ]


def test_pads_v2_compiles_full_grid_for_both_hands_of_two_people() -> None:
    engine, _ = _ready_engine()
    snapshot = engine.snapshot(["routes"])
    assert len(snapshot["routes"]) == 128
    assert {
        route["destination"]["bindings"]["S"]
        for route in snapshot["routes"]
    } == {0, 1, 2, 3}
    assert {
        route["destination"]["bindings"]["N"]
        for route in snapshot["routes"]
    } == set(range(1, 33))


def test_each_hand_continuously_activates_exactly_its_current_harmonic() -> None:
    engine, recorder = _ready_engine()
    _emit_hand(engine, 0, "r", HARMOCAP_X_SPAN * 0.88, 0.88)
    _emit_hand(engine, 0, "l", HARMOCAP_X_SPAN * 0.88, 0.12)

    # Grid origin is N=1; the upper cell of the first serpentine column is N=8.
    assert any(record.value == 1.0 for record in _source_writes(recorder.records, 1, 0))
    assert any(record.value == 1.0 for record in _source_writes(recorder.records, 8, 1))
    for source, selected in ((0, 1), (1, 8)):
        active = {
            record.bindings["N"]
            for record in recorder.records
            if record.capability == "harmonic_source_envelope"
            and record.reason == "route"
            and record.bindings["S"] == source
            and record.value > 0.0
        }
        assert active == {selected}


def test_full_grid_is_bottom_left_origin_with_serpentine_columns() -> None:
    """Visual grid: H1 rises in the left column; each next column reverses."""
    for column in range(4):
        for row_from_bottom in range(8):
            engine, recorder = _ready_engine()
            # HarMoCAP coordinates are mirrored in X and have Y=0 at the top.
            x = HARMOCAP_X_SPAN * (1.0 - (column + 0.5) / 4.0)
            y = 1.0 - (row_from_bottom + 0.5) / 8.0
            _emit_hand(engine, 0, "r", x, y)
            expected = column * 8 + (
                row_from_bottom if column % 2 == 0 else 7 - row_from_bottom
            ) + 1
            active = {
                record.bindings["N"]
                for record in recorder.records
                if record.capability == "harmonic_source_envelope"
                and record.reason == "route"
                and record.bindings["S"] == 0
                and record.value > 0.0
            }
            assert active == {expected}


def test_same_pad_from_two_hands_keeps_independent_source_ownership() -> None:
    engine, recorder = _ready_engine()
    _emit_hand(engine, 0, "r", HARMOCAP_X_SPAN * 0.88, 0.88)
    _emit_hand(engine, 0, "l", HARMOCAP_X_SPAN * 0.88, 0.88)

    assert any(record.value == 1.0 for record in _source_writes(recorder.records, 1, 0))
    assert any(record.value == 1.0 for record in _source_writes(recorder.records, 1, 1))


def test_absent_person_does_not_activate_a_hand() -> None:
    engine, recorder = _ready_engine()
    _emit_hand(engine, 1, "r", HARMOCAP_X_SPAN * 0.88, 0.88, present=False)
    active = [
        record
        for record in recorder.records
        if record.capability == "harmonic_source_envelope"
        and record.reason == "route"
        and record.bindings["S"] == 2
        and record.value > 0.0
    ]
    assert active == []
