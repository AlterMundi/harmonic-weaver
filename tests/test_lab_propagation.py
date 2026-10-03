import numpy as np

from harmonic_weaver.lab.collective import LaggedPropagation
from harmonic_weaver.lab.contracts import AlgorithmSettings


def test_delayed_support_uses_only_past_and_improves_over_own_history():
    settings = AlgorithmSettings(lag_s=.1, window_s=4., propagation_interval_s=.2)
    model = LaggedPropagation(settings)
    rng = np.random.default_rng(23)
    source = rng.normal(size=(150,2))
    for i in range(150):
        target = source[i-2] if i >= 2 else np.zeros(2)
        result = model.push(round(i*.05,8), np.stack([source[i],target]))
        if i:
            assert result['history_end_s'] < round(i*.05,8)
    assert result['state'] == 'observed'
    region = result['regions']['1']
    assert region['score'] > .8
    assert region['support'][0]['lag_s'] == .1
    assert region['support'][0]['augmented_error'] < region['support'][0]['own_history_error']*.2
    # No forced winner, and an unsupported reverse direction stays weak.
    assert result['regions']['2']['score'] < .3
    result = model.push(9., np.zeros((2,2)))
    assert result['state'] == 'missing'
    assert result['history_end_s'] is None


def test_missing_support_resets_training_and_zero_motion_does_not_invent_centers():
    model = LaggedPropagation(AlgorithmSettings())
    for i in range(60):
        result = model.push(i/30, np.zeros((2,2)))
    assert all(r['score'] == 0 for r in result['regions'].values())
    result = model.push(2., np.array([[np.nan,0.],[0.,0.]]))
    assert result['state'] == 'missing'
    assert not model.history and not model.models


def test_regional_shape_changes_reset_models_and_warm_a_new_history():
    model=LaggedPropagation(AlgorithmSettings(window_s=4))
    rng=np.random.default_rng(31)
    for i in range(40):model.push(i/30,rng.normal(size=(2,2)))
    assert model.models and model.errors
    for shape in ((3,2),(3,1)):
        t=model.history[-1][0]+1/30
        result=model.push(t,rng.normal(size=shape))
        assert result['state']=='missing' and result['history_end_s'] is None
        assert len(model.history)==1 and not model.models and not model.errors
    result=model.push(float('nan'),np.zeros((3,1)))
    assert result['reason']=='missing regional support' and not model.history
    result=model.push(3.,np.empty((0,2)))
    assert result['state']=='missing' and not model.history
