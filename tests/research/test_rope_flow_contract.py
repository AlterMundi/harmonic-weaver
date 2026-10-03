from copy import deepcopy
import numpy as np
import pytest
from harmonic_weaver.lab.research.rope_flow import RopeFlow
from harmonic_weaver.lab.research.rope_flow_run import Request
from harmonic_weaver.lab.research.rope_flow_contract import validate_frames


def evidence():
    request=Request.model_validate({'media_sha256':'a'*64,'width_px':160,'height_px':120,
        'start_frame_index':0,'frame_times_s':[0,.1,.2],'seeds':[{'x':.5,'y':.5}]})
    image=np.zeros((120,160),dtype=np.uint8);flow=RopeFlow()
    frames=[flow.feed(image,0,0,seeds=[{'x':.5,'y':.5}]),flow.feed(image,1,.1),flow.feed(image,2,.2)]
    return request,frames


def test_structural_support_without_resurrection_or_invented_points():
    request,frames=evidence();validate_frames(frames,request)
    mutations=[]
    bad=deepcopy(frames);bad[1]['rows'][0]['point']={'x':.5,'y':.5};mutations.append(bad)
    bad=deepcopy(frames);bad[0]['rows']*=2;mutations.append(bad)
    bad=deepcopy(frames);bad[2]['rows']=deepcopy(frames[0]['rows']);bad[2]['status']='seeded';mutations.append(bad)
    bad=deepcopy(frames);bad[0]['rows'][0]['seed_index']=True;mutations.append(bad)
    bad=deepcopy(frames);bad[0]['rows'][0]['point']['x']=1.1;mutations.append(bad)
    bad=deepcopy(frames);bad[0]['rows'][0]['point']['x']=1;mutations.append(bad)
    bad=deepcopy(frames);bad[0]['rows'][0]['point']['x']=.4;mutations.append(bad)
    bad=deepcopy(frames);bad[1]['status']='reset';bad[1]['rows'][0]['cause']='source_gap_or_dimensions_changed';mutations.append(bad)
    bad=deepcopy(frames);bad[1]['unexpected']=True;mutations.append(bad)
    for bad in mutations:
        with pytest.raises(ValueError):validate_frames(bad,request)
