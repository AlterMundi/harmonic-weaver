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


def test_neuro_synthetic_snr_explicit_control_without_archive(tmp_path):
    from research.test_neuro_snr import config
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body=config();response=client.post('/api/research/r11/synthetic-snr',json=body)
        assert response.status_code==200,response.text
        assert response.json()['metrics']['status']=='finite'
        assert response.json()==client.post('/api/research/r11/synthetic-snr',json=body).json()
        body['signal']['frequency_hz']=128
        assert client.post('/api/research/r11/synthetic-snr',json=body).status_code==422
        assert list((tmp_path/'research/r11-observations').iterdir())==[]


def test_snr_archive_api_repeat_restart_and_artifact_allowlist(tmp_path):
    from research.test_neuro_snr import config
    url='/api/research/r11/snr-records'
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post(url,json=config())
        assert response.status_code==200,response.text
        saved=response.json();ident=saved['id']
        assert client.post(url,json=config()).json()['id']==ident
        result=client.get(f'{url}/{ident}/artifacts/result.json')
        assert result.status_code==200 and 'attachment' in result.headers['content-disposition']
        assert result.json()['metrics']['snr_db']>6
        assert client.get(f'{url}/{ident}/artifacts/unexpected').status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert len(client.get(url).json())==1
        assert client.get(f'{url}/{ident}/artifacts/result.json').content==result.content


def test_explicit_csv_api_convert_then_archive_preserves_raw_digest(tmp_path):
    from research.test_neuro_csv import request
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body=request();converted=client.post('/api/research/r11/import-csv',json=body)
        assert converted.status_code==200,converted.text
        native=converted.json()['stream']
        saved=client.post('/api/research/r11/observations',json=native)
        assert saved.status_code==200,saved.text
        ident=saved.json()['id']
        reopened=client.get(f'/api/research/r11/observations/{ident}/artifacts/request.json').json()
        assert reopened==native and reopened['raw_source_sha256']
        body['csv_text']='index,time_ms,channel\n0,0,"unfinished'
        assert client.post('/api/research/r11/import-csv',json=body).status_code==422
