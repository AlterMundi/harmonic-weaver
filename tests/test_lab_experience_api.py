from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_experience_protocol import data


def test_experience_preview_is_declared_and_response_validation_stateless(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        request=data();response=client.post('/api/research/r10/preview',json=request)
        assert response.status_code==200 and len(response.json()['trials'])==3
        protocol=response.json()['request'];ratings={i['id']:None for i in protocol['config']['items']}
        validated=client.post('/api/research/r10/validate-response',json={'protocol':protocol,'response':{'trial_id':'trial-0001','ratings':ratings}})
        assert validated.status_code==200 and validated.json()['role']=='observer'
        ratings['pleasure']=101
        assert client.post('/api/research/r10/validate-response',json={'protocol':protocol,'response':{'trial_id':'trial-0001','ratings':ratings}}).status_code==422


def test_experience_presets_portable_strict_and_restart(tmp_path):
    url='/api/research/r10/presets';body={'name':'Condiciones','config':{'conditions':['video_only','sound_only'],'scale_min':1,'scale_max':7}}
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post(url,json=body);assert response.status_code==200
        ident=response.json()['id'];exported=client.get(f'{url}/{ident}')
        assert 'attachment' in exported.headers['content-disposition'] and 'id' not in exported.json()
        for key in ('participant_slot','role','order_index','stimuli','ratings','trial_id'):
            assert client.post(url,json={**body,'config':{**body['config'],key:'private'}}).status_code==422
        assert client.post(url,json={**body,'config':{'conditions':['video_only','video_only']}}).status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(url).json()[0]['config']==exported.json()['config']
        assert client.get(f'{url}/{ident}').content==exported.content
