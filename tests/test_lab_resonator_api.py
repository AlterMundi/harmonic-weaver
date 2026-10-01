"""Real synthetic-pose evaluation -> verified selection -> HTTP -> R05 worker."""
import time
import pytest
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


@pytest.mark.parametrize('paired',[False,True])
def test_real_http_freeze_pcm_repeat_restore_and_changed_replay(tmp_path,paired):
    source,_,_=source_fixture(tmp_path)
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident
    folder.mkdir(parents=True)
    preset=next(p for p in initial_presets() if p.algorithm.id=='local')
    request=Request(presets=[preset],sources=[source])
    atomic_json(folder/'request.json',request.model_dump());run(request,folder/'result')
    store=SessionStore(root,prepare=PreparedRoutes)
    body=dict(selection=dict(evaluation_id=ident,run_index=0,signal_id='zone.1.speed',start_s=.2,end_s=2),
              resonators={'sample_rate':8000},excitation={'high':.1,'low':.02},render={'tail_s':.1})
    if paired:body['mapping']={'attack_s':.01,'release_s':.05}
    sum_name='excited-sum.wav' if paired else 'sum.wav'
    voice_name='mapped-voices.wav' if paired else 'voices.wav'
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
                if paired:
                    result=client.get(f'/api/research/r05/{job}/artifacts/result.json')
                    assert result.status_code==200 and result.json()['clock']['total_frames']==15200
                    assert result.json()['mapping_preparation']['mapping']['attack_s']==.01
                else:assert report['levels']['frames']==15200
                frozen=client.get(f'/api/research/r05/{job}/artifacts/input.json').json()
                assert frozen['provenance']['source']['person_id']=='one'
                assert frozen['duplicate_control_holds_excluded']>0 and frozen['unit']
                assert frozen['request']['high']==.1 and frozen['request']['low']==.02
                wav=client.get(f'/api/research/r05/{job}/artifacts/{sum_name}')
                assert wav.status_code==200;outputs.append(wav.content)
                projection=client.post(f'/api/research/r05/{job}/projection',json={
                    'arm':'mapped' if paired else 'single','start_sample':800,'points':32,'stride':2})
                assert projection.status_code==200,projection.text
                assert projection.json()['sample_indices']==list(range(800,864,2))
                assert projection.json()['voices']==6 and len(projection.json()['points'])==32
                listen=client.get(f'/api/research/r05/{job}/listen/'+('mapped' if paired else 'single'),headers={'Range':'bytes=0-43'})
                assert listen.status_code==206 and listen.content[:4]==b'RIFF'
                info=client.get(f'/api/research/r05/{job}/source-info')
                assert info.status_code==200 and info.json()['person_id']=='one'
                assert info.json()['source_start_s']==.2 and info.json()['source_end_s']==2
                assert 'media_path' not in info.json()
                original_video=client.get(f'/api/research/r05/{job}/source')
                assert original_video.status_code==200 and original_video.content==b'a'
            assert outputs[0]==outputs[1]
            bad={**body,'render':{'tail_s':11}}
            assert client.post('/api/research/r05',json=bad).status_code==422
            assert client.get(f'/api/research/r05/{jobs[0]}/artifacts/worker.log').status_code==422
            (folder/'result/source-00-preset-00.jsonl').write_text('changed')
            assert client.post('/api/research/r05',json=body).status_code==422
            assert len(client.get('/api/research/r05').json())==2
        with TestClient(create_app(root,store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
            assert len(client.get('/api/research/r05').json())==2
            assert client.get(f'/api/research/r05/{jobs[0]}/artifacts/{sum_name}').content==outputs[0]
            path=root/'research/r05'/jobs[0]
            (path/('mapped/sum.wav' if paired else 'sum.wav')).write_bytes(b'broken')
            assert client.get(f'/api/research/r05/{jobs[0]}/artifacts/{voice_name}').status_code==422
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
        paired={**config,'mapping':{'attack_s':.01}}
        validated=client.post('/api/research/r05/configuration',json=paired)
        assert validated.status_code==200 and validated.json()['mapping']['attack_s']==.01
        assert len(validated.json()['mapping']['voice_weights'])==6
        assert client.post('/api/research/r05/configuration',json={**config,'mapping':{'voice_weights':[1]*7}}).status_code==422
        for bad in ({**config,'selection':{}},{**config,'schema_version':2},
                    {**config,'excitation':{**config['excitation'],'voice_weights':[1]*7}},
                    {**config,'resonators':{**config['resonators'],'topology':'custom','adjacency':[[0]]}}):
            assert client.post('/api/research/r05/configuration',json=bad).status_code==422
        assert client.get('/api/research/r05').json()==[]
        projection={'schema_version':1,'settings':{'scale_x':2,'weights':[1]*6}}
        validated=client.post('/api/research/r05/projection/configuration',json=projection)
        assert validated.status_code==200 and validated.json()['settings']['scale_x']==2
        assert 'start_sample' not in validated.json()['settings']
        with_playback={**projection,'playback':{'follow_audio':True,'refresh_hz':12,'preview_gain':.5,'loop_audio':True}}
        assert client.post('/api/research/r05/projection/configuration',json=with_playback).json()=={
            **validated.json(),'playback':with_playback['playback']}
        assert client.post('/api/research/r05/projection/configuration',json={**projection,'playback':{'refresh_hz':31}}).status_code==422
        for bad in ({**projection,'source_id':'private'},
                    {**projection,'settings':{'start_sample':30}},
                    {**projection,'settings':{'weights':[101]*6}},
                    {**projection,'schema_version':2}):
            assert client.post('/api/research/r05/projection/configuration',json=bad).status_code==422
        assert client.get('/api/research/r05').json()==[]
