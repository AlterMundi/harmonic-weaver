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
