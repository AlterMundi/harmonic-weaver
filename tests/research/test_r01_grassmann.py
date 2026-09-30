import numpy as np
from harmonic_weaver.lab.research.grassmann import Settings, generate, evaluate, run


def test_global_rotation_preserves_error_and_common_support():
    settings=Settings(samples=120,dimensions=5,signal_rank=2,components=2)
    t,controls=generate(settings)
    first=evaluate(settings,t,controls['original']);rotated=evaluate(settings,t,controls['global_rotation'])
    assert first['metrics']['common_samples']>0
    assert first['metrics']['common_samples']==rotated['metrics']['common_samples']
    for key,value in first['metrics']['mean_prediction_mse'].items():
        np.testing.assert_allclose(value,rotated['metrics']['mean_prediction_mse'][key],rtol=1e-9,atol=1e-12)
    assert all(row['history_end_s']<row['time_s'] for row in first['rows'] if row['state']=='observed')


def test_future_suffix_cannot_change_earlier_estimates():
    settings=Settings(samples=120,dimensions=5,signal_rank=2,components=2)
    t,controls=generate(settings);data=controls['original']
    original=evaluate(settings,t,data);changed=data.copy();changed[80:]*=100
    perturbed=evaluate(settings,t,changed)
    assert original['rows'][:80]==perturbed['rows'][:80]


def test_repeated_bench_preserves_synthetic_inputs_and_metrics(tmp_path):
    settings=Settings(samples=60,dimensions=4,signal_rank=2,components=2)
    a=run(settings.model_dump(),tmp_path/'a');b=run(settings.model_dump(),tmp_path/'b')
    assert a['input_hashes']==b['input_hashes'] and a['results']==b['results']
    assert (tmp_path/'a'/'original.jsonl').read_bytes()==(tmp_path/'b'/'original.jsonl').read_bytes()


def test_low_reconstruction_error_is_not_perfect_temporal_prediction():
    settings=Settings(samples=120,dimensions=4,signal_rank=2,components=2,scenario='stochastic_span',temporal_memory=0,noise_std=0)
    t,controls=generate(settings);result=evaluate(settings,t,controls['original'])
    assert result['metrics']['mean_reconstruction_residual']<1e-10
    assert result['metrics']['mean_prediction_mse']['subspace_ridge']>1e-8


def test_research_worker_job_completes_with_frozen_request(tmp_path):
    import time
    from harmonic_weaver.lab.research.service import ResearchService
    service=ResearchService(tmp_path)
    job=service.start(Settings(samples=60,dimensions=4,signal_rank=2,components=2).model_dump())
    process=service.processes[job['id']]
    assert process.wait(timeout=20)==0
    restored=ResearchService(tmp_path)
    report=restored.list()[0]
    assert report['status']=='complete' and report['settings']['samples']==60
    assert (tmp_path/'research'/'r01'/job['id']/'request.json').exists()
    service.close();restored.close()


def test_completed_result_is_not_overwritten(tmp_path):
    import pytest
    settings=Settings(samples=60,dimensions=4,signal_rank=2,components=2)
    run(settings.model_dump(),tmp_path/'result')
    before=(tmp_path/'result'/'manifest.json').read_bytes()
    with pytest.raises(ValueError,match='already'):run(settings.model_dump(),tmp_path/'result')
    assert (tmp_path/'result'/'manifest.json').read_bytes()==before


def test_paired_controls_exclude_unequal_support_before_scoring():
    from harmonic_weaver.lab.research.grassmann import pair_controls
    def row(t,value):return {'time_s':t,'prediction_mse':dict(persistence=value,full_ridge=value,subspace_ridge=value),'reconstruction_residual':value}
    evaluations={'original':{'rows':[row(0,100),row(1,2),row(2,4)]},
                 'global_rotation':{'rows':[row(1,2),row(2,4),row(3,100)]},
                 'temporal_shuffle':{'rows':[row(2,6)]}}
    paired,traces=pair_controls(evaluations)
    assert paired['common_samples']==1 and [r['time_s'] for r in traces]==[2]
    assert paired['results']['original']['mean_prediction_mse']['persistence']==4
    assert paired['mean_mse_delta_vs_original']['global_rotation']['persistence']==0
    assert paired['mean_mse_delta_vs_original']['temporal_shuffle']['persistence']==2
    assert paired['excluded_by_control']['original']==2


def test_no_common_support_is_not_a_zero_error_score():
    from harmonic_weaver.lab.research.grassmann import pair_controls
    row={'time_s':1,'prediction_mse':{},'reconstruction_residual':0}
    paired,traces=pair_controls({'a':{'rows':[row]},'b':{'rows':[]}})
    assert paired['common_samples']==0 and not traces
    assert paired['results']['a']['mean_prediction_mse']=={}
    assert paired['results']['a']['mean_reconstruction_residual'] is None


def test_research_artifacts_restore_and_reject_changed_data(tmp_path):
    import json
    import pytest
    from harmonic_weaver.lab.research.service import ResearchService
    service=ResearchService(tmp_path)
    job=service.start(Settings(samples=60,dimensions=4,signal_rank=2,components=2).model_dump())
    assert service.processes[job['id']].wait(timeout=20)==0
    restored=ResearchService(tmp_path)
    assert restored.artifact(job['id'],'request.json').is_file()
    path=restored.artifact(job['id'],'paired.jsonl')
    assert restored.artifact(job['id'],'paired.jsonl')==path
    with pytest.raises(ValueError):restored.artifact(job['id'],'../worker.log')
    path.write_text('changed')
    with pytest.raises(ValueError,match='changed'):restored.artifact(job['id'],'paired.jsonl')
    request=restored.artifact(job['id'],'request.json');settings=json.loads(request.read_text());settings['seed']=99
    request.write_text(json.dumps(settings))
    with pytest.raises(ValueError,match='changed'):restored.artifact(job['id'],'request.json')
    assert restored.artifact(job['id'],'manifest.json').is_file()
    service.close();restored.close()


def test_research_download_api_ranges_and_corrupt_trace(tmp_path):
    import time
    from pathlib import Path
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        job=client.post('/api/research/r01',json=Settings(samples=60,dimensions=4,signal_rank=2,components=2).model_dump()).json()
        deadline=time.monotonic()+20;report=None
        while time.monotonic()<deadline:
            reports=client.get('/api/research/r01').json()
            report=next(j for j in reports if j['id']==job['id'])
            if report['status']!='running':break
            time.sleep(.05)
        assert report['status']=='complete',report
        url=f"/api/research/r01/{job['id']}/artifacts/paired.jsonl"
        response=client.get(url,headers={'Range':'bytes=0-9'})
        assert response.status_code==206 and len(response.content)==10
        assert client.get(f"/api/research/r01/{job['id']}/artifacts/request.json").json()['samples']==60
        assert client.get(f"/api/research/r01/{job['id']}/artifacts/worker.log").status_code==422
        (Path(job['directory'])/'paired.jsonl').write_text('changed')
        assert client.get(url).status_code==422


def test_cancel_owned_worker_preserves_partial_files_and_survives_restart(tmp_path):
    import json
    import subprocess
    import sys
    from uuid import uuid4
    import pytest
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.research.service import ResearchService
    service=ResearchService(tmp_path)
    ident=uuid4().hex;folder=service.root/ident;folder.mkdir()
    atomic_json(folder/'manifest.json',{'status':'running','line':'R01'})
    partial=folder/'original.jsonl';partial.write_text('partial diagnostic')
    process=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
    service.processes[ident]=process
    try:
        result=service.cancel(ident)
        assert process.poll() is not None and result['status']=='cancelled'
        assert partial.read_text()=='partial diagnostic'
        restored=ResearchService(tmp_path)
        assert restored.list()[0]['status']=='cancelled'
        assert service.cancel(ident)==result
        with pytest.raises(ValueError,match='not complete'):restored.artifact(ident,'original.jsonl')
        with pytest.raises(ValueError):service.cancel('../outside')
        service.close()
        assert json.loads((folder/'manifest.json').read_text())['status']=='cancelled'
    finally:
        if process.poll() is None:process.kill();process.wait()


def test_cancel_does_not_relabel_completed_or_unowned_results(tmp_path):
    from uuid import uuid4
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.research.service import ResearchService
    service=ResearchService(tmp_path)
    for status in ('complete','running'):
        ident=uuid4().hex;folder=service.root/ident;folder.mkdir()
        atomic_json(folder/'manifest.json',{'status':status,'line':'R01'})
        before=(folder/'manifest.json').read_bytes()
        result=service.cancel(ident)
        if status=='complete':
            assert result['status']=='complete'
            assert (folder/'manifest.json').read_bytes()==before
        else:assert result['status']=='interrupted'
    service.close()


def test_completion_during_cancel_wins_and_shutdown_is_interrupted(tmp_path):
    from uuid import uuid4
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.research.service import ResearchService
    service=ResearchService(tmp_path)
    ident=uuid4().hex;folder=service.root/ident;folder.mkdir()
    manifest=folder/'manifest.json';atomic_json(manifest,{'status':'running'})
    class CompletingWorker:
        done=False
        def poll(self):return 0 if self.done else None
        def terminate(self):
            atomic_json(manifest,{'status':'complete','result':'committed'})
            self.done=True
        def wait(self,timeout):return 0
    service.processes[ident]=CompletingWorker()
    assert service.cancel(ident)['result']=='committed'
    assert service.list()[0]['status']=='complete'
    # Closing a real live worker is an interruption, not a human cancellation.
    import subprocess
    import sys
    second=uuid4().hex;other=service.root/second;other.mkdir()
    atomic_json(other/'manifest.json',{'status':'running'})
    worker=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
    service.processes[second]=worker
    try:
        service.close()
        report=next(j for j in service.list() if j['id']==second)
        assert report['status']=='interrupted' and report['error']=='Service shutdown'
        assert worker.poll() is not None
    finally:
        if worker.poll() is None:worker.kill();worker.wait()


def test_long_horizon_forecasts_cannot_use_intervening_observations():
    settings=Settings(samples=120,dimensions=5,signal_rank=2,components=2,horizon_steps=12)
    t,controls=generate(settings);data=controls['original']
    first=evaluate(settings,t,data)
    changed=data.copy();changed[80:]+=np.arange(5)*.3
    second=evaluate(settings,t,changed)
    compared=0
    for a,b in zip(first['rows'],second['rows']):
        if a.get('prediction_origin_s',np.inf)<t[80] and 'predictions' in b:
            assert a['predictions']==b['predictions']
            assert a['prediction_fit_end_s']<=a['prediction_origin_s']
            np.testing.assert_allclose(a['time_s']-a['prediction_origin_s'],12/30,atol=1e-12)
            if a['time_s']>=t[80]:compared+=1
    assert compared>0  # Includes targets after the modified suffix begins.


def test_direct_horizon_fit_uses_lagged_pairs_and_last_available_anchor():
    from harmonic_weaver.lab.research.grassmann import predict
    past=np.arange(10,dtype=float)[:,None]
    result=predict(past,np.eye(1),1e-8,horizon_steps=3)
    np.testing.assert_allclose(result,[12],atol=1e-7)


def test_long_horizon_rotation_and_repetition_have_common_support(tmp_path):
    settings=Settings(samples=90,dimensions=5,signal_rank=2,components=2,horizon_steps=9)
    first=run(settings.model_dump(),tmp_path/'first')
    second=run(settings.model_dump(),tmp_path/'second')
    assert first['artifact_hashes']==second['artifact_hashes']
    assert first['paired']['common_samples']>0
    for key,value in first['paired']['results']['original']['mean_prediction_mse'].items():
        np.testing.assert_allclose(value,first['paired']['results']['global_rotation']['mean_prediction_mse'][key],rtol=1e-9,atol=1e-12)


def test_insufficient_horizon_history_is_explicit_not_nan_or_zero_score():
    settings=Settings(samples=60,dimensions=4,signal_rank=2,components=2,horizon_steps=30,window_s=.3)
    t,controls=generate(settings);result=evaluate(settings,t,controls['original'])
    assert result['metrics']['common_samples']==0
    assert result['metrics']['mean_prediction_mse']=={}
    assert any(row['prediction_reason']=='No valid forecast from the required past origin' for row in result['rows'])
    import pytest
    with pytest.raises(ValueError):Settings(horizon_steps=0)
    with pytest.raises(ValueError):Settings(horizon_steps=31)
