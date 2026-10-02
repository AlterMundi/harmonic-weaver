from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_neuro_observations import data


def test_neuro_inspect_preserves_raw_without_acquisition_or_archive(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body=data();response=client.post('/api/research/r11/inspect',json=body)
        assert response.status_code==200,response.text
        result=response.json()
        assert result['stream']['samples'][0]['values']['ch1']==0
        assert result['stream']['samples'][1]['values']['ch1'] is None
        assert result['index_gaps'][0]['missing_index_count']==1
        assert result['channels'][0]['reference']=='declared-reference'
        assert client.post('/api/research/r11/inspect',json={**body,'device':'invented'}).status_code==422
        assert list((tmp_path/'research/r11-observations').iterdir())==[]


def test_neuro_saved_raw_export_retry_and_restart(tmp_path):
    url='/api/research/r11/observations'
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        saved=client.post(url,json=data());assert saved.status_code==200,saved.text
        ident=saved.json()['id'];assert client.post(url,json=data()).json()['id']==ident
        exported=client.get(f'{url}/{ident}/artifacts/request.json')
        assert 'attachment' in exported.headers['content-disposition']
        assert exported.json()['samples'][1]['missing_causes']=={'ch1':'dropped'}
        assert client.get(f'{url}/{ident}/artifacts/private.mp4').status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert len(client.get(url).json())==1
        assert client.get(f'{url}/{ident}/artifacts/request.json').content==exported.content
