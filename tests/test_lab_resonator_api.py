"""Real synthetic-pose evaluation -> verified selection -> HTTP -> R05 worker."""
import time
from uuid import uuid4
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.evaluation.runner import Request,run
from harmonic_weaver.lab.presets import initial_presets
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.store import SessionStore
from test_lab_evaluation import source_fixture


class Runtime:
    library=None
    def start(self):pass
    def close(self):pass


def test_real_http_freeze_pcm_repeat_restore_and_changed_replay(tmp_path):
    source,_,_=source_fixture(tmp_path)
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident
    folder.mkdir(parents=True)
    preset=next(p for p in initial_presets() if p.algorithm.id=='local')
    request=Request(presets=[preset],sources=[source])
    atomic_json(folder/'request.json',request.model_dump());run(request,folder/'result')
    store=SessionStore(root,prepare=PreparedRoutes)
    body=dict(selection=dict(evaluation_id=ident,run_index=0,signal_id='zone.1.speed',start_s=.2,end_s=2),
              resonators={'sample_rate':8000},excitation={'high':.1,'low':.02},render={'tail_s':.1})
    outputs=[];jobs=[]
    try:
        with TestClient(create_app(root,store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
            for _ in range(2):
                response=client.post('/api/research/r05',json=body)
                assert response.status_code==200,response.text
                job=response.json()['id'];jobs.append(job);deadline=time.monotonic()+10
                while True:
                    report=next(j for j in client.get('/api/research/r05').json() if j['id']==job)
                    if report['status'] not in ('queued','running'):break
                    assert time.monotonic()<deadline;time.sleep(.02)
                assert report['status']=='complete',report
                assert report['levels']['frames']==15200
                frozen=client.get(f'/api/research/r05/{job}/artifacts/input.json').json()
                assert frozen['provenance']['source']['person_id']=='one'
                assert frozen['duplicate_control_holds_excluded']>0 and frozen['unit']
                assert frozen['request']['high']==.1 and frozen['request']['low']==.02
                wav=client.get(f'/api/research/r05/{job}/artifacts/sum.wav')
                assert wav.status_code==200;outputs.append(wav.content)
            assert outputs[0]==outputs[1]
            bad={**body,'render':{'tail_s':11}}
            assert client.post('/api/research/r05',json=bad).status_code==422
            assert client.get(f'/api/research/r05/{jobs[0]}/artifacts/worker.log').status_code==422
            (folder/'result/source-00-preset-00.jsonl').write_text('changed')
            assert client.post('/api/research/r05',json=body).status_code==422
            assert len(client.get('/api/research/r05').json())==2
        with TestClient(create_app(root,store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
            assert len(client.get('/api/research/r05').json())==2
            assert client.get(f'/api/research/r05/{jobs[0]}/artifacts/sum.wav').content==outputs[0]
            (root/'research/r05'/jobs[0]/'sum.wav').write_bytes(b'broken')
            assert client.get(f'/api/research/r05/{jobs[0]}/artifacts/voices.wav').status_code==422
    finally:store.close()


def test_no_library_does_not_enqueue(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body={'selection':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',end_s=1)}
        assert client.post('/api/research/r05',json=body).status_code==422
        assert client.get('/api/research/r05').json()==[]


def test_portable_configuration_validates_without_job_or_source(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post('/api/research/r05/configuration',json={})
        assert response.status_code==200
        config=response.json()
        assert len(config['resonators']['ratios'])==6
        assert set(config)=={'schema_version','resonators','excitation','render'}
        config['excitation']['mode']='positive_delta';config['render']['tail_s']=10
        assert client.post('/api/research/r05/configuration',json=config).json()==config
        for bad in ({**config,'selection':{}},{**config,'schema_version':2},
                    {**config,'excitation':{**config['excitation'],'voice_weights':[1]*7}},
                    {**config,'resonators':{**config['resonators'],'topology':'custom','adjacency':[[0]]}}):
            assert client.post('/api/research/r05/configuration',json=bad).status_code==422
        assert client.get('/api/research/r05').json()==[]
