import pytest
from harmonic_weaver.lab.research.rope_compare import compare


def annotation(y=0,frames=(0,1)):
    return {'media_sha256':'a'*64,'width_px':100,'height_px':200,'frames':[
        {'frame_index':i,'time_s':i*.1,'state':'observed','visible_segments':[[{'x':0,'y':y},{'x':1,'y':y}]]} for i in frames]}


def test_curve_metric_shift_coverage_and_no_occlusion_bridge():
    ref=annotation();candidate=annotation(.2,(0,))
    result=compare({'reference':ref,'candidate':candidate})
    assert result['rows'][0]['sampled_symmetric_mean_distance_px']==40
    assert result['rows'][0]['sampled_hausdorff_px']==40
    assert not result['rows'][1]['supported'] and result['rows'][1]['sampled_hausdorff_px'] is None
    assert result['coverage']['unsupported_reference_frames']==1
    partial=annotation(frames=(0,));partial['frames'][0].update(state='partial',causes=['occlusion'],visible_segments=[
        [{'x':0,'y':0},{'x':.2,'y':0}],[{'x':.8,'y':0},{'x':1,'y':0}]])
    same=compare({'reference':partial,'candidate':partial})
    assert same['rows'][0]['sampled_hausdorff_px']==0
    missing=compare({'reference':ref,'candidate':annotation(frames=())})
    assert missing['coverage']['supported_frames']==0
    assert all(r['sampled_hausdorff_px'] is None for r in missing['rows'])


def test_curve_compare_rejects_wrong_source_dimensions_clock_and_budget():
    ref=annotation();candidate=annotation()
    for field,value in [('media_sha256','b'*64),('width_px',101)]:
        with pytest.raises(ValueError):compare({'reference':ref,'candidate':{**candidate,field:value}})
    candidate['frames'][0]['time_s']=.01
    with pytest.raises(ValueError):compare({'reference':ref,'candidate':candidate})
    with pytest.raises(ValueError):compare({'reference':ref,'candidate':ref,'samples_per_segment':True})
    crowded=annotation(frames=(0,));crowded['frames'][0].update(state='partial',causes=['occlusion'])
    crowded['frames'][0]['visible_segments']*=64
    with pytest.raises(ValueError,match='budget'):compare({'reference':crowded,'candidate':crowded,'samples_per_segment':64})
