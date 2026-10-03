import pytest
from harmonic_weaver.lab.research.spatial_service import SpatialService
from test_spatial_adapter import data


def test_declared_receipt_restart_request_binding_and_failed_attempt(tmp_path,monkeypatch):
    service=SpatialService(tmp_path);body={'conversion':data(),'idempotency_key':'a'*32}
    saved=service.start(body);restored=SpatialService(tmp_path)
    assert restored.start(body)['id']==saved['id'] and len(restored.list())==1
    with pytest.raises(ValueError,match='different request'):restored.start({**body,'conversion':{**data(),'person_id':'absent'}})
    import harmonic_weaver.lab.research.spatial_service as module
    def failed(*args):raise ValueError('injected failure')
    monkeypatch.setattr(module,'run',failed)
    with pytest.raises(ValueError,match='injected'):service.start({**body,'idempotency_key':'b'*32})
    with pytest.raises(ValueError,match='unavailable'):restored.start({**body,'idempotency_key':'b'*32})
    assert len(service.list())==1


def test_library_receipt_recovers_without_reopening_source(tmp_path):
    from harmonic_weaver.lab.media import VideoLibrary,VideoJob
    from harmonic_weaver.lab.contracts import MotionFrame,PerceptionSettings
    library=VideoLibrary(tmp_path/'library');original=data()
    library.jobs['job']=VideoJob('job',tmp_path/'missing.mp4',PerceptionSettings(checkpoint='synthetic.pt'),status='ready',generation='gen',cache_key='a'*64,frames=[MotionFrame.model_validate(f) for f in original['frames']],times=[0.,.2],duration_s=1.)
    body={'job_id':'job','start_s':0.,'end_s':.2,'person_id':original['person_id'],'clock':original['clock'],'expected_generation':'gen','idempotency_key':'c'*32}
    service=SpatialService(tmp_path);saved=service.from_source(library,body)
    library.jobs.clear()
    assert SpatialService(tmp_path).from_source(library,body)['id']==saved['id']
    with pytest.raises(ValueError,match='different request'):service.from_source(library,{**body,'expected_generation':'other'})
