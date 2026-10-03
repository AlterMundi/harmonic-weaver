import time
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app


def test_controls_api_real_worker_portable_preset_and_artifacts(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        c=client.post('/api/research/r07-controls/configuration',json={'settings':{'duration_samples':800,'forcing_samples':400}})
        assert c.status_code==200
        assert client.get('/api/research/r07-controls').json()==[]
        job=client.post('/api/research/r07-controls',json=c.json()['settings']);assert job.status_code==200
        ident=job.json()['id'];deadline=time.monotonic()+15
        while True:
            report=client.get(f'/api/research/r07-controls/{ident}').json()
            if report['status'] not in ('queued','running'):break
            assert time.monotonic()<deadline;time.sleep(.02)
        assert report['status']=='complete'
        result=client.get(f'/api/research/r07-controls/{ident}/artifacts/result.json')
        assert result.status_code==200
        assert set(result.json()['conditions'])=={'impulse','pulse','multisine','seeded_noise'}
        assert client.get(f'/api/research/r07-controls/{ident}/artifacts/worker.log').status_code==422
        assert client.post('/api/research/r07-controls',json={'seed':True}).status_code==422
