from copy import deepcopy
import pytest
from harmonic_weaver.lab.research.spatial_observations import Stream


def data():
    return {'source_id':'camera-a','subject_slot':'slot-1','provider':'monocular_3d','dimensions':3,
        'coordinate_frame':'camera','units':'model_units',
        'clock':{'source_clock':'pts','common_clock':'session','offset_s':.2,'rate':1.001,'uncertainty_s':.01,'method':'declared_assumption'},
        'frames':[{'index':0,'source_time_s':0.,'points':[{'label':'hand','state':'inferred','position':[.1,.2,.3]}]},
                  {'index':2,'source_time_s':.1,'points':[{'label':'hand','state':'missing','cause':'occluded'}]}]}


def test_scale_inference_clock_and_missing_remain_explicit():
    stream=Stream.model_validate(data())
    assert stream.clock.common_time(10)==pytest.approx(10.21)
    assert stream.frames[1].points[0].position is None
    assert Stream.model_validate_json(stream.model_dump_json())==stream


def test_semantic_errors_are_rejected():
    patches=[]
    for key,value in [('units','metres'),('provider','calibrated_multiview'),('dimensions',2)]:
        item=data();item[key]=value;patches.append(item)
    item=data();item['frames'][0]['points'][0]['state']='observed';patches.append(item)
    item=data();item['frames'][1]['source_time_s']=0.;patches.append(item)
    item=data();item['clock']['method']='measured_sync';patches.append(item)
    item=data();item['frames'][1]['points'][0]['position']=[0.,0.,0.];patches.append(item)
    item=data();item['frames'][0]['points'][0]['position'][0]=float('nan');patches.append(item)
    for item in patches:
        with pytest.raises(ValueError):Stream.model_validate(item)
