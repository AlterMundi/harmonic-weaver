import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest

from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.body import BodyRequest,run,snapshot
from harmonic_weaver.lab.research.service import ResearchService


def document(gap=True):
    rows=[]
    for index in range(120):
        stamp=index/30
        rows.append({'time_s':stamp,'values':None if gap and 45<=index<48 else
            [np.sin(stamp*3),np.cos(stamp*2)],'invalid_signals':{}})
    return {'signal_ids':['a','b'],'unit':'T/s','rows':rows,'provenance':{'fixture':'synthetic'},'duplicate_control_holds_excluded':0}


def frozen(tmp_path,doc):
    tmp_path.mkdir(parents=True)
    atomic_json(tmp_path/'input.json',doc)
    request=BodyRequest(evaluation_id='a'*32,run_index=0,signal_ids=['a','b'],start_s=0,end_s=4,components=1,
        noise_threshold=.0001,horizon_steps=6,input_sha256=sha256_file(tmp_path/'input.json'))
    atomic_json(tmp_path/'request.json',request.model_dump())
    return request


def test_body_gap_resets_forecasts_repeats_and_input_hashes(tmp_path):
    a=frozen(tmp_path/'a',document());b=frozen(tmp_path/'b',document())
    first=run(a.model_dump(),tmp_path/'a');second=run(b.model_dump(),tmp_path/'b')
    assert first['contiguous_segments']==2 and first['invalid_observations']==3
    assert first['paired']['common_samples']>0
    assert first['artifact_hashes']==second['artifact_hashes']
    rows=list(map(json.loads,(tmp_path/'a'/'original.jsonl').read_text().splitlines()))
    for row in rows:
        if 'prediction_origin_s' in row and row['segment_index']==1:
            assert row['prediction_origin_s']>=48/30
            assert row['prediction_fit_end_s']<=row['prediction_origin_s']
            np.testing.assert_allclose(row['horizon_elapsed_s'],.2,atol=1e-12)
    (tmp_path/'b'/'input.json').write_text('{}')
    with pytest.raises(ValueError,match='changed'):run(b.model_dump(),tmp_path/'b')
    with pytest.raises(ValueError,match='already'):run(a.model_dump(),tmp_path/'a')


def test_missing_support_produces_empty_scores_and_irregular_horizon_is_measured(tmp_path):
    doc=document(False)
    for row in doc['rows']:row['time_s']*=1.1
    request=frozen(tmp_path/'irregular',doc)
    report=run(request.model_dump(),tmp_path/'irregular')
    rows=list(map(json.loads,(tmp_path/'irregular'/'original.jsonl').read_text().splitlines()))
    scored=[row for row in rows if 'prediction_mse' in row]
    assert scored
    np.testing.assert_allclose(scored[0]['horizon_elapsed_s'],.22,atol=1e-12)
    for row in doc['rows']:row['values']=None
    request=frozen(tmp_path/'missing',doc)
    report=run(request.model_dump(),tmp_path/'missing')
    assert report['invalid_observations']==120 and report['paired']['common_samples']==0
    assert report['results']['original']['mean_prediction_mse']=={}


def test_snapshot_verified_replay_deduplicates_and_rejects_mixed_units(tmp_path):
    from test_lab_evaluation import source_fixture
    from harmonic_weaver.lab.evaluation.runner import Request,run as evaluate
    from harmonic_weaver.lab.evaluation.service import EvaluationService
    from harmonic_weaver.lab.presets import initial_presets
    from harmonic_weaver.lab.routing import PreparedRoutes
    from harmonic_weaver.lab.store import SessionStore
    source,_,_=source_fixture(tmp_path)
    preset=next(p for p in initial_presets() if p.algorithm.id=='local')
    request=Request(presets=[preset],sources=[source])
    ident=uuid4().hex;root=tmp_path/'session';folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    atomic_json(folder/'request.json',request.model_dump())
    evaluate(request,folder/'result')
    store=SessionStore(root,prepare=PreparedRoutes);evaluation=EvaluationService(root,store,None)
    body=BodyRequest(evaluation_id=ident,run_index=0,signal_ids=['zone.1.speed','zone.2.speed'],start_s=.2,end_s=2,components=1)
    research=ResearchService(root)
    try:
        data=snapshot(evaluation,body)
        assert data['duplicate_control_holds_excluded']>0
        assert data['unit']=='T/s'
        observed=[r for r in data['rows'] if r['values'] is not None]
        assert len({r['time_s'] for r in observed})==len(observed)
        assert data['provenance']['source']['person_id']=='one'
        with pytest.raises(ValueError,match='same unit'):
            snapshot(evaluation,body.model_copy(update={'signal_ids':['zone.1.speed','zone.1.acceleration']}))
        with pytest.raises(ValueError,match='within'):
            snapshot(evaluation,body.model_copy(update={'start_s':0}))
        job=research.start_body(body.model_dump(),evaluation)
        assert research.processes[job['id']].wait(timeout=20)==0
        restored=ResearchService(root)
        result=next(j for j in restored.list() if j['id']==job['id'])
        assert result['status']=='complete' and result['input_kind']=='evaluation_features'
        assert restored.artifact(job['id'],'input.json').is_file()
        frozen_request=json.loads(restored.artifact(job['id'],'request.json').read_text())
        assert frozen_request['input_sha256']==sha256_file(restored.artifact(job['id'],'input.json'))
        from fastapi.testclient import TestClient
        from harmonic_weaver.lab.app import create_app
        import time
        class Runtime:
            library=None
            def start(self):pass
            def close(self):pass
        with TestClient(create_app(root,store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
            response=client.post('/api/research/r01/trace',json=body.model_dump())
            assert response.status_code==200,response.text
            ident=response.json()['id'];deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                result=next(j for j in client.get('/api/research/r01').json() if j['id']==ident)
                if result['status']!='running':break
                time.sleep(.05)
            assert result['status']=='complete'
            assert client.get(f'/api/research/r01/{ident}/artifacts/input.json').status_code==200
            assert client.post('/api/research/r01/trace',json={**body.model_dump(),'components':3}).status_code==422
        (folder/'result'/'source-00-preset-00.jsonl').write_text('changed')
        with pytest.raises(ValueError,match='cambió'):snapshot(evaluation,body)
    finally:research.close();evaluation.close();store.close()


def test_snapshot_rejects_lookahead_and_person_substitution(tmp_path):
    path=tmp_path/'trace.jsonl'
    request=BodyRequest(evaluation_id='a'*32,run_index=0,signal_ids=['a','b'],start_s=0,end_s=1)
    class Evaluation:
        def report(self,ident):return {'manifest':{'runs':[{'file':'trace.jsonl','sha256':sha256_file(path),'signals':{'a':{'unit':'T/s'},'b':{'unit':'T/s'}},'source_index':0,'preset_sha256':'fixture'}],
            'request':{'sources':[{'start_s':0,'end_s':1,'person_id':'one'}]},'request_sha256':'fixture','code':{},'source_records':[{}]}}
        def artifact(self,ident,name):return path
    frame={'source_time_s':0,'person_id':'one','lookahead_s':.1,'signals':{'a':{'state':'observed','value':1,'unit':'T/s'},'b':{'state':'observed','value':2,'unit':'T/s'}}}
    path.write_text(json.dumps({'source_time_s':0,'features':frame})+'\n')
    with pytest.raises(ValueError,match='zero-lookahead'):snapshot(Evaluation(),request)
    frame.update(lookahead_s=0,person_id='other')
    path.write_text(json.dumps({'source_time_s':0,'features':frame})+'\n')
    with pytest.raises(ValueError,match='person'):snapshot(Evaluation(),request)
