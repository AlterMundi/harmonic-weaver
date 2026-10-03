import json
import subprocess
import time
from types import SimpleNamespace
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.media import VideoLibrary


def test_actual_http_benchmark_download_and_restart(tmp_path):
    video=tmp_path/'test.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    root=tmp_path/'data';library=VideoLibrary(root/'library')
    library.index.write_text(json.dumps({'video':{'id':'video','name':video.name,'path':str(video)}}))
    runtime=SimpleNamespace(library=VideoLibrary(root/'library'),start=lambda:None,close=lambda:None)
    url='/api/research/r08/flow-benchmarks'
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        media=client.post('/api/research/r08/probe',json={'media_id':'video'}).json()
        annotation={'media_sha256':media['media_sha256'],'width_px':160,'height_px':120,
            'frames':[{'frame_index':1,'time_s':.1,'state':'observed',
                'visible_segments':[[{'x':.2,'y':.2},{'x':.5,'y':.5}]],'endpoints':{'a':{'x':.5,'y':.5}}}]}
        ref=client.post('/api/research/r08',json={'media_id':'video','annotation':annotation}).json()['id']
        flow=client.post('/api/research/r08/flow',json={'media_id':'video','request':{
            'media_sha256':media['media_sha256'],'width_px':160,'height_px':120,'start_frame_index':0,
            'frame_times_s':media['frame_times_s'][:3],'seeds':[{'x':.5,'y':.5}]}}).json()['id']
        deadline=time.monotonic()+10
        while client.get(f'/api/research/r08/flow/{flow}').json()['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        body={'reference_id':ref,'flow_id':flow,'endpoint_seeds':{'a':0}}
        response=client.post(url,json=body);assert response.status_code==200
        ident=response.json()['id'];assert response.json()['source_resolution']=='verified_local_artifacts_at_creation'
        result=client.get(f'{url}/{ident}/artifacts/result.json')
        assert result.status_code==200 and 'attachment' in result.headers['content-disposition']
        assert result.json()['coverage']['eligible_endpoints']==1
        for invalid in ({**body,'endpoint_seeds':{'a':True}},{**body,'flow_id':'missing'},{**body,'path':'private'}):
            assert client.post(url,json=invalid).status_code==422
        assert client.get(f'{url}/{ident}/artifacts/video.mp4').status_code==422
        other=client.post(url,json=body).json()['id']
        paired_url='/api/research/r08/flow-paired'
        paired=client.post(paired_url,json={'conditions':{'original':ident,'repeat':other}})
        assert paired.status_code==200
        paired_id=paired.json()['id']
        paired_result=client.get(f'{paired_url}/{paired_id}/artifacts/result.json')
        assert paired_result.status_code==200
        assert paired_result.json()['common_eligible_endpoints']==1
        assert client.post(paired_url,json={'conditions':{'a':ident,'b':ident}}).status_code==422
        assert client.get(f'{paired_url}/{paired_id}/artifacts/video.mp4').status_code==422

    with TestClient(create_app(root),base_url='http://127.0.0.1') as client:
        assert client.get(paired_url).json()[0]['read_verification']=='recomputed'
        assert client.get(f'{paired_url}/{paired_id}/artifacts/result.json').content==paired_result.content
        assert client.get(url).json()[0]['read_verification']=='recomputed'
        assert client.get(f'{url}/{ident}/artifacts/result.json').content==result.content
