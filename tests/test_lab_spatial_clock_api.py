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


def test_clock_conversion_http_sources_are_server_resolved(tmp_path):
    from research.test_spatial_external_stream import data as stream_data
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        stream=stream_data();stream['clock']['source_clock']='camera'
        source=client.post('/api/research/r09/conversions',json={'stream':stream}).json()['id']
        fit_id=client.post('/api/research/r09/clock-fits',json={'fit':data()}).json()['id']
        selection={'conversion_id':source,'fit_id':fit_id,'idempotency_key':'c'*32}
        response=client.post('/api/research/r09/clock-conversions',json=selection);assert response.status_code==200
        ident=response.json()['id'];result=client.get(f'/api/research/r09/conversions/{ident}/artifacts/result.json').json()
        assert result['clock_application']['clock_fit']['id']==fit_id
        assert client.post('/api/research/r09/clock-conversions',json=selection).json()['id']==ident
        assert client.post('/api/research/r09/conversions',json={'stream':result['stream'],'clock_application':result['clock_application']}).status_code==422
