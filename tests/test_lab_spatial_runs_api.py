import json
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_spatial_adapter import data
from harmonic_weaver.lab.cache import atomic_json,sha256_file


def test_persistence_http_restart_download_and_corrupt_inventory(tmp_path):
    url='/api/research/r09/conversions'
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body={'conversion':data()};saved=client.post(url,json=body)
        assert saved.status_code==200;ident=saved.json()['id']
        result=client.get(f'{url}/{ident}/artifacts/result.json')
        assert result.status_code==200 and 'attachment' in result.headers['content-disposition']
        assert result.json()['coverage']['observed']==1
        assert client.post(url,json={**body,'path':'private'}).status_code==422
        assert client.get(f'{url}/{ident}/artifacts/video.mp4').status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(url).json()[0]['read_verification']=='recomputed'
        assert client.get(f'{url}/{ident}/artifacts/result.json').content==result.content
        folder=tmp_path/'research/r09-conversions'/ident
        document=result.json();document['coverage']['observed']=999;atomic_json(folder/'result.json',document)
        manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
        assert client.get(url).json()==[]
        assert client.get(f'{url}/{ident}/artifacts/result.json').status_code==422
