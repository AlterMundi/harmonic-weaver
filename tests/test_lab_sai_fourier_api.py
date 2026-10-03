import time

from fastapi.testclient import TestClient

from harmonic_weaver.lab.app import create_app


def test_fourier_api_runs_exports_restores_and_rejects_invalid_config(tmp_path):
    url = '/api/research/sai-fourier'
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1') as client:
        assert client.post(url, json={'samples': 12}).status_code == 422
        response = client.post(url, json={'samples': 64, 'hz': 60, 'seeds': [7]})
        assert response.status_code == 200, response.text
        ident = response.json()['id']
        deadline = time.monotonic() + 20
        while True:
            report = client.get(f'{url}/{ident}').json()
            if report['status'] not in ('queued', 'running'):
                break
            assert time.monotonic() < deadline
            time.sleep(.02)
        assert report['status'] == 'complete', report
        result = client.get(f'{url}/{ident}/artifacts/result.json')
        assert result.status_code == 200 and 'attachment' in result.headers['content-disposition']
        assert result.json()['settings']['samples'] == 64
        assert client.get(f'{url}/{ident}/artifacts/unknown').status_code == 422
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1') as client:
        assert len(client.get(url).json()) == 1
        assert client.get(f'{url}/{ident}/artifacts/result.json').content == result.content
