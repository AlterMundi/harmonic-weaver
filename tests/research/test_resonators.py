import numpy as np
import pytest
from harmonic_weaver.lab.research.resonators import Resonators,Settings


def test_uncoupled_impulse_has_exact_declared_carriers_and_decay():
    settings=Settings(sample_rate=8000)
    inputs=np.zeros((1000,6));inputs[0]=1
    result=Resonators(settings).render(inputs)
    t=np.arange(1,1001)/8000
    expected=np.exp(-2*t[:,None])*np.sin(2*np.pi*40.4*t[:,None]*np.arange(1,7))
    np.testing.assert_allclose(result['voices'],expected,atol=1e-12)
    assert np.any(result['sum'][1:]!=0) # autonomous tail after single impulse
    assert np.all(np.diff(result['state_norm_squared'])<0)


def test_block_partition_preserves_phase_and_reset_silences_state():
    inputs=np.zeros((1000,6));inputs[0,0]=1;inputs[411,3]=.5
    whole=Resonators(Settings(sample_rate=8000,topology='ring',coupling_per_s=3)).render(inputs)
    split=Resonators(Settings(sample_rate=8000,topology='ring',coupling_per_s=3))
    a=split.render(inputs[:317]);b=split.render(inputs[317:])
    np.testing.assert_array_equal(np.concatenate([a['voices'],b['voices']]),whole['voices'])
    assert b['sample_index']==1000
    split.reset();zero=split.render(np.zeros((100,6)))
    assert zero['sample_index']==100 and not zero['voices'].any()


def test_coupled_free_evolution_does_not_create_internal_norm():
    model=Resonators(Settings(sample_rate=8000,topology='complete',coupling_per_s=30,damping_per_s=[0.]*6))
    inputs=np.zeros((1000,6));inputs[0,0]=1
    result=model.render(inputs)
    assert np.all(np.diff(result['state_norm_squared'])<=1e-14)
    assert result['state_norm_squared'][0]<=1+1e-14


@pytest.mark.parametrize('settings',[{'ratios':[1,2,3]}, {'damping_per_s':[-1]*6},
    {'fundamental_hz':400,'sample_rate':8000,'ratios':[1,2,3,4,5,10]},
    {'topology':'custom','adjacency':[[0]*6]*5}])
def test_invalid_resonator_contracts_rejected(settings):
    with pytest.raises(ValueError):Settings.model_validate(settings)
