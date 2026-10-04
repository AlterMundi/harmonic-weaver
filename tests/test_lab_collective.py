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


def test_propagation_compares_predictors_on_shared_target_times():
    from harmonic_weaver.lab.collective import LaggedPropagation
    class FixedPredictors(LaggedPropagation):
        def _train(self,t,regions):pass
        @staticmethod
        def _predict(model,x):return np.array([0.])
    model=FixedPredictors(AlgorithmSettings(window_s=2,noise_velocity=.001))
    model.models={(None,1):(0.,.02,'own'),(0,1):(0.,.3,'augmented')}
    for i in range(16):result=model.push(i*.05,[[0.],[i*.05]])
    region=result['regions']['1']
    target=region['support'][0]
    assert target['own_history_available_samples']>target['augmented_available_samples']
    assert target['evaluation_samples']==target['augmented_available_samples']
    assert target['own_history_error']==pytest.approx(target['augmented_error'])
    assert target['improvement']==pytest.approx(0.)


def test_observed_support_keeps_real_modes_without_inventing_occluded_coordinates():
    model = CausalSubspace(AlgorithmSettings(components=1, noise_velocity=.001, collective_support="observed"))
    for i in range(30):
        result = model.push(i/30, [np.sin(i/5), 2*np.sin(i/5), np.nan, np.nan], ["a.x", "a.y", "b.x", "b.y"])
    assert result["state"] == "observed"
    assert result["support"] == ["a.x", "a.y"]
    assert result["excluded_support"] == ["b.x", "b.y"]
    assert np.array(result["basis"]).shape == (2, 1)
    assert result["history_end_s"] < 29/30
    assert np.isfinite(result["amplitudes"]).all()
    assert len(model.history) == 30
    # Returning coordinates cannot acquire a fitted mode from invented history.
    result = model.push(1., [0., 0., 5., 6.], ["a.x", "a.y", "b.x", "b.y"])
    assert result["support"] == ["a.x", "a.y"]
    assert model.push(1.1, [np.nan]*4, ["a.x", "a.y", "b.x", "b.y"])["state"] == "missing"
    assert not model.history


def test_observed_support_does_not_join_alternating_nonoverlapping_observations():
    model = CausalSubspace(AlgorithmSettings(collective_support="observed"))
    for i in range(20):
        vector = [i, i, np.nan, np.nan] if i%2 else [np.nan, np.nan, i, i]
        result = model.push(i/30, vector, ["a.x", "a.y", "b.x", "b.y"])
    assert result["state"] == "missing"
    assert result["reason"] == "insufficient common observed collective support"
    assert result["support"] == []
