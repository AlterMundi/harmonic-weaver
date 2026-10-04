import copy
import numpy as np
import pytest

from harmonic_weaver.lab.research.heldout import Request, calculate, nonlinear_synthetic, quadratic_inputs, synthetic
from harmonic_weaver.lab.research.heldout_run import run, verify
from harmonic_weaver.lab.cache import sha256_file


def test_quadratic_control_recovers_known_nonlinearity_on_reserved_initial_condition():
    result=calculate(nonlinear_synthetic())
    scores=result['results'][0]['mean_mse']
    assert scores['quadratic_ridge']<1e-12
    assert scores['full_ridge']>.1
    model=result['models']['frozen']
    assert model['quadratic_features']['regressors']==2
    np.testing.assert_allclose(quadratic_inputs(np.array([2.,3.])),[2.,3.,4.,6.,9.])
    assert all(set(row['predictions'])==set(scores) for row in result['rows'])


@pytest.mark.parametrize('mode',['pooled_prefix','prefix_only'])
def test_quadratic_models_never_fit_future_test_targets_and_share_support(mode):
    raw=nonlinear_synthetic().model_dump()
    raw['settings'].update(adaptation_prefix_samples=30,adaptation_mode=mode,
                           shuffle_training_targets=True,shuffle_seed=7)
    raw['sequences'][1]['observations'][90].update(values=None,cause='declared_gap')
    first=calculate(raw)
    changed=copy.deepcopy(raw);changed['sequences'][1]['observations'][-1]['values']=[1000.]
    second=calculate(changed)
    assert first['models']==second['models']
    assert first['rows'][:-1]==second['rows'][:-1]
    assert first['rows'][-1]['predictions']==second['rows'][-1]['predictions']
    assert first['rows'][-1]['mse']!=second['rows'][-1]['mse']
    linear=copy.deepcopy(raw);linear['settings']['quadratic_control']=False
    baseline=calculate(linear)
    assert first['results'][0]['common_support_sha256']==baseline['results'][0]['common_support_sha256']
    for row,old in zip(first['rows'],baseline['rows']):
        assert row['origin_s']>raw['sequences'][1]['observations'][29]['time_s']
        assert not row['history_start_s']<3.<row['target_s']
        for key,value in old['predictions'].items(): assert row['predictions'][key]==value
        assert {'quadratic_ridge','adapted_quadratic_ridge','shuffled_quadratic_ridge'}<=row['predictions'].keys()


def test_quadratic_control_budget_and_empty_support():
    raw=synthetic().model_dump();raw['settings'].update(quadratic_control=True,history_steps=8)
    raw['feature_ids']=['a','b','c','d']
    for sequence in raw['sequences']:
        for row in sequence['observations']:row['values']*=2
    with pytest.raises(ValueError,match='324 regressors'):Request.model_validate(raw)
    raw=nonlinear_synthetic().model_dump();raw['settings']['horizon_steps']=5
    raw['sequences'][1]['observations']=raw['sequences'][1]['observations'][:3]
    result=calculate(raw)
    assert result['results'][0]['mean_mse']['quadratic_ridge'] is None
    assert result['rows']==[]


def test_quadratic_artifacts_repeat_and_recompute(tmp_path):
    for name in ('first','second'):run(nonlinear_synthetic(),tmp_path/name)
    for name in ('request.json','result.json','predictions.jsonl'):
        assert sha256_file(tmp_path/'first'/name)==sha256_file(tmp_path/'second'/name)
    assert verify(tmp_path/'first',recompute=True)['read_verification']=='recomputed'
