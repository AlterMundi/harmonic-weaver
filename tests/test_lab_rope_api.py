import subprocess
from types import SimpleNamespace
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app


def test_rope_api_library_binding_revisions_restore_and_reject(tmp_path):
    video=tmp_path/'test.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    def path(ident):
        if ident!='local-video':raise KeyError(ident)
        return video
    runtime=SimpleNamespace(library=SimpleNamespace(path=path),start=lambda:None,close=lambda:None)
    root=tmp_path/'data'
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        media=client.post('/api/research/r08/probe',json={'media_id':'local-video'})
        assert media.status_code==200
        annotation={'media_sha256':media.json()['media_sha256'],'width_px':160,'height_px':120,'frames':[]}
        first=client.post('/api/research/r08',json={'media_id':'local-video','annotation':annotation})
        assert first.status_code==200
        ident=first.json()['id']
        second=client.post('/api/research/r08',json={'media_id':'local-video','annotation':annotation,'parent_id':ident})
        assert second.status_code==200 and second.json()['parent_manifest_sha256']
        assert client.post('/api/research/r08/probe',json={'media_id':str(video)}).status_code==404
        assert client.post('/api/research/r08/probe',json={'media_id':'local-video','path':str(video)}).status_code==422
        assert client.get(f'/api/research/r08/{ident}/artifacts/worker.log').status_code==422
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        assert len(client.get('/api/research/r08').json())==2
        assert client.get(f'/api/research/r08/{ident}/artifacts/annotation.json').json()['frames']==[]
        assert client.post(f'/api/research/r08/{ident}/rebind',json={'media_id':'local-video'}).status_code==200
        with video.open('ab') as handle:handle.write(b'changed')
        assert client.post(f'/api/research/r08/{ident}/rebind',json={'media_id':'local-video'}).status_code==422
    with TestClient(create_app(root),base_url='http://127.0.0.1') as client:
        assert len(client.get('/api/research/r08').json())==2
        assert client.post('/api/research/r08/probe',json={'media_id':'local-video'}).status_code==422
