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
        assert client.post('/api/research/r08/mask',json={'media_id':'local-video','read_id':job['id']}).status_code==422
        frame_job=client.post('/api/research/r08/reads',json={'media_id':'local-video','frame_index':2,'sha256':media.json()['media_sha256']}).json()
        deadline=time.monotonic()+5
        while client.get(f"/api/research/r08/reads/{frame_job['id']}").json()['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        candidates=client.post('/api/research/r08/mask',json={'media_id':'local-video','read_id':frame_job['id'],'settings':{'distance_rgb':442,'min_component_px':1}})
        assert candidates.status_code==200
        assert candidates.json()['frame_index']==2 and candidates.json()['time_s']==.2
        assert candidates.json()['candidate_components'][0]['area_px']==160*120
        request={k:candidates.json()[k] for k in ('media_sha256','width_px','height_px','frame_index','time_s','settings')}
        saved=client.post('/api/research/r08/masks',json={'media_id':'local-video','request':request})
        assert saved.status_code==200
        mask_id=saved.json()['id']
        assert client.post(f'/api/research/r08/masks/{mask_id}/reverify',json={'media_id':'local-video'}).json()==candidates.json()
        assert client.get(f'/api/research/r08/masks/{mask_id}/artifacts/frame.png').status_code==422
        path=client.post('/api/research/r08/path',json={'media_id':'local-video','mask_id':mask_id,'settings':{'component_id':1,'start':{'x':0,'y':0},'stop':{'x':1,'y':1}}})
        assert path.status_code==200 and path.json()['supported']
        assert path.json()['frame_index']==2 and path.json()['time_s']==.2
        assert client.post(f"/api/research/r08/paths/{path.json()['run_id']}/rebind",json={'media_id':'local-video'}).json()==path.json()


        assert client.get('/api/research/r08').json()==[]
        from copy import deepcopy
        origin={'segment_index':0,'path_run_id':path.json()['run_id'],'path_manifest_sha256':path.json()['path_manifest_sha256'],'relation':'exact'}
        assisted={'media_sha256':media.json()['media_sha256'],'width_px':160,'height_px':120,'frames':[{'frame_index':2,'time_s':.2,'state':'observed','visible_segments':[path.json()['points']],'curve_sources':[origin]}]}
        assert client.post('/api/research/r08',json={'media_id':'local-video','annotation':assisted}).status_code==200
        edited=deepcopy(assisted);edited['frames'][0]['visible_segments'][0][0]['x']=.01
        assert client.post('/api/research/r08',json={'media_id':'local-video','annotation':edited}).status_code==422
        edited['frames'][0]['curve_sources'][0]['relation']='edited'
        assert client.post('/api/research/r08',json={'media_id':'local-video','annotation':edited}).status_code==200
        wrong=deepcopy(assisted);wrong['frames'][0]['curve_sources'][0]['path_manifest_sha256']='0'*64
        assert client.post('/api/research/r08',json={'media_id':'local-video','annotation':wrong}).status_code==422


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
        comparison=client.post('/api/research/r08/compare',json={'reference_id':ident,'candidate_id':second.json()['id']})
        assert comparison.status_code==200
        compared=client.get(f"/api/research/r08/comparisons/{comparison.json()['id']}/artifacts/result.json")
        assert compared.status_code==200 and compared.json()['coverage']['reference_frames']==0
        assert client.post('/api/research/r08/probe',json={'media_id':str(video)}).status_code==404
        assert client.post('/api/research/r08/probe',json={'media_id':'local-video','path':str(video)}).status_code==422
        assert client.get(f'/api/research/r08/{ident}/artifacts/worker.log').status_code==422
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        assert len(client.get('/api/research/r08').json())==4
        assert len(client.get('/api/research/r08/comparisons').json())==1
        assert len(client.get('/api/research/r08/masks').json())==1
        assert client.get(f"/api/research/r08/comparisons/{comparison.json()['id']}/artifacts/worker.log").status_code==422
        assert client.get(f'/api/research/r08/{ident}/artifacts/annotation.json').json()['frames']==[]
        assert client.post(f'/api/research/r08/{ident}/rebind',json={'media_id':'local-video'}).status_code==200
        with video.open('ab') as handle:handle.write(b'changed')
        assert client.post(f'/api/research/r08/{ident}/rebind',json={'media_id':'local-video'}).status_code==422
    with TestClient(create_app(root),base_url='http://127.0.0.1') as client:
        assert len(client.get('/api/research/r08').json())==4
        assert client.post('/api/research/r08/probe',json={'media_id':'local-video'}).status_code==422
