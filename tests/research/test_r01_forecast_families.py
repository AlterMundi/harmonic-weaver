import numpy as np
import pytest

from harmonic_weaver.lab.research.forecast_families import linear_trend, lagged_ridge
from harmonic_weaver.lab.research.grassmann import Settings, generate, evaluate, predict, run, pair_controls

METHODS=['persistence','full_ridge','subspace_ridge','linear_trend','lagged_full_ridge','lagged_subspace_ridge']


def test_linear_trend_extrapolates_vector_drift():
    x=np.arange(20.)[:,None]*np.array([[2.,-3.]])+np.array([[4.,7.]])
    np.testing.assert_allclose(linear_trend(x,5),[52.,-65.],atol=1e-12)


def test_lag_one_matches_existing_direct_ridge():
    past=np.random.default_rng(5).normal(size=(30,5))
    basis=np.linalg.qr(np.random.default_rng(7).normal(size=(5,2)))[0]
    for h in (1,4):
        np.testing.assert_allclose(lagged_ridge(past,basis,.1,h,1),predict(past,basis,.1,h),atol=1e-12)


def test_all_families_are_rotation_equivariant_and_frozen_at_origin():
    settings=Settings(samples=90,dimensions=5,signal_rank=2,components=2,predictors=METHODS,horizon_steps=4)
    t,controls=generate(settings)
    original=evaluate(settings,t,controls['original']);rotated=evaluate(settings,t,controls['global_rotation'])
    assert set(original['metrics']['mean_prediction_mse'])==set(METHODS)
    for key,error in original['metrics']['mean_prediction_mse'].items():
        np.testing.assert_allclose(error,rotated['metrics']['mean_prediction_mse'][key],atol=1e-11,rtol=1e-8)
    changed=controls['original'].copy();changed[60:]*=100
    perturbed=evaluate(settings,t,changed)
    assert original['rows'][:60]==perturbed['rows'][:60]
    # A forecast whose target is changed retains every committed prediction.
    a=original['rows'][60];b=perturbed['rows'][60]
    assert a['prediction_origin_s']<t[60] and a['predictions']==b['predictions']
    assert a['prediction_mse']!=b['prediction_mse']
    assert a['prediction_fit_support']['lagged_full_ridge']['training_pairs']==a['prediction_training_pairs']


def test_persistence_only_does_not_require_unused_lag_training():
    settings=Settings(samples=60,dimensions=4,signal_rank=2,components=2,predictors=['persistence'],horizon_steps=10,autoregressive_lags=12)
    t,controls=generate(settings)
    result=evaluate(settings,t,controls['original'])
    first=next(row for row in result['rows'] if 'predictions' in row)
    assert first['prediction_fit_support']['persistence']=={'past_observations':1,'training_pairs':0}


def test_repeatable_artifacts_and_common_support_include_selected_families(tmp_path):
    settings=Settings(samples=60,dimensions=4,signal_rank=2,components=2,predictors=METHODS)
    a=run(settings.model_dump(),tmp_path/'a');b=run(settings.model_dump(),tmp_path/'b')
    assert a['paired']==b['paired'] and a['results']==b['results']
    assert (tmp_path/'a'/'paired.jsonl').read_bytes()==(tmp_path/'b'/'paired.jsonl').read_bytes()
    assert set(a['paired']['results']['original']['mean_prediction_mse'])==set(METHODS)


def test_mismatched_methods_and_invalid_selection_rejected():
    with pytest.raises(ValueError):Settings(predictors=[])
    with pytest.raises(ValueError):Settings(predictors=['persistence','persistence'])
    with pytest.raises(ValueError):Settings(predictors=['unknown'])
    row={'time_s':0.,'prediction_mse':{'persistence':1.},'reconstruction_residual':0.}
    with pytest.raises(ValueError,match='same predictor'):
        pair_controls({'a':{'rows':[row]},'b':{'rows':[{**row,'prediction_mse':{'linear_trend':1.}}]}})


def test_frozen_body_features_share_families_and_reset_at_gaps(tmp_path):
    from test_lab_research_body import frozen,document
    from harmonic_weaver.lab.research.body import run as body_run
    request=frozen(tmp_path/'body',document()).model_copy(update={'predictors':METHODS,'autoregressive_lags':2})
    report=body_run(request.model_dump(),tmp_path/'body')
    assert set(report['paired']['results']['original']['mean_prediction_mse'])==set(METHODS)
    import json
    rows=[json.loads(line) for line in (tmp_path/'body'/'original.jsonl').read_text().splitlines()]
    forecasts=[row for row in rows if 'predictions' in row]
    assert forecasts and all(set(row['predictions'])==set(METHODS) for row in forecasts)
    assert all(row['prediction_origin_s']>=48/30 for row in forecasts if row['segment_index']==1)
