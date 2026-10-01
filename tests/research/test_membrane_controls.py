import numpy as np
import pytest
from harmonic_weaver.lab.research.membrane_controls import Request,signals,compare


def test_control_repeat_doses_components_and_fixed_boundaries():
    request=Request(duration_samples=800,forcing_samples=400)
    inputs=signals(request)
    expected=sum(np.sin(2*np.pi*f*np.arange(400)/8000) for f in request.frequencies_hz)
    np.testing.assert_allclose(inputs['multisine'][:400],expected,rtol=1e-12,atol=1e-13)
    result=compare(request)
    assert result==compare(request)
    for name,row in result['conditions'].items():
        assert row['input_sum_squares']==np.dot(inputs[name],inputs[name])
        assert row['field']['rms'][0]==row['field']['rms'][-1]==0
        assert row['field']['sample_count']==800
    assert not np.array_equal(signals(request.model_copy(update={'seed':18}))['seeded_noise'],inputs['seeded_noise'])


def test_zero_control_and_block_partition():
    request=Request(duration_samples=800,forcing_samples=400,amplitude=0)
    assert all(not any(row['field']['rms']) for row in compare(request)['conditions'].values())
    a=compare(request.model_copy(update={'amplitude':1.}))
    b=compare(request.model_copy(update={'amplitude':1.,'block_size':317}))
    for name in a['conditions']:
        np.testing.assert_allclose(a['conditions'][name]['field']['rms'],b['conditions'][name]['field']['rms'],rtol=1e-12,atol=1e-18)


def test_bad_controls_rejected():
    for bad in ({'forcing_samples':9000},{'weights':[1.]},{'seed':True},{'frequencies_hz':[4000]*6}):
        with pytest.raises(ValueError):Request.model_validate(bad)
