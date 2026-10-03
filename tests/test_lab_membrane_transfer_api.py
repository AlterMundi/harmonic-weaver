from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app


def test_transfer_api_config_repeat_restore_and_tamper(tmp_path):
    ids=[];outputs=[]
    for i in range(2):
        with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
            c=client.post('/api/research/r07-transfer/configuration',json={})
            assert c.status_code==200
            assert len(client.get('/api/research/r07-transfer').json())==i
            job=client.post('/api/research/r07-transfer',json=c.json()['settings'])
            assert job.status_code==200
            ident=job.json()['id'];ids.append(ident)
            result=client.get(f'/api/research/r07-transfer/{ident}/artifacts/result.json')
            assert result.status_code==200
            outputs.append(result.content)
            assert client.get(f'/api/research/r07-transfer/{ident}/artifacts/worker.log').status_code==422
    assert outputs[0]==outputs[1]
    (tmp_path/'research/r07-transfer'/ids[0]/'result.json').write_bytes(b'changed')
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(f'/api/research/r07-transfer/{ids[0]}/artifacts/result.json').status_code==422
        assert len(client.get('/api/research/r07-transfer').json())==1
