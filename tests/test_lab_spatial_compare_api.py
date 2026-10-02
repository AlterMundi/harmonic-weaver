from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_spatial_compare_run import data


def test_compare_http_export_restart_and_incompatible_inputs(tmp_path):
    url='/api/research/r09/comparisons'
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        saved=client.post(url,json=data());assert saved.status_code==200;ident=saved.json()['id']
        result=client.get(f'{url}/{ident}/artifacts/result.json')
        assert result.status_code==200 and 'attachment' in result.headers['content-disposition']
        assert result.json()['coverage']['supported_points']==1
        wrong=data();wrong['comparison']['candidate']['coordinate_frame']='other'
        assert client.post(url,json=wrong).status_code==422
        assert client.get(f'{url}/{ident}/artifacts/video.mp4').status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(url).json()[0]['read_verification']=='recomputed'
        assert client.get(f'{url}/{ident}/artifacts/result.json').content==result.content
