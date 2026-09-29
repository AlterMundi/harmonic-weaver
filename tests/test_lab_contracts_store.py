from concurrent.futures import ThreadPoolExecutor
import json

import pytest
from pydantic import ValidationError

from harmonic_weaver.lab.contracts import Calibration, MotionFrame, Preset
from harmonic_weaver.lab.store import RevisionConflict, SessionStore


def test_preset_is_portable_and_versions_fail_closed():
    preset = Preset()
    assert len(preset.voices) == 6 and preset.algorithm.components == 3
    assert Preset.model_validate_json(preset.model_dump_json()) == preset
    for patch in ({"source_id": "private-video"}, {"schema_version": 2},
                  {"master": float("nan")}, {"master": True},
                  {"algorithm": {"id": "future-model"}}, {"voices": preset.model_dump()["voices"][:3]}):
        with pytest.raises(ValidationError):
            Preset.model_validate({**preset.model_dump(), **patch})


def test_persistent_configuration_and_calibration_are_separate(tmp_path):
    store = SessionStore(tmp_path)
    preset = Preset(name="Movimiento relativo")
    store.save(preset)
    store.edit(preset, 0)
    store.set_runtime(source_id="one", person_id="person-a", position_s=13.0)
    store.save_calibration(Calibration(source_id="one", person_id="person-a", torso_scale=.4,
                                      measured_at="2026-09-29", provenance="observed shoulders/pelvis"))
    store.mark("Se siente bien")
    old_session = store.state.session_id
    store.close()
    reopened = SessionStore(tmp_path)
    assert reopened.load(preset.id) == preset
    assert reopened.preset == preset and reopened.state.desired_revision == 1
    assert reopened.state.source_id is None and reopened.state.position_s == 0
    assert reopened.state.calibration_id is None and reopened.state.session_id != old_session
    assert reopened.calibrations()[0]["source_id"] == "one"
    assert all(e["kind"] in {"configuration", "preset_save", "calibration", "mark"} for e in reopened.events())
    assert "joints" not in json.dumps(reopened.events()[0])
    reopened.close()


def test_atomic_preparation_and_two_client_conflict(tmp_path):
    def prepare(p):
        if p.fundamental_hz > 100:
            raise ValueError("simulated graph preparation failure")
        return p.fundamental_hz
    store = SessionStore(tmp_path, prepare=prepare)
    original = store.snapshot()
    with pytest.raises(ValueError):
        store.edit(Preset(fundamental_hz=150), 0)
    assert store.snapshot() == original and not store.events()
    def edit(frequency):
        try:
            store.edit(Preset(fundamental_hz=frequency), 0)
            return "applied"
        except RevisionConflict:
            return "conflict"
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(edit, [50., 60.])) == ["applied", "conflict"]
    assert store.state.desired_revision == 1 and len(store.events()) == 1
    store.close()


def test_undo_and_macros_do_not_restore_source_history(tmp_path):
    store = SessionStore(tmp_path)
    p = Preset.model_validate({**store.preset.model_dump(), "macros": [
        {"id": "space", "label": "Espacio", "value": .5, "targets": [
            {"path": "fundamental_hz", "minimum": 20., "maximum": 80.},
            {"path": "algorithm.components", "minimum": 2., "maximum": 6.}]}]})
    store.edit(p, 0)
    store.apply_macro("space", 1., 1)
    assert store.preset.fundamental_hz == 80 and store.preset.algorithm.components == 6
    assert len(store.preset.voices) == 6
    store.set_runtime(source_id="new", position_s=7.)
    store.history(2)
    assert store.preset.fundamental_hz == 40.4
    assert store.state.source_id == "new" and store.state.position_s == 7
    store.history(3, redo=True)
    assert store.preset.fundamental_hz == 80
    invalid = p.model_dump()
    invalid["macros"][0]["targets"][0]["path"] = "voices.0.id"
    with pytest.raises(ValueError):
        store.edit(Preset.model_validate(invalid), 4)
    store.close()


def test_preset_rejects_ambiguous_destinations():
    p = Preset().model_dump()
    p["routes"].append({**p["routes"][0], "id": "duplicate-writer"})
    with pytest.raises(ValidationError, match="one final writer"):
        Preset.model_validate(p)


def test_motion_contract_preserves_shape_and_missingness():
    frame = dict(source_id="vfr", stream_id="one", sequence=1, source_time_s=.053,
                 available_monotonic_s=1., timestamp_origin="pts", width=720, height=1280,
                 persons=[{"person_id": "a", "joints": [
                     {"index": 5, "position": [.2, .4], "confidence": .9, "state": "observed"},
                     {"index": 6, "state": "missing"}]}])
    model = MotionFrame.model_validate(frame)
    assert model.persons[0].joints[1].position is None
    frame["persons"][0]["joints"][0]["position"].append(.9)
    with pytest.raises(ValidationError, match="dimension differs"):
        MotionFrame.model_validate(frame)
