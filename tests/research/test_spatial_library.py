import pytest
from harmonic_weaver.lab.media import VideoLibrary,VideoJob
from harmonic_weaver.lab.contracts import MotionFrame,PerceptionSettings
from harmonic_weaver.lab.research.spatial_adapter import from_library
from test_spatial_adapter import data


def test_completed_generation_inclusive_bounds_deep_copy_no_media_io(tmp_path):
    library=VideoLibrary(tmp_path);frames=[MotionFrame.model_validate(f) for f in data()['frames']]
    job=VideoJob('job',tmp_path/'nonexistent.mp4',PerceptionSettings(checkpoint='synthetic.pt'),status='ready',
        generation='generation-1',cache_key='a'*64,frames=frames,times=[0.,.2],duration_s=1.)
    library.jobs['job']=job
    request={'job_id':'job','start_s':0.,'end_s':.2,'person_id':data()['person_id'],'clock':data()['clock']}
    result=from_library(library,request)
    assert len(result['stream']['frames'])==2
    assert result['tracking_provenance']['generation']=='generation-1'
    assert 'path' not in result['tracking_provenance']
    frozen,_=library.spatial_segment('job',0.,.2);frozen[0].persons[0].joints[0].position[0]=99.
    assert job.frames[0].persons[0].joints[0].position[0]==1.4
    for start,end in ((.3,.4),(0.,2.),(0.,121.),(.2,.1)):
        with pytest.raises(ValueError):from_library(library,{**request,'start_s':start,'end_s':end})
    job.status='tracking'
    with pytest.raises(ValueError):from_library(library,request)
