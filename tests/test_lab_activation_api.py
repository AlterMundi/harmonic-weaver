import time
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.store import SessionStore


def settings():return {'medium':{'sample_rate':8000},'excitation_span_s':.1,'tail_s':.1,'seed':31}


def wait(client,ident):
    deadline=time.monotonic()+15
    while True:
        value=client.get(f'/api/research/r06/{ident}').json()
        if value['status'] not in ('queued','running'):return value
        assert time.monotonic()<deadline;time.sleep(.02)


def test_api_portable_configuration_real_worker_repeat_restore_and_integrity(tmp_path):
    store=SessionStore(tmp_path);outputs=[];ids=[]
    try:
        for iteration in range(2):
            with TestClient(create_app(tmp_path,store=store),base_url='http://127.0.0.1') as client:
                config=client.post('/api/research/r06/configuration',json={'settings':settings()})
                assert config.status_code==200
                portable=config.json();assert portable['schema_version']==1
                assert portable['settings']['seed']==31
                assert not set(portable)&{'source','person','calibration','run_id'}
                if iteration:
                    assert client.get(f'/api/research/r06/{ids[0]}').json()['status']=='complete'
                created=client.post('/api/research/r06',json=portable['settings'])
                assert created.status_code==200
                ident=created.json()['id'];ids.append(ident)
                assert wait(client,ident)['status']=='complete'
                result=client.get(f'/api/research/r06/{ident}/artifacts/result.json')
                assert result.status_code==200;outputs.append(result.content)
                assert set(result.json()['conditions'])=={'rational','phi','sqrt2','random'}
                assert client.get(f'/api/research/r06/{ident}/artifacts/request.json').json()==portable['settings']
                assert client.get(f'/api/research/r06/{ident}/artifacts/worker.log').status_code==422
        assert outputs[0]==outputs[1]
        (tmp_path/'research/r06'/ids[0]/'result.json').write_bytes(b'changed')
        with TestClient(create_app(tmp_path,store=store),base_url='http://127.0.0.1') as client:
            assert len(client.get('/api/research/r06').json())==2
            assert client.get(f'/api/research/r06/{ids[0]}/artifacts/result.json').status_code==422
            assert client.post(f'/api/research/r06/{ids[1]}/cancel',json={}).status_code==422
    finally:store.close()


def test_invalid_settings_never_enqueue_and_schema_is_strict(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        for bad in [{'event_count':3},{'tail_s':-1},{'trace_stride':1},{'seed':True},{'unexpected':1}]:
            assert client.post('/api/research/r06',json=bad).status_code==422
            assert client.post('/api/research/r06/configuration',json={'settings':bad}).status_code==422
        assert client.post('/api/research/r06/configuration',json={'schema_version':2}).status_code==422
        assert client.get('/api/research/r06').json()==[]
        assert client.get('/api/research/r06/not-a-job').status_code==422


def test_cancel_owned_api_job_keeps_partial_artifacts_unavailable(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        request={'medium':{'sample_rate':96000},'excitation_span_s':5,'tail_s':10,
                 'event_count':32,'trace_stride':8192}
        started=client.post('/api/research/r06',json=request);assert started.status_code==200
        ident=started.json()['id'];deadline=time.monotonic()+10
        while client.get(f'/api/research/r06/{ident}').json()['status']=='queued':
            assert time.monotonic()<deadline;time.sleep(.01)
        assert client.post(f'/api/research/r06/{ident}/cancel',json={}).json()['status']=='cancelled'
        assert client.get(f'/api/research/r06/{ident}/artifacts/result.json').status_code==422
        assert client.get(f'/api/research/r06/{ident}/artifacts/manifest.json').status_code==200
