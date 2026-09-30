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
