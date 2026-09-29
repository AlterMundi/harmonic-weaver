import numpy as np
import pytest

from harmonic_weaver.lab.collective import CausalSubspace, DeploymentEvents, align_basis, principal_angles
from harmonic_weaver.lab.contracts import AlgorithmSettings


def test_basis_rotations_and_sign_changes_do_not_create_new_geometry():
    basis = np.eye(4)[:, :2]
    angle = .8
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    changed = basis @ rotation
    aligned = align_basis(changed, basis)
    assert aligned == pytest.approx(basis)
    assert principal_angles(changed, basis) == pytest.approx([0., 0.], abs=1e-7)
    assert align_basis(-basis, basis) == pytest.approx(basis)


def test_collective_predicts_new_observation_using_only_past():
    settings = AlgorithmSettings(components=1, noise_velocity=.001)
    model = CausalSubspace(settings)
    for i in range(30):
        model.push(i/30, [np.sin(i/5), 0.], ["x", "y"])
    result = model.push(1., [0., 50.], ["x", "y"])
    assert result["state"] == "observed"
    assert result["projector"] == pytest.approx(np.array([[1., 0.], [0., 0.]]))
    assert result["residual"] > .99
    assert result["history_end_s"] < 1.
    assert len(result["amplitudes"]) == 1  # never constrains synthesis voice count


def test_missingness_support_changes_and_quiet_are_not_zero_padded_modes():
    model = CausalSubspace(AlgorithmSettings(components=1))
    for i in range(15):
        result = model.push(i/30, [1., 1.], ["x", "y"])
    assert result["reason"] == "no established collective mode"
    assert model.push(.5, [np.nan, 0.], ["x", "y"])["reason"] == "missing collective support"
    assert not model.history
    result = model.push(.6, [1., 0.], ["x", "z"])
    assert result["past_samples"] == 0


def test_degenerate_cut_is_reported_rather_than_emitting_unstable_axis():
    model = CausalSubspace(AlgorithmSettings(components=1, noise_velocity=.001))
    for i in range(40):
        model.push(i*.025, [np.cos(i*np.pi/2), np.sin(i*np.pi/2)], ["x", "y"])
    result = model.push(1., [1., 0.], ["x", "y"])
    assert result["state"] == "missing"
    assert result["reason"] == "degenerate component boundary"


def test_deployment_has_multiple_candidates_and_no_forced_center():
    model = DeploymentEvents(AlgorithmSettings())
    assert not any(v["candidate"] for v in model.push(0., {"hips": 0., "wrist": 0.}).values())
    events = model.push(.1, {"hips": 2., "wrist": 3.})
    assert events["hips"]["candidate"] and events["wrist"]["candidate"]
    assert not any(v["candidate"] for v in model.push(.5, {"hips": 2., "wrist": 3.}).values())
    model.push(.6, {"hips": 0., "wrist": None})
    assert model.push(.7, {"hips": 2., "wrist": 0.})["hips"]["candidate"]
