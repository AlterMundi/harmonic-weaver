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
