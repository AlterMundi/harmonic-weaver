from copy import deepcopy
import pytest
from harmonic_weaver.lab.research.spatial_adapter import convert


def data():
    frames=[{'source_id':'video','stream_id':'run','sequence':i,'source_time_s':i*.1,
        'available_monotonic_s':10.+i,'timestamp_origin':'pts','width':1920,'height':1080,
        'persons':[{'person_id':'slot-1-generation-2','joints':[{'index':0,'position':[1.4,.3],'confidence':.8,'state':'observed'},
            {'index':1,'position':[.4,.5],'confidence':.6,'state':'held'},
            {'index':2,'position':[.7,.6],'confidence':.1,'state':'missing'}]}] if i==0 else []} for i in (0,2)]
    return {'frames':frames,'person_id':'slot-1-generation-2','clock':{'source_clock':'pts','common_clock':'session','rate':1.,'offset_s':0.,'uncertainty_s':.02,'method':'declared_assumption'}}


def test_original_units_hold_missing_and_gaps():
    original=data();result=convert(original);stream=result['stream']
    assert stream['units']=='frame_height' and stream['frames'][0]['points'][0]['position']==[1.4,.3]
    assert stream['frames'][0]['points'][1]['state']=='held'
    assert stream['frames'][0]['points'][2]['position'] is None
    assert stream['frames'][0]['points'][3]['cause']=='joint_not_present'
    assert stream['frames'][1]['index']==2
    assert all(p['cause']=='person_slot_absent' for p in stream['frames'][1]['points'])
    assert original==data() and convert(original)==result


def test_mixed_source_geometry_clock_or_3d_rejected():
    for key,value in [('source_id','other'),('stream_id','other'),('width',1280),('timestamp_origin','index_fps'),('dimensions',3)]:
        item=deepcopy(data());item['frames'][1][key]=value
        with pytest.raises(ValueError):convert(item)
