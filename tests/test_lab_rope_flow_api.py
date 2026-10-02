import json
import subprocess
import time
from types import SimpleNamespace
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.media import VideoLibrary


def test_flow_api_library_binding_download_and_restart(tmp_path):
    video=tmp_path/'video.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    root=tmp_path/'data';library=VideoLibrary(root/'library')
    library.index.write_text(json.dumps({'synthetic':{'id':'synthetic','name':video.name,'path':str(video)}}))
    runtime=SimpleNamespace(library=VideoLibrary(root/'library'),start=lambda:None,close=lambda:None)
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        media=client.post('/api/research/r08/probe',json={'media_id':'synthetic'}).json()
        request={k:media[k] for k in ('media_sha256','width_px','height_px')}
        request.update(start_frame_index=0,frame_times_s=media['frame_times_s'][:3],seeds=[{'x':.5,'y':.5}])
        assert client.post('/api/research/r08/flow',json={'media_id':'missing','request':request}).status_code in (404,422)
        assert client.post('/api/research/r08/flow',json={'media_id':'synthetic','request':{**request,'frame_times_s':[0,0]}}).status_code==422
        body={'media_id':'synthetic','request':request,'idempotency_key':'c'*32}
        response=client.post('/api/research/r08/flow',json=body)
        assert response.status_code==200;ident=response.json()['id'];base=f'/api/research/r08/flow/{ident}'
        assert client.post('/api/research/r08/flow',json=body).json()['id']==ident
        assert client.post('/api/research/r08/flow',json={**body,'request':{**request,'seeds':[{'x':.4,'y':.5}]}}).status_code==422
        deadline=time.monotonic()+5
        while client.get(base).json()['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        assert client.get(base).json()['status']=='complete'
        result=client.get(base+'/artifacts/result.json');assert result.status_code==200
        assert len(result.json()['frames'])==3
        assert client.get(base+'/artifacts/video.mp4').status_code==422
        assert client.get('/api/research/r08/flow').json()[0]['read_verification']=='integrity_only'
        assert client.post(base+'/cancel').json()['status']=='complete'
        verification=client.post(base+'/reverify',json={'media_id':'synthetic'})
        assert verification.status_code==200
        verification_url=f"/api/research/r08/flow-verifications/{verification.json()['id']}"
        deadline=time.monotonic()+5
        while client.get(verification_url).json()['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        checked=client.get(verification_url).json()
        assert checked['status']=='complete' and checked['verification']=='recomputed'
        assert checked['source_run_id']==ident
        assert client.get(base+'/artifacts/result.json').content==result.content
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        assert client.post('/api/research/r08/flow',json=body).json()['id']==ident
        assert client.get(base).json()['status']=='complete'
        assert client.get(base+'/artifacts/result.json').content==result.content
        assert len(client.get('/api/research/r08/flow').json())==1
        with video.open('ab') as handle:handle.write(b'changed')
        failed=client.post(base+'/reverify',json={'media_id':'synthetic'}).json()
        url=f"/api/research/r08/flow-verifications/{failed['id']}"
        deadline=time.monotonic()+5
        while client.get(url).json()['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        assert client.get(url).json()['status']=='failed'
        assert client.get(url).json()['verification'] is None
        assert client.get(base+'/artifacts/result.json').content==result.content
