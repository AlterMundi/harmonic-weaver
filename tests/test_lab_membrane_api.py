import time
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from test_resonator_artifacts import fixture


def test_real_r07_api_worker_portable_config_and_artifacts(tmp_path):
    source_id = 'a'*32
    source = tmp_path/'research/r05'/source_id
    fixture(source)
    settings = {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 800}
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1') as client:
        config = client.post('/api/research/r07/configuration', json={'settings': settings})
        assert config.status_code == 200
        assert 'source_run_id' not in config.json()
        created = client.post('/api/research/r07', json={'source_run_id': source_id, 'settings': config.json()['settings']})
        assert created.status_code == 200
        ident = created.json()['id']
        deadline = time.monotonic()+15
        while True:
            report = client.get(f'/api/research/r07/{ident}').json()
            if report['status'] not in ('queued', 'running'): break
            assert time.monotonic() < deadline
            time.sleep(.02)
        assert report['status'] == 'complete'
        artifact = client.get(f'/api/research/r07/{ident}/artifacts/result.json')
        assert artifact.status_code == 200
        assert artifact.json()['window']['sample_count'] == 800
        assert client.get(f'/api/research/r07/{ident}/artifacts/source.json').status_code == 422
        assert client.post('/api/research/r07', json={'source_run_id': '../bad', 'settings': settings}).status_code == 422
        assert client.post('/api/research/r07/configuration', json={'schema_version': 2, 'settings': settings}).status_code == 422
