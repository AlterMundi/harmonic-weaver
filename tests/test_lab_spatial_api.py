from copy import deepcopy
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_spatial_adapter import data


def test_conversion_http_preserves_source_and_reports_coverage(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body=data();response=client.post('/api/research/r09/convert',json=body)
        assert response.status_code==200
        result=response.json()
        assert result['coverage']=={'observed':1,'held':1,'inferred':0,'missing':32}
        assert result['common_times_s']==[0.,.2]
        assert result['request']['person_id']==body['person_id']
        assert result['stream']['units']=='frame_height'
        validated=client.post('/api/research/r09/validate',json=result['stream'])
        assert validated.status_code==200 and validated.json()['validation']=='contract_only'
        assert validated.json()['stream']==result['stream']
        for patch in ({'person_id':True},{'clock':{}},{'path':'private-video'}):
            assert client.post('/api/research/r09/convert',json={**body,**patch}).status_code==422
        changed=deepcopy(result['stream']);changed['units']='metres'
        assert client.post('/api/research/r09/validate',json=changed).status_code==422
        assert not (tmp_path/'research/r09').exists() # Stateless conversion, no private archive yet.


def test_source_http_inventory_generation_and_explicit_slot(tmp_path):
    from types import SimpleNamespace
    from harmonic_weaver.lab.media import VideoLibrary,VideoJob
    from harmonic_weaver.lab.contracts import MotionFrame,PerceptionSettings
    library=VideoLibrary(tmp_path/'library');body=data()
    library.jobs['job']=VideoJob('job',tmp_path/'nonexistent.mp4',PerceptionSettings(checkpoint='synthetic.pt'),
        status='ready',generation='gen-1',cache_key='a'*64,duration_s=1.,
        person_ids=[body['person_id']],frames=[MotionFrame.model_validate(f) for f in body['frames']],times=[0.,.2])
    runtime=SimpleNamespace(library=library,start=lambda:None,close=lambda:None)
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        sources=client.get('/api/research/r09/sources').json()
        assert sources[0]['person_ids']==[body['person_id']] and 'path' not in sources[0]
        selection={'job_id':'job','start_s':0.,'end_s':.2,'person_id':body['person_id'],'clock':body['clock']}
        result=client.post('/api/research/r09/source',json=selection)
        assert result.status_code==200 and result.json()['tracking_provenance']['generation']=='gen-1'
        assert len(result.json()['stream']['frames'])==2
        absent=client.post('/api/research/r09/source',json={**selection,'person_id':'absent'})
        assert absent.json()['coverage']['missing']==34
        assert client.post('/api/research/r09/source',json={**selection,'job_id':'missing'}).status_code==404
        library.jobs['job'].status='tracking'
        assert client.get('/api/research/r09/sources').json()==[]
        assert client.post('/api/research/r09/source',json=selection).status_code==422
