"""Real evaluation -> verified replay reader -> HTTP freeze -> owned R03 worker."""
import json
import time
from uuid import uuid4
from fastapi.testclient import TestClient

from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.evaluation.runner import Request,run
from harmonic_weaver.lab.evaluation.service import EvaluationService
from harmonic_weaver.lab.presets import initial_presets
from harmonic_weaver.lab.research.candidate_input import candidate_snapshot
from harmonic_weaver.lab.research.coincidence import compare_frozen,content_hash
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.store import SessionStore
from test_lab_evaluation import source_fixture


def test_real_replay_http_freeze_repeats_exact_result_and_rejects_changed_input(tmp_path):
    source,_,_=source_fixture(tmp_path)
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident
    folder.mkdir(parents=True)
    preset=next(p for p in initial_presets() if p.algorithm.id=='local')
    request=Request(presets=[preset],sources=[source])
    atomic_json(folder/'request.json',request.model_dump())
    run(request,folder/'result')
    store=SessionStore(root,prepare=PreparedRoutes)
    evaluation=EvaluationService(root,store,None)
    candidate=dict(evaluation_id=ident,run_index=0,signal_id='zone.1.speed',start_s=.2,end_s=2,high=.1,low=.02)
    try:
        features=candidate_snapshot(evaluation,candidate)
        record=features['provenance']['source_record'];cache=record['cache_manifest']
        identity=dict(kind='video',cache_manifest_sha256=record['cache_manifest_sha256'],
                      generation=cache['generation'],cache_key=cache['key'],media_id=cache['media_sha256'])
        store.state.source_id='synthetic-live';store.state.person_id='one';store.state.position_s=.5
        store.mark('Synthetic marker, not human evidence',category='deployment',observed_epoch=2,transport_epoch=2,source_identity=identity)
        context=dict(source_id=store.state.source_id,person_id='one',session_id=store.state.session_id,
                     observed_epoch=2,category='deployment')
        marks=store.marks_snapshot(**context,through_sequence=store.marks_snapshot()['through_sequence'])
        expected=compare_frozen(marks,features,feature_sha256=content_hash(features),context=context,
                                mark_support=[[.2,2.0]],tolerance_s=.2,mark_offset_s=0)
        assert features['duplicate_control_holds_excluded']>0
        assert expected['comparison']['support_duration_s']>0
        class Runtime:
            library=None
            def start(self):pass
            def close(self):pass
        body=dict(candidate=candidate,**context,through_sequence=marks['through_sequence'],mark_support=[[.2,2]])
        results=[]
        with TestClient(create_app(root,store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
            for _ in range(2):
                response=client.post('/api/research/r03',json=body)
                assert response.status_code==200,response.text
                job=response.json()['id'];deadline=time.monotonic()+10
                while True:
                    report=next(j for j in client.get('/api/research/r03').json() if j['id']==job)
                    if report['status'] not in ('queued','running'):break
                    assert time.monotonic()<deadline
                    time.sleep(.02)
                assert report['status']=='complete',report
                response=client.get(f'/api/research/r03/{job}/artifacts/result.json')
                assert response.status_code==200 and response.json()==json.loads(json.dumps(expected))
                results.append(response.content)
                frozen=client.get(f'/api/research/r03/{job}/artifacts/features.json')
                assert frozen.json()==features
            assert results[0]==results[1]
            # Hash check belongs to the real reader; no worker should be launched.
            trace=folder/'result/source-00-preset-00.jsonl'
            trace.write_text('changed')
            response=client.post('/api/research/r03',json=body)
            assert response.status_code==422,response.text
            assert len(client.get('/api/research/r03').json())==2
    finally:evaluation.close();store.close()
