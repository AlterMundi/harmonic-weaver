import subprocess
from types import SimpleNamespace
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.media import VideoLibrary


def test_rope_api_library_binding_revisions_restore_and_reject(tmp_path):
    video=tmp_path/'test.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    root=tmp_path/'data'
    library=VideoLibrary(root/'library')
    library.index.write_text(__import__('json').dumps({'local-video':{'id':'local-video','name':video.name,'path':str(video)}}))
    library=VideoLibrary(root/'library')
    assert library.jobs=={}
    runtime=SimpleNamespace(library=library,start=lambda:None,close=lambda:None)
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        media=client.post('/api/research/r08/probe',json={'media_id':'local-video'})
        assert media.status_code==200
        job=client.post('/api/research/r08/reads',json={'media_id':'local-video'}).json()
        import time
        deadline=time.monotonic()+5
        while client.get(f"/api/research/r08/reads/{job['id']}").json()['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        decoded=client.get(f"/api/research/r08/reads/{job['id']}/result")
        assert decoded.status_code==200 and decoded.json()==media.json()
        assert client.post('/api/research/r08/reads',json={'media_id':'local-video','frame_index':0}).status_code==422

        frame_url='/api/research/r08/media/local-video/frames/2'
        image=client.get(frame_url,params={'sha256':media.json()['media_sha256']})
        assert image.status_code==200 and image.content.startswith(b'\x89PNG\r\n\x1a\n')
        assert int.from_bytes(image.content[16:20],'big')==160
        assert int.from_bytes(image.content[20:24],'big')==120
        assert client.get(frame_url,params={'sha256':'0'*64}).status_code==422
        assert client.get('/api/research/r08/media/local-video/frames/5',params={'sha256':media.json()['media_sha256']}).status_code==422
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
