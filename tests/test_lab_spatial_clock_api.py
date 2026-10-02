from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_spatial_clock_fit import data


def test_clock_persistence_http_export_and_restart(tmp_path):
    url='/api/research/r09/clock-fits';body={'fit':data(),'idempotency_key':'b'*32}
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post(url,json=body);assert response.status_code==200
        ident=response.json()['id'];artifact=client.get(f'{url}/{ident}/artifacts/result.json')
        assert artifact.status_code==200 and 'attachment' in artifact.headers['content-disposition']
        assert client.post(url,json=body).json()['id']==ident
        assert client.get(f'{url}/{ident}/artifacts/video.mp4').status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(url).json()[0]['read_verification']=='recomputed'
        assert client.get(f'{url}/{ident}/artifacts/result.json').content==artifact.content


def test_apply_clock_http_preserves_frames_and_rejects_mismatched_clock(tmp_path):
    from research.test_spatial_adapter import data as pose_data
    from harmonic_weaver.lab.research.spatial_adapter import convert
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        ident=client.post('/api/research/r09/clock-fits',json={'fit':data()}).json()['id']
        stream=convert(pose_data())['stream'];stream['clock']['source_clock']='camera'
        body={'fit_id':ident,'stream':stream}
        result=client.post('/api/research/r09/apply-clock',json=body)
        assert result.status_code==200 and result.json()['stream']['frames']==stream['frames']
        stream['clock']['source_clock']='other'
        assert client.post('/api/research/r09/apply-clock',json=body).status_code==422
