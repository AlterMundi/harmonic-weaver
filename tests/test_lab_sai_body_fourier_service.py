from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from harmonic_weaver.lab.contracts import Preset
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.research.sai_body_fourier import Settings, SourceRequest, freeze, BodyFourierService, body_bridge


def settings():
    preset=Preset(id="synthetic_body_fourier");preset.algorithm.id='relational';preset.response.pluck_enabled=False
    return Settings(channels=[[7,0],[7,1],[9,0],[9,1]],sample_hz=60.,scale=.26,
        scale_unit='frame_height',scale_provenance='explicit synthetic torso',min_samples=8,
        seeds=[7],preset=preset)


class Library:
    def __init__(self):
        self.frames=body_bridge().synthetic_frames({'sample_hz':60.,'epochs':[{'kind':'coupled','stream_id':'epoch','samples':32}]})
    def spatial_segment(self,job_id,start_s,end_s):
        assert job_id=='job'
        return [f.model_copy(deep=True) for f in self.frames],{'generation':'synthetic','verification':'completed_in_memory_generation'}


def request():return SourceRequest(job_id='job',person_id='athlete',start_s=0.,end_s=1.,settings=settings())


def test_freeze_keeps_private_identity_and_reports_invalid_rows_without_filling():
    library=Library();next(p for p in library.frames[15].persons if p.person_id=='athlete').joints[7].state='held'
    req,document,support=freeze(library,request())
    assert support['input_frames']==32 and support['excluded_frames']==1
    assert support['exclusion_counts']=={'selected_joint_invalid':1}
    variant=request().model_copy(update={'settings':settings().model_copy(update={'min_samples':64})})
    _,_,short=freeze(library,variant)
    assert short['short_block_lengths']==[15,16] and short['longest_short_block']==16
    before=deepcopy(document['frames'][0])
    library.frames[0].persons[0].joints[7].position[0]+=1
    assert document['frames'][0]==before


def test_worker_repeat_restart_and_integrity(tmp_path):
    service=BodyFourierService(tmp_path);library=Library()
    first=service.start(library,request())
    assert service.processes[first['id']].wait(timeout=30)==0
    a=json.loads(service.artifact(first['id'],'result.json').read_text())
    second=service.start(library,request())
    assert service.processes[second['id']].wait(timeout=30)==0
    b=json.loads(service.artifact(second['id'],'result.json').read_text())
    assert a==b and a['preparation']['retained_frames']==32
    restored=BodyFourierService(tmp_path)
    assert all(job['status']=='complete' for job in restored.list())
    path=restored.artifact(first['id'],'input.json');path.write_text('{}')
    with pytest.raises(ValueError,match='changed'):restored.artifact(first['id'],'result.json')
    with pytest.raises(ValueError):restored.artifact(second['id'],'../input.json')
    service.close();restored.close()


def test_prepare_api_does_not_run_workers_or_change_runtime(tmp_path):
    runtime=SimpleNamespace(library=Library(),start=lambda:None,close=lambda:None,snapshot=lambda:{'marker':'unchanged'})
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        before=client.get('/api/state').json()
        r=client.post('/api/research/sai-body-fourier/prepare',json=request().model_dump())
        assert r.status_code==200,r.text
        assert r.json()['preparation']['retained_frames']==32
        assert client.get('/api/research/sai-body-fourier').json()==[]
        assert client.get('/api/state').json()==before
        assert client.post('/api/research/sai-body-fourier/settings',json=settings().model_dump()).status_code==200
        bad=settings().model_dump();bad['scale']=None
        assert client.post('/api/research/sai-body-fourier/settings',json=bad).status_code==422


def test_no_scale_inference_bad_sampling_and_baseline_rejected():
    for key,value in [('scale',None),('scale_provenance',''),('sample_hz',0.),('channels',[[7,2]])]:
        with pytest.raises(ValueError):Settings.model_validate({**settings().model_dump(),key:value})
    bad=settings().model_dump();bad['preset']['algorithm']['id']='baseline'
    with pytest.raises(ValueError):Settings.model_validate(bad)
    bad=settings().model_dump();bad['preset']['response']['pluck_enabled']=True
    with pytest.raises(ValueError):Settings.model_validate(bad)


def test_cancel_only_owned_worker_and_reject_concurrent_start(tmp_path,monkeypatch):
    import subprocess,sys
    import harmonic_weaver.lab.research.coincidence_service as base
    real_popen=subprocess.Popen
    def sleeping_worker(command,**kwargs):
        return real_popen([sys.executable,'-c','import time; time.sleep(30)'],**kwargs)
    monkeypatch.setattr(base.subprocess,'Popen',sleeping_worker)
    service=BodyFourierService(tmp_path);library=Library()
    job=service.start(library,request());process=service.processes[job['id']]
    assert process.poll() is None
    with pytest.raises(ValueError,match='already active'):service.start(library,request())
    assert service.cancel(job['id'])['status']=='cancelled'
    assert process.poll() is not None
    restored=BodyFourierService(tmp_path)
    assert restored.list()[0]['status']=='cancelled'
    service.close();restored.close()


def test_short_block_summary_preserves_metadata_and_grid_boundaries():
    from harmonic_weaver.lab.research.sai_body_fourier import short_block_summary
    rows=[{'reason':'short_block','input_index':i,'source_id':'source','stream_id':'stream','person_id':'person'} for i in range(8)]
    support={'boundaries':[{'input_index':4,'reason':'sampling_grid_drift'}],'exclusions':rows}
    result=short_block_summary(support)
    assert result['short_block_lengths']==[4,4] and result['longest_short_block']==4
    assert 'short_block_lengths' not in support
