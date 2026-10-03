import copy,json
import numpy as np
import pytest
from pydantic import ValidationError
from harmonic_weaver.lab.research.heldout import Request,calculate,synthetic
from harmonic_weaver.lab.research.heldout_run import run,verify
from harmonic_weaver.lab.cache import atomic_json,sha256_file


def test_train_only_models_forecasts_fair_support_and_frozen_targets():
    raw=synthetic().model_dump();a=calculate(raw)
    changed=copy.deepcopy(raw);changed['sequences'][1]['observations'][-1]['values']=[1000.,-1000.]
    b=calculate(changed)
    assert a['models']==b['models']
    assert a['rows'][:-1]==b['rows'][:-1]
    assert a['rows'][-1]['predictions']==b['rows'][-1]['predictions']
    assert a['rows'][-1]['mse']!=b['rows'][-1]['mse']
    stats=a['results'][0]
    assert stats['common_count']==178 and stats['mean_mse']['full_ridge']<stats['mean_mse']['persistence']
    for row in a['rows']:
        assert row['target_s']>row['origin_s']>=row['history_start_s']
        assert set(row['mse'])=={'full_ridge','subspace_ridge','training_mean','persistence'}
        np.testing.assert_allclose(row['predictions']['full_ridge'],row['predictions']['subspace_ridge'],atol=1e-12)


def test_adaptation_prefix_excluded_model_frozen_and_gaps_split_forecasts():
    raw=synthetic().model_dump();raw['settings']['adaptation_prefix_samples']=30
    a=calculate(raw);prefix_end=raw['sequences'][1]['observations'][29]['time_s']
    assert all(r['origin_s']>prefix_end for r in a['rows'])
    assert len(a['models'])==2
    changed=copy.deepcopy(raw);changed['sequences'][1]['observations'][-1]['values']=[500.,500.]
    assert calculate(changed)['models']==a['models']
    raw['sequences'][1]['observations'][90].update(values=None,cause='tracking_lost')
    result=calculate(raw);gap=raw['sequences'][1]['observations'][90]['time_s']
    assert result['results'][0]['contiguous_segments']==2
    assert not any(r['history_start_s']<gap<r['target_s'] for r in result['rows'])
    raw['settings']['adaptation_prefix_samples']=180
    with pytest.raises(ValueError,match='leaves no test'):calculate(raw)


@pytest.mark.parametrize('reservation',['take','subject','task','within_take'])
def test_reservations_overlap_and_embargo_rejected(reservation):
    raw=synthetic().model_dump();raw['reservation']=reservation
    raw['sequences'][1]['recording_id']='train'
    if reservation=='subject':raw['sequences'][1]['subject_group']='train'
    if reservation=='task':raw['sequences'][1]['task_id']='oscillation'
    with pytest.raises(ValidationError):Request.model_validate(raw)
    if reservation=='within_take':
        for row in raw['sequences'][1]['observations']:row['time_s']+=7.
        Request.model_validate(raw)


def test_manifest_repeatability_exact_recompute_and_corruption(tmp_path):
    request=synthetic();run(request,tmp_path/'a');run(request,tmp_path/'b')
    for name in ('request.json','result.json','predictions.jsonl'):
        assert sha256_file(tmp_path/'a'/name)==sha256_file(tmp_path/'b'/name)
    assert verify(tmp_path/'a',recompute=True)['read_verification']=='recomputed'
    result=json.loads((tmp_path/'a/result.json').read_text());result['models']['frozen']['mean'][0]=10.
    atomic_json(tmp_path/'a/result.json',result)
    manifest=json.loads((tmp_path/'a/manifest.json').read_text());manifest['hashes']['result.json']=sha256_file(tmp_path/'a/result.json');atomic_json(tmp_path/'a/manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(tmp_path/'a',recompute=True)


def test_owned_worker_restart_cancel_and_evaluation_snapshot(tmp_path):
    from harmonic_weaver.lab.research.heldout_service import HeldoutService
    from test_lab_video_export import prepared
    evaluation,ident=prepared(tmp_path)
    service=HeldoutService(tmp_path/'data')
    selection={'evaluation_id':ident,'run_index':0,'signal_ids':['global.speed','zone.1.gain'],
               'start_s':.2,'end_s':2.}
    manifest=evaluation.report(ident)['manifest'];catalog=manifest['runs'][0]['signals']
    # Choose actual same-unit signal inventory instead of manufacturing a body schema.
    units={}
    for key,value in catalog.items():units.setdefault(value['unit'],[]).append(key)
    selection['signal_ids']=next(ids[:2] for ids in units.values() if len(ids)>=2)
    document=service.freeze(evaluation,{'selection':selection,'id':'body','role':'test','subject_group':'declared-fixture-person','task_id':'fixture'})
    assert document['provider']=='evaluation_features'
    assert document['recording_id']==manifest['source_records'][0]['cache_manifest']['media_sha256']
    assert document['provenance']['source']['person_id']=='one'
    job=service.start(synthetic());service.processes[job['id']].wait(timeout=20)
    assert service.list()[0]['status']=='complete'
    restored=HeldoutService(tmp_path/'data');assert restored.list()[0]['read_verification']=='integrity_only'
    assert restored.artifact(job['id'],'predictions.jsonl').is_file()
    repeat=restored.repeat(job['id']);restored.processes[repeat['id']].wait(timeout=20)
    assert sha256_file(restored.artifact(repeat['id'],'result.json'))==sha256_file(restored.artifact(job['id'],'result.json'))
    active=restored.start(synthetic());status=restored.cancel(active['id'])
    assert status['status'] in ('cancelled','complete')
    assert restored.processes[active['id']].poll() is not None
    restored.close();service.close()


def test_prefix_only_and_shuffled_training_keep_frozen_baselines_and_shared_targets():
    raw=synthetic().model_dump();raw['settings'].update(adaptation_prefix_samples=30,adaptation_mode='prefix_only',shuffle_training_targets=True,shuffle_seed=7)
    result=calculate(raw)
    assert result['models']['reserved']['training_sequences']==['reserved:prefix']
    assert result['models']['training_shuffle']['training_targets_shuffled'] is True
    assert result['models']['training_shuffle']['mean']==result['models']['frozen']['mean']
    assert len(result['results'][0]['mean_mse'])==9
    baseline=copy.deepcopy(raw);baseline['settings']['adaptation_prefix_samples']=0;baseline['settings']['shuffle_training_targets']=False
    indexed={r['target_s']:r for r in calculate(baseline)['rows']}
    for row in result['rows']:
        for key in ('persistence','training_mean','full_ridge','subspace_ridge'):
            assert row['predictions'][key]==indexed[row['target_s']]['predictions'][key]
        assert len(row['mse'])==9
    changed=copy.deepcopy(raw);changed['sequences'][1]['observations'][-1]['values']=[500.,500.]
    assert calculate(changed)['models']==result['models']


def test_no_forecast_support_and_historical_defaults_do_not_rewrite_frozen_input(tmp_path):
    from harmonic_weaver.lab.evaluation.runner import digest
    raw=synthetic().model_dump();raw['settings']['horizon_steps']=5
    raw['sequences'][1]['observations']=raw['sequences'][1]['observations'][:3]
    result=calculate(raw)
    assert result['results'][0]['common_count']==0 and result['rows']==[]
    assert all(value is None for value in result['results'][0]['mean_mse'].values())
    run(raw,tmp_path/'historical')
    request=json.loads((tmp_path/'historical/request.json').read_text())
    request['settings'].pop('shuffle_training_targets')
    atomic_json(tmp_path/'historical/request.json',request)
    recorded=json.loads((tmp_path/'historical/result.json').read_text());recorded['request_sha256']=digest(request)
    atomic_json(tmp_path/'historical/result.json',recorded)
    manifest=json.loads((tmp_path/'historical/manifest.json').read_text());manifest['request_sha256']=digest(request);manifest['settings']=request['settings'];manifest['environment']['python']='historic'
    manifest['hashes'].update({name:sha256_file(tmp_path/'historical'/name) for name in ('request.json','result.json')})
    atomic_json(tmp_path/'historical/manifest.json',manifest)
    report=verify(tmp_path/'historical')
    assert report['read_verification']=='integrity_only' and not report['code_matches_current']
    assert 'shuffle_training_targets' not in json.loads((tmp_path/'historical/request.json').read_text())['settings']
    with pytest.raises(ValueError,match='implementation/environment'):verify(tmp_path/'historical',recompute=True)


def test_completed_run_cannot_be_overwritten(tmp_path):
    run(synthetic(),tmp_path/'run')
    before=sha256_file(tmp_path/'run/manifest.json')
    with pytest.raises(ValueError,match='choose a new folder'):run(synthetic(),tmp_path/'run')
    assert sha256_file(tmp_path/'run/manifest.json')==before
