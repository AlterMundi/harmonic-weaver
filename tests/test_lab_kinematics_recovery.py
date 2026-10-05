"""Prediction must not treat reacquisition as observed displacement."""
import numpy as np
import pytest

from harmonic_weaver.lab.contracts import AlgorithmSettings, Joint
from harmonic_weaver.lab.kinematics import Kinematics
from test_lab_models import observation


@pytest.mark.parametrize('loss', ['missing', 'held', 'omitted'])
def test_prediction_waits_for_post_loss_history_per_joint(loss):
    k = Kinematics(AlgorithmSettings(), .2)
    for i in range(20):
        k.push(i/30, observation(i/30, i).persons[0])
    person = observation(20/30, 20).persons[0]
    if loss == 'omitted':
        person.joints = [q for q in person.joints if q.index != 11]
    else:
        person.joints[11] = Joint(index=11, state=loss, position=None if loss == 'missing' else [9.,9.])
    k.push(20/30, person)
    for i in range(21, 26):
        person = observation(i/30, i).persons[0]
        person.joints[11].position[0] += 2.
        result = k.push(i/30, person)
        assert np.isnan(result['position_error'][11])
        assert np.isnan(result['velocity_error'][11])
        assert np.isfinite(result['velocity_error'][12])  # unaffected joint keeps its history
    for i in range(26, 33):
        person = observation(i/30, i).persons[0]
        person.joints[11].position[0] += 2.
        result = k.push(i/30, person)
    assert np.isfinite(result['velocity_error'][11])
    assert result['velocity_error'][11] < .2  # fresh history, no 10-torso-length reacquisition error


@pytest.mark.parametrize('timestamp', [.1, 4.])
def test_seek_and_long_gap_invalidate_all_prediction_history(timestamp):
    k = Kinematics(AlgorithmSettings(), .2)
    for i in range(20):
        k.push(i/30, observation(i/30, i).persons[0])
    result = k.push(timestamp, observation(timestamp, 21).persons[0])
    assert np.isnan(result['position_error']).all()
    assert np.isnan(result['velocity_error']).all()


def test_local_prediction_route_does_not_activate_from_reacquired_hip():
    from harmonic_weaver.lab.models import MotionModel
    from harmonic_weaver.lab.presets import initial_presets
    from harmonic_weaver.lab.routing import PreparedRoutes
    preset = next(p for p in initial_presets() if p.id == 'lab-v3-descriptor-local')
    model, routes = MotionModel(preset, .2), PreparedRoutes(preset)
    for i in range(20):
        features = model.observe(observation(i/30, i), 'one', i/30)
        routes.evaluate(features, i/30)
    lost = observation(20/30, 20)
    lost.persons[0].joints[11] = Joint(index=11, state='missing')
    routes.evaluate(model.observe(lost, 'one', 20/30), 20/30)
    found = observation(21/30, 21)
    found.persons[0].joints[11].position[0] += 2.
    features = model.observe(found, 'one', 21/30)
    targets, diagnostic = routes.evaluate(features, 21/30)
    assert features.signals['zone.1.velocity_error'].state == 'missing'
    assert 1 in diagnostic['invalid_voices']
    assert not any(t.id == 1 and t.gain > 0 for t in targets)
    assert any(t.id != 1 and t.gain > 0 for t in targets)
