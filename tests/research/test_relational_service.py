import pytest
from harmonic_weaver.lab.research.relational_service import RelationalService
from harmonic_weaver.lab.research.coincidence_service import CoincidenceService
from harmonic_weaver.lab.cache import sha256_file


def test_owned_r04_worker_restores_verifies_and_keeps_r03_inventory_separate(tmp_path):
    service=RelationalService(tmp_path)
    try:
        job=service.start({'samples':30})
        assert service.processes[job['id']].wait(timeout=10)==0
        assert service.report(job['id'])['status']=='complete'
        restored=RelationalService(tmp_path)
        assert restored.list()[0]['status']=='complete'
        assert restored.artifact(job['id'],'request.json').is_file()
        result=restored.artifact(job['id'],'result.json')
        assert sha256_file(result)==restored.report(job['id'])['output']['sha256']
        assert CoincidenceService(tmp_path).list()==[]
        with pytest.raises(ValueError,match='Unknown'):restored.artifact(job['id'],'marks.json')
        result.write_text('{}')
        with pytest.raises(ValueError,match='changed'):restored.artifact(job['id'],'result.json')
        restored.close()
    finally:service.close()


def test_r04_http_real_worker_download_and_restore(tmp_path):
    import time
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.post('/api/research/r04',json={'samples':1}).status_code==422
        response=client.post('/api/research/r04',json={'samples':30})
        assert response.status_code==200,response.text
        ident=response.json()['id'];deadline=time.monotonic()+10
        while True:
            report=client.get('/api/research/r04').json()[0]
            if report['status'] not in ('queued','running'):break
            assert time.monotonic()<deadline
            time.sleep(.02)
        assert report['status']=='complete' and report['line']=='R04'
        result=client.get(f'/api/research/r04/{ident}/artifacts/result.json')
        assert result.status_code==200 and len(result.json()['traces'])==25
        assert client.get('/api/research/r03').json()==[]
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get('/api/research/r04').json()[0]['status']=='complete'
        assert client.get(f'/api/research/r04/{ident}/artifacts/result.json').content==result.content
