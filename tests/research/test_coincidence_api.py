"""HTTP freeze/worker/restore test; replay reader mocked, no bodily media/audio."""
import time
from copy import deepcopy
from fastapi.testclient import TestClient
from harmonic_weaver.lab import app as app_module
from harmonic_weaver.lab.store import SessionStore


class Runtime:
    library=None
    def start(self):pass
    def close(self):pass


def test_http_freeze_cursor_worker_restore_and_verified_download(tmp_path,monkeypatch):
    store=SessionStore(tmp_path)
    try:
        identity=dict(kind='video',media_id='media',cache_key='key',generation='gen',cache_manifest_sha256='manifest')
        store.state.source_id='live';store.state.person_id='right';store.state.position_s=.03
        store.mark('A',category='deployment',observed_epoch=2,transport_epoch=2,source_identity=identity)
        cursor=store.marks_snapshot()['through_sequence']
        candidate=dict(evaluation_id='a'*32,run_index=0,signal_id='speed',end_s=1,high=1,low=.2)
        def features(evaluation,request):
            return {'request':request.model_dump(),
                'rows':[{'time_s':0.,'value':0.},{'time_s':.03,'value':2.},{'time_s':.06,'value':2.}],
                'provenance':{'source':{'person_id':'right'},'source_record':{'cache_manifest_sha256':'manifest',
                    'cache_manifest':{'media_sha256':'media','key':'key','generation':'gen'}}}}
        monkeypatch.setattr(app_module,'candidate_snapshot',features)
        body=dict(candidate=candidate,source_id='live',person_id='right',session_id=store.state.session_id,
                  observed_epoch=2,category='deployment',through_sequence=cursor,mark_support=[[0,1]],control_offsets_s=[.01])
        with TestClient(app_module.create_app(tmp_path,store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
            bad=deepcopy(body);bad['mark_support']=[[1,0]]
            assert client.post('/api/research/r03',json=bad).status_code==422
            bad=deepcopy(body);bad['person_id']='left'
            assert client.post('/api/research/r03',json=bad).status_code==422
            assert client.get('/api/research/r03').json()==[]
            response=client.post('/api/research/r03',json=body)
            assert response.status_code==200,response.text
            ident=response.json()['id']
            # Append after freezing: this must not enter this run.
            store.mark('later',category='deployment',observed_epoch=2,transport_epoch=2,source_identity=identity)
            deadline=time.monotonic()+10
            while True:
                report=next(j for j in client.get('/api/research/r03').json() if j['id']==ident)
                if report['status'] not in ('queued','running'):break
                assert time.monotonic()<deadline
                time.sleep(.02)
            assert report['status']=='complete',report
            result=client.get(f'/api/research/r03/{ident}/artifacts/result.json')
            assert result.status_code==200
            assert len(result.json()['temporal_controls']['conditions'])==2
            assert all(c['paired']['common_support']==result.json()['temporal_controls']['common_support'] for c in result.json()['temporal_controls']['conditions'])
            assert len(result.json()['annotations'])==1
            assert len(result.json()['comparison']['matches'])==1
            frozen=client.get(f'/api/research/r03/{ident}/artifacts/marks.json').json()
            assert frozen['through_sequence']==cursor
            assert client.get(f'/api/research/r03/{ident}/artifacts/worker.log').status_code==422
        with TestClient(app_module.create_app(tmp_path,store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
            assert client.get('/api/research/r03').json()[0]['status']=='complete'
            assert client.get(f'/api/research/r03/{ident}/artifacts/result.json').content==result.content
            (tmp_path/'research/r03'/ident/'result.json').write_text('{}')
            assert client.get(f'/api/research/r03/{ident}/artifacts/result.json').status_code==422
    finally:store.close()


def test_http_without_replay_library_cannot_start(tmp_path):
    with TestClient(app_module.create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get('/api/research/r03').json()==[]
        body=dict(candidate=dict(evaluation_id='a'*32,run_index=0,signal_id='speed',end_s=1,high=1,low=0),
                  source_id='source',person_id='person',session_id='session',observed_epoch=0,
                  category='deployment',through_sequence=0,mark_support=[[0,1]])
        response=client.post('/api/research/r03',json=body)
        assert response.status_code==422 and 'library' in response.json()['detail']
