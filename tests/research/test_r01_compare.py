import json
import numpy as np
import pytest
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.grassmann import Settings, run
from harmonic_weaver.lab.research.grassmann_compare import ComparisonRequest
from harmonic_weaver.lab.research.service import ResearchService


def runs(tmp_path, **change):
    service=ResearchService(tmp_path)
    ids=['a'*32,'b'*32]
    first=Settings(samples=100,dimensions=4,signal_rank=2,components=2,noise_threshold=.0001).model_dump()
    for ident,settings in zip(ids,[first,{**first,**change}]):
        folder=service.root/ident
        report=run(settings,folder)
        atomic_json(folder/'request.json',report['settings'])
    return service,ids


def test_windows_use_shared_targets_and_archived_errors_without_writes(tmp_path):
    service,ids=runs(tmp_path,window_s=.5)
    before={str(p):sha256_file(p) for p in service.root.rglob('*') if p.is_file()}
    report=service.compare({'run_ids':ids})
    control=report['controls'][0]
    assert control['common_count']>0
    a,b=control['conditions']
    assert a['mean_mse']['persistence']==b['mean_mse']['persistence']
    assert b['mean_delta_mse_vs_first']['persistence']==0
    rows=list(map(json.loads,(service.root/ids[0]/'original.jsonl').read_text().splitlines()))
    support={tuple(v) for v in control['support']}
    expected=np.mean([row['prediction_mse']['full_ridge'] for row in rows
        if 'prediction_mse' in row and (0,row['time_s'],row['prediction_origin_s']) in support])
    assert a['mean_mse']['full_ridge']==pytest.approx(expected)
    assert service.compare({'run_ids':ids})==report
    assert {str(p):sha256_file(p) for p in service.root.rglob('*') if p.is_file()}==before


def test_horizons_explicitly_distinguish_targets_from_origin_target_pairs(tmp_path):
    service,ids=runs(tmp_path,horizon_steps=6)
    paired=service.compare({'run_ids':ids})
    assert all(c['common_count']==0 for c in paired['controls'])
    assert all(v is None for c in paired['controls'] for condition in c['conditions'] for v in condition['mean_mse'].values())
    targets=service.compare({'run_ids':ids,'support':'target'})
    assert targets['support_columns']==['segment_index','target_s']
    assert all(c['common_count']>0 for c in targets['controls'])
    a,b=targets['controls'][0]['conditions']
    assert a['origins_s']!=b['origins_s']
    assert all(x<y[1] for x,y in zip(b['origins_s'],targets['controls'][0]['support']))


@pytest.mark.parametrize('change',[{'seed':1},{'control_hz':60},{'noise_std':.05}])
def test_different_frozen_inputs_or_clock_are_rejected(tmp_path,change):
    service,ids=runs(tmp_path,**change)
    with pytest.raises(ValueError,match='same frozen R01'):service.compare({'run_ids':ids})


def test_no_common_method_has_no_scores_and_changed_trace_rejected(tmp_path):
    service,ids=runs(tmp_path,predictors=['linear_trend'])
    # First run has default predictors, no linear_trend.
    report=service.compare({'run_ids':ids})
    assert all(c['methods']==[] for c in report['controls'])
    assert all(condition['mean_mse']=={} for c in report['controls'] for condition in c['conditions'])
    with (service.root/ids[0]/'original.jsonl').open('a') as stream:stream.write('{}\n')
    with pytest.raises(ValueError,match='artifact changed'):service.compare({'run_ids':ids})


@pytest.mark.parametrize('ids', [['a'*32],['a'*32,'a'*32],['../escape','a'*32]])
def test_comparison_ids_fail_closed(ids):
    with pytest.raises(ValueError):ComparisonRequest(run_ids=ids)


def test_body_frozen_input_and_segment_support(tmp_path):
    from test_lab_research_body import document,frozen
    from harmonic_weaver.lab.research.body import run as body_run
    service=ResearchService(tmp_path);ids=['a'*32,'b'*32]
    for ident,horizon in zip(ids,[1,6]):
        folder=service.root/ident
        request=frozen(folder,document());request.horizon_steps=horizon
        atomic_json(folder/'request.json',request.model_dump())
        body_run(request.model_dump(),folder)
    result=service.compare({'run_ids':ids,'support':'target'})
    assert result['input_identity']['kind']=='evaluation_features'
    assert {key[0] for key in result['controls'][0]['support']}=={0,1}
    with (service.root/ids[0]/'input.json').open('a') as stream:stream.write(' ')
    with pytest.raises(ValueError,match='artifact changed'):service.compare({'run_ids':ids,'support':'target'})


def test_comparison_http_read_only_and_error(tmp_path):
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    service,ids=runs(tmp_path,horizon_steps=6)
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post('/api/research/r01/compare',json={'run_ids':ids,'support':'target'})
        assert response.status_code==200 and response.json()['controls'][0]['common_count']>0
        assert client.post('/api/research/r01/compare',json={'run_ids':['../escape',ids[0]]}).status_code==422


def test_historical_defaults_accepted_but_missing_origin_not_invented(tmp_path):
    service,ids=runs(tmp_path)
    folder=service.root/ids[0]
    manifest=json.loads((folder/'manifest.json').read_text())
    del manifest['settings']['predictors']
    atomic_json(folder/'manifest.json',manifest)
    atomic_json(folder/'request.json',manifest['settings'])
    assert service.compare({'run_ids':ids})['controls'][0]['common_count']>0
    path=folder/'original.jsonl'
    rows=list(map(json.loads,path.read_text().splitlines()))
    for row in rows:row.pop('prediction_origin_s',None)
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    manifest['artifact_hashes']['original.jsonl']=sha256_file(path)
    atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='no archived forecast origin'):
        service.compare({'run_ids':ids,'support':'target'})
