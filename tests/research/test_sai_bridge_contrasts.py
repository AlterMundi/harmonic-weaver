import json
from pathlib import Path

import numpy as np
import pytest

from harmonic_weaver.lab.contracts import MotionFrame
from harmonic_weaver.lab.contracts import AlgorithmSettings
from harmonic_weaver.lab.collective import CausalSubspace
from research.laboratory.sai_bridge.adapter import common_observed, read_models
from research.laboratory.sai_bridge.prediction import (
    prediction_contrast, require_causal, require_same_support, support_selection_control,
)
from research.laboratory.sai_bridge.synthetic import (
    ambiguous_observation_frames, ambiguous_projection, common_rhythm_no_pair_coupling,
    concentration, diagonal_counterexample, equal_path_rhythm, event_phase,
    frame_controls, motion_frame, paired_cycles, phase_controls, plane_pair, spacetime_c,
)

FIXTURES = Path(__file__).resolve().parents[2] / "research/laboratory/sai_bridge/fixtures"


def test_contract_fixture_and_separate_3d_truth():
    frame = MotionFrame.model_validate(json.loads((FIXTURES / "observation.json").read_text()))
    truth = json.loads((FIXTURES / "truth.json").read_text())
    assert frame.dimensions == 2 and frame.timestamp_origin == "synthetic"
    assert frame.source_time_s < frame.available_monotonic_s
    assert all(j.position is None or len(j.position) == 2 for j in frame.persons[0].joints)
    for name in ("world_a_xyz", "world_b_xyz"):
        x, y, z = truth[name]
        assert [x/z, y/z] == pytest.approx(truth["image_uv"])
    assert truth["world_a_xyz"] != truth["world_b_xyz"]


def test_reproduced_geometry_time_phase_and_projection_banks():
    rhythm = equal_path_rhythm()
    assert rhythm["uniform"]["time_half"] == pytest.approx(.5, abs=.002)
    assert rhythm["warped"]["time_half"] == pytest.approx(.3246, abs=.003)
    assert rhythm["uniform"]["arc_half"] == pytest.approx(.5, abs=.002)
    assert rhythm["warped"]["arc_half"] == pytest.approx(.5, abs=.002)
    aligned, delta_a = paired_cycles(opposed=False)
    opposed, delta_b = paired_cycles(opposed=True)
    assert len(aligned) == len(opposed) == 241
    assert concentration(delta_a) == pytest.approx(1.)
    assert concentration(delta_b) == pytest.approx(.077246, abs=.0001)
    for joint_index in (9, 10):
        def speeds(frames):
            xy = np.array([f.persons[0].joints[joint_index].position for f in frames])
            return np.linalg.norm(np.diff(xy, axis=0), axis=1) * 60
        if joint_index == 9:
            assert speeds(aligned) == pytest.approx(speeds(opposed))
        else:
            assert np.sort(speeds(aligned)) == pytest.approx(np.sort(speeds(opposed)))
    assert plane_pair()["xy"] == pytest.approx([.5, .5, 0.], abs=.001)
    assert plane_pair()["xz"] == pytest.approx([.5, 0., .5], abs=.001)
    ambiguity = ambiguous_projection()
    assert ambiguity["image_max_difference"] < 1e-12
    assert ambiguity["arc_3d_b"] > 2 * ambiguity["arc_3d_a"]
    phase = phase_controls()
    assert phase["error_deg"] == pytest.approx(-36.)
    assert phase["warmup"] == "warmup" and phase["expired"] == "expired"
    with pytest.raises(ValueError, match="future"):
        event_phase(2.4, [0., 1., 2., 2.8])


def test_q_is_not_tensor_or_phase_and_frame_is_declared():
    counter = diagonal_counterexample()
    assert counter["q_a"] == pytest.approx(counter["q_b"])
    assert counter["projector_gap"] > 1.
    common = common_rhythm_no_pair_coupling()
    assert min(common["within_session_r"]) > .999
    assert common["pooled_r"] < 1e-12
    frame = frame_controls()
    assert frame["translated_edge_error"] < 1e-12
    assert frame["rotating_camera_edge_arc"] > .1
    assert frame["rotating_body_edge_arc"] < 1e-12
    # The signed half-plane speed contrast is a 2D analogue, not Sai's C contract.
    assert abs(spacetime_c()["uniform"]) < .02
    assert abs(spacetime_c()["warped"]) > .05


def test_degenerate_plane_does_not_invent_a_unique_collective_axis():
    subspace = CausalSubspace(AlgorithmSettings(components=1, noise_velocity=.001))
    for k in range(40):
        angle = k * np.pi/2
        subspace.push(k*.025, [np.cos(angle), np.sin(angle)], ["x", "y"])
    result = subspace.push(1., [1., 0.], ["x", "y"])
    assert result["state"] == "missing"
    assert result["reason"] == "degenerate component boundary"


def test_prediction_bank_uses_fair_capacity_and_session_holdout():
    null, related = prediction_contrast(False), prediction_contrast(True)
    assert null["held_sessions"] == related["held_sessions"] == 4
    assert null["held_units"] == related["held_units"] == 480
    assert abs(null["linear_relation_rmse"] - null["linear_rmse"]) < .02
    assert related["linear_relation_rmse"] < related["linear_rmse"] / 3
    assert abs(related["matched_nonlinear_rmse"] - related["linear_relation_rmse"]) < .02
    biased = support_selection_control()
    assert biased["unmatched_rejected"]
    assert biased["invalid_full_linear_rmse"] > 3 * biased["invalid_easy_relation_rmse"]
    assert biased["matched_easy_linear_rmse"] <= biased["matched_easy_relation_rmse"]


def test_causal_guard_and_identical_support_reject_future_or_selection():
    row = {"session": 1, "cycle": 2, "origin": 2., "latest": 2., "available": 2.,
           "target_start": 3., "target": 1.}
    require_causal([row])
    require_same_support([row], [dict(row)])
    with pytest.raises(ValueError, match="unavailable"):
        require_causal([dict(row, available=3.)])
    with pytest.raises(ValueError, match="support"):
        require_same_support([row], [])
    with pytest.raises(ValueError, match="support"):
        require_same_support([row], [dict(row, target=2.)])


def test_weaver_models_are_prefix_causal_and_missingness_is_not_zero():
    frames = ambiguous_observation_frames(48)
    prefix = read_models(frames[:30])
    changed_future = frames[:30] + [motion_frame(k/48, k, left=[.8, .8])
                                     for k in range(30, 49)]
    extended = read_models(changed_future)
    for algorithm in prefix:
        assert prefix[algorithm] == extended[algorithm][:30]
        assert all(row["available_monotonic_s"] >= row["source_time_s"]
                   for row in prefix[algorithm])
    # Held and missing observations must not become zero-valued measurements.
    gap = frames[:20] + [motion_frame(20/48, 20, states={9: "held", 10: "missing"})] + frames[21:]
    outputs = read_models(gap, algorithms=("local", "relational", "angular", "collective"))
    for algorithm, records in outputs.items():
        assert records[20]["signals"].get("zone.6.speed", {}).get("state") != "observed"
    assert outputs["relational"][20]["zone6_relations"][0]["state"] == "missing"
    assert outputs["relational"][20]["signals"]["zone.6.I"]["value"] is None
    # Per-edge diagnostics can be valid even though a static opposite wrist makes
    # the bilateral zone aggregate missing; this is a candidate interface gap.
    assert any(row["zone6_relations"][0]["state"] == "observed"
               for row in outputs["relational"][:20])
    assert not common_observed(outputs["relational"], outputs["relational"], "zone.6.I")


def test_stream_identity_and_seek_do_not_inherit_previous_derivatives():
    first = ambiguous_observation_frames(30)[:20]
    second = [motion_frame(k/30, k, left=[.3 + .01*k, .4], stream="new", person="p1")
              for k in range(12)]
    combined = read_models(first + second, algorithms=("local", "relational", "angular", "collective"))
    fresh = read_models(second, algorithms=("local", "relational", "angular", "collective"))
    for algorithm in combined:
        assert combined[algorithm][20:] == fresh[algorithm]
