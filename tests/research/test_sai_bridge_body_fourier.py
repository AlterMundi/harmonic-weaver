from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from harmonic_weaver.lab.contracts import Preset
from research.laboratory.sai_bridge.body_fourier import (
    BodyConfig, block_values, compare_blocks, control_frames,
    compare_signal, effective_modules, geometric_diagnostics, observe_body, prepare_blocks, synthetic_frames,
)

CHANNELS = ((7, 0), (7, 1), (9, 0), (9, 1), (8, 0), (8, 1), (10, 0), (10, 1))
FIXTURE = Path(__file__).resolve().parents[2] / "research/laboratory/sai_bridge/fixtures/body_fourier_public.json"


def config(**overrides):
    return replace(BodyConfig("athlete", CHANNELS, 60., .26, "frame_height",
                              "declared synthetic reference", min_samples=8), **overrides)


def frames(kind="coupled", n=128, stream="epoch0", **events):
    return synthetic_frames({"sample_hz": 60., "epochs": [
        {"stream_id": stream, "kind": kind, "samples": n, **events}]})


def preset():
    p = Preset(id="body_test")
    p.algorithm.id = "relational"
    p.response.pluck_enabled = False
    return p


def prepared(values, cfg=None):
    return prepare_blocks(values, cfg or config(), provenance={"kind": "public test construction"})


def test_explicit_person_and_deep_frozen_content_preserved():
    source = frames(n=16)
    blocks, support = prepared(source)
    assert len(blocks) == 1 and support["retained_frames"] == 16
    block = blocks[0]
    np.testing.assert_array_equal(block.values(), block_values(block))
    expected = block.values().copy()
    source[0].persons[0].joints[7].position[0] += 1
    np.testing.assert_array_equal(expected, block.values())
    controls, _ = control_frames(block, seed=7)
    for i, frozen in enumerate(block.frames):
        for condition in controls.values():
            frame = condition[i]
            assert frame.source_id == frozen.source_id and frame.stream_id == frozen.stream_id
            assert frame.source_time_s == frozen.source_time_s
            assert frame.available_monotonic_s == frozen.available_monotonic_s
            assert frame.sequence == frozen.sequence and frame.unit == frozen.unit
            assert frame.timestamp_origin == frozen.timestamp_origin
            assert frame.coordinate_frame == frozen.coordinate_frame
            assert next(p for p in frame.persons if p.person_id == "bystander").model_dump() == next(
                p for p in frozen.persons if p.person_id == "bystander").model_dump()
            selected = next(p for p in frame.persons if p.person_id == "athlete")
            original = next(p for p in frozen.persons if p.person_id == "athlete")
            for j in (0, 5, 6, 11, 12, 13):
                assert selected.joints[j].model_dump() == original.joints[j].model_dump()
    assert controls["original"][0].model_dump() == block.frames[0].model_dump()


def test_gap_invalid_absent_and_epochs_have_accounted_support():
    source = frames(n=60, drop_indices=list(range(16, 34)), invalid_indices=[46], absent_indices=[57])
    source += frames(n=16, stream="epoch1")
    blocks, support = prepared(source)
    assert [len(b.frames) for b in blocks] == [16, 12, 10, 16]
    assert support["input_frames"] == support["retained_frames"]+support["excluded_frames"]
    assert support["exclusion_counts"] == {
        "selected_joint_invalid": 1, "selected_person_absent": 1, "short_block": 2}
    assert "gap" in [b["reason"] for b in support["boundaries"]]
    # Identical source times in different epochs cannot mix model histories.
    assert blocks[-1].frames[0].source_time_s == 0
    assert blocks[-1].frames[0].stream_id == "epoch1"


@pytest.mark.parametrize("mutation,reason", [
    ("held", "selected_joint_invalid"), ("confidence", "selected_joint_invalid"),
    ("unit", "scale_unit_mismatch"), ("duplicate", "nonincreasing_time_in_epoch")])
def test_invalid_rows_split_without_filling(mutation, reason):
    source = frames(n=20)
    f = source[10]
    selected = next(p for p in f.persons if p.person_id == "athlete")
    if mutation == "held":
        selected.joints[9].state = "held"
    elif mutation == "confidence":
        selected.joints[9].confidence = .1
    elif mutation == "unit":
        f.unit = "meter"
    else:
        f.source_time_s = source[9].source_time_s
    blocks, support = prepared(source)
    assert reason in support["exclusion_counts"]
    assert all(10 not in b.input_indices for b in blocks)
    assert support["retained_frames"]+support["excluded_frames"] == 20


def test_irregular_sampling_and_drift_do_not_become_an_fft_grid_silently():
    source = frames(n=20)
    source[10].source_time_s += .001
    _, support = prepared(source)
    assert "irregular_interval" in [b["reason"] for b in support["boundaries"]]
    tiny = frames(n=20)
    tolerance = config().absolute_tolerance_s+config().relative_tolerance/60
    for k, frame in enumerate(tiny):
        frame.source_time_s += k*tolerance*.6
    _, drift = prepared(tiny)
    assert "sampling_grid_drift" in [b["reason"] for b in drift["boundaries"]]
    valid = frames(n=20)
    valid[10].source_time_s += tolerance*.1
    blocks, accepted = prepared(valid)
    assert len(blocks) == 1 and accepted["retained_frames"] == 20
    assert blocks[0].frames[10].source_time_s == valid[10].source_time_s


def test_no_scale_or_provenance_is_inferred_and_channels_are_explicit():
    for kwargs in ({"scale": 0.}, {"scale_provenance": ""}, {"channels": ((9, 0), (9, 0))},
                   {"channels": ((9, True),)}, {"minimum_confidence": 2.}):
        with pytest.raises(ValueError):
            config(**kwargs)
    with pytest.raises(ValueError, match="provenance"):
        prepare_blocks(frames(), config(), provenance={})


@pytest.mark.parametrize("n", [127, 128])
def test_body_controls_preserve_spectra_and_shared_cross_spectra(n):
    blocks, _ = prepared(frames(n=n))
    controls, checks = control_frames(blocks[0], seed=7)
    for condition in ("shared", "independent"):
        assert checks[condition]["full_coordinates"]["power_max_relative_error"] < 1e-12
        assert checks[condition]["full_coordinates"]["mean_max_absolute_error"] < 1e-12
    assert checks["shared"]["fluctuations"]["cross_spectrum_max_relative_change"] < 1e-12
    assert checks["independent"]["fluctuations"]["cross_spectrum_max_relative_change"] > .1
    x = block_values(blocks[0])
    y = block_values(replace(blocks[0], frames=tuple(controls["shared"])))
    assert not np.allclose(x, y)


def test_rigid_links_can_be_distorted_even_by_shared_phase_control():
    block = prepared(frames("articulated", n=128))[0][0]
    controls, _ = control_frames(block, seed=7)
    for condition in ("shared", "independent"):
        geometry = geometric_diagnostics(controls["original"], controls[condition], person_id="athlete")
        assert geometry["unit"] == "frame_height"
        segment = geometry["segments"]["7-9"]
        assert segment["original_std"] < 1e-12
        assert segment["paired_length_max_change"] > .001
    geometry = geometric_diagnostics(controls["original"], controls["original"], person_id="athlete")
    assert geometry["segments"]["7-9"]["paired_length_mae"] == 0


def test_descriptor_selection_is_not_first_person_and_replay_is_prefix_causal():
    source = frames(n=64)
    outputs = observe_body(source, person_id="athlete", scale=.26, preset=preset())
    selected = []
    for frame in source:
        clone = frame.model_copy(deep=True)
        clone.persons = [p for p in clone.persons if p.person_id == "athlete"]
        selected.append(clone)
    assert outputs == observe_body(selected, person_id="athlete", scale=.26, preset=preset())
    assert outputs[:32] == observe_body(source[:32], person_id="athlete", scale=.26, preset=preset())


def test_single_coordinate_and_static_are_negative_not_manufactured_scores():
    for kind, cfg in (("single_channel", config(channels=((9, 0),))), ("static", config())):
        block = prepared(frames(kind, n=64), cfg)[0][0]
        controls, _ = control_frames(block, seed=7)
        assert [f.model_dump() for f in controls["shared"]] == [f.model_dump() for f in controls["independent"]]
        compared = compare_blocks([block], seeds=[7], preset=preset())["results"][0]
        assert compared["descriptors"]["zone.6.I"]["common_observed"] == 0
        assert compared["descriptors"]["zone.6.I"]["conditions"]["original"]["common_mean"] is None
        residual = compared["descriptors"]["collective.residual"]
        if residual["common_observed"]:
            assert residual["common_shared_independent_mae"] == 0


def test_fresh_history_after_each_block_and_same_preset():
    blocks, _ = prepared(frames(n=64)+frames(n=64, stream="next"))
    results = compare_blocks(blocks, seeds=[7], preset=preset())
    assert results["preset"] == preset().model_dump()
    for signal in ("zone.6.I", "collective.residual"):
        a, b = (r["descriptors"][signal] for r in results["results"])
        assert a["conditions"] == b["conditions"]
        assert a["common_observed"] == b["common_observed"]
        assert [t["independent_minus_original"] for t in a["paired_temporal_differences"]] == [
            t["independent_minus_original"] for t in b["paired_temporal_differences"]]


def test_public_fixture_spec_has_variable_pose_multiple_people_and_epochs():
    spec = json.loads(FIXTURE.read_text())
    assert spec["algorithm"] == preset().algorithm.model_dump()
    source = synthetic_frames(spec)
    assert len({f.stream_id for f in source}) == 5
    assert any(len(f.persons) == 1 for f in source)
    assert any(f.persons[0].person_id == "bystander" for f in source)
    assert any(next(p for p in f.persons if p.person_id == "athlete").joints[9].state == "missing"
               for f in source if any(p.person_id == "athlete" for p in f.persons))


def test_body_surrogates_are_offline_even_with_preserved_availability():
    source = frames(n=128)
    block = prepared(source)[0][0]
    original_controls, _ = control_frames(block, seed=7)
    for frame in source[64:]:
        person = next(p for p in frame.persons if p.person_id == "athlete")
        person.joints[9].position[0] += .1
    changed_controls, _ = control_frames(prepared(source)[0][0], seed=7)
    left = block_values(replace(block, frames=tuple(original_controls["shared"])))
    right = block_values(replace(block, frames=tuple(changed_controls["shared"])))
    assert np.max(abs(left[:64]-right[:64])) > .001


def test_contract_invalid_input_is_a_hard_error_not_a_filled_sample():
    source = frames(n=16)
    source[8].persons[0].joints[9].position[0] = float("nan")
    with pytest.raises(ValueError):
        prepared(source)


def test_sources_metadata_and_nonselected_invalid_geometry():
    source = frames(n=16)+frames(n=16)
    for frame in source[16:]:
        frame.source_id = "second_source"
        frame.width = 800
    blocks, support = prepared(source)
    assert len(blocks) == 2
    assert support["boundaries"][0]["reason"] == "identity_or_metadata_change"
    for frame in blocks[1].frames:
        person = next(p for p in frame.persons if p.person_id == "athlete")
        person.joints[5].state, person.joints[5].position = "missing", None
    geometry = geometric_diagnostics(blocks[1].frames, blocks[1].frames, person_id="athlete")
    assert geometry["segments"]["5-7"]["common_observed"] == 0
    assert geometry["segments"]["5-7"]["paired_length_mae"] is None


def test_paired_traces_use_three_way_observed_support_and_exact_identities():
    def row(t, value):
        return {"source_id": "s", "stream_id": "epoch", "person_id": "p", "source_time_s": t,
                "sequence": int(t), "signals": {"I": {"state": "observed" if value is not None else "missing",
                    "value": value, "unit": "1", "reason": "no mode" if value is None else None}}}
    rows = {"original": [row(0., 1), row(1., 100)], "shared": [row(0., 2), row(1., None)],
            "independent": [row(0., 4), row(1., -100)]}
    result = compare_signal(rows, "I")
    assert result["common_observed"] == 1
    assert result["paired_temporal_differences"] == [{"identity": ["s", "epoch", "p", 0.],
        "sequence": 0, "shared_minus_original": 1, "independent_minus_original": 3,
        "shared_minus_independent": -2}]
    assert result["missing_reason_counts"]["shared"] == {"no mode": 1}


def test_effective_producers_resolve_imported_phase_and_frozen_driver():
    manifest = effective_modules()
    assert "research.laboratory.sai_bridge.fourier" in manifest
    assert "weaver_lab_frozen_driver" in manifest
    assert all(Path(entry["path"]).is_file() for entry in manifest.values())


def test_serialized_public_boundary_motionframes_are_usable_without_generator():
    fixture = json.loads(FIXTURE.with_name("body_fourier_boundary_frames.json").read_text())
    blocks, support = prepare_blocks(fixture["frames"], config(min_samples=4), provenance=fixture["provenance"])
    assert support["input_frames"] == 17
    assert [len(b.frames) for b in blocks] == [5, 6]
    assert support["retained_frames"] == 11 and support["excluded_frames"] == 6
    assert {b.frames[0].stream_id for b in blocks} == {"snapshot_a", "snapshot_b"}


def test_coupled_fixture_discrimination_and_local_noninvariance():
    block = prepared(frames(n=240))[0][0]
    result = compare_blocks([block], seeds=[7], preset=preset())["results"][0]
    residual = result["descriptors"]["collective.residual"]
    assert residual["common_observed"] > 200
    assert residual["conditions"]["shared"]["common_mean"] < .03
    assert residual["conditions"]["independent"]["common_mean"] > .15
    assert result["descriptors"]["zone.6.I"]["common_mae_from_original"]["shared"] > .2


def test_3d_is_explicitly_excluded_not_projected_silently():
    source = frames(n=8)
    for frame in source:
        frame.dimensions = 3
        for person in frame.persons:
            for joint in person.joints:
                joint.position.append(1.)
    blocks, support = prepared(source)
    assert not blocks
    assert support["exclusion_counts"] == {"unsupported_dimensions": 8}


def test_geometry_rejects_changed_units_and_preset_requires_explicit_description():
    source = frames(n=8)
    altered = [f.model_copy(deep=True) for f in source]
    altered[0].unit = "meter"
    with pytest.raises(ValueError, match="metadata"):
        geometric_diagnostics(source, altered, person_id="athlete")
    blocks, _ = prepared(source)
    p = preset()
    p.response.pluck_enabled = True
    with pytest.raises(ValueError, match="disabled"):
        compare_blocks(blocks, seeds=[7], preset=p)
