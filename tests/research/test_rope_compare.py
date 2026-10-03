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


def test_unidentifiable_reference_is_separate_from_missing_eligible_prediction():
    ref=annotation();ref['frames'].append({'frame_index':2,'time_s':.2,'state':'unidentifiable','causes':['occlusion']})
    candidate=annotation(frames=(0,))
    result=compare({'reference':ref,'candidate':candidate})
    coverage=result['coverage']
    assert coverage['eligible_reference_frames']==2
    assert coverage['reference_frames_without_visible_curve']==1
    assert coverage['eligible_reference_frames_without_candidate_curve']==1
    assert coverage['supported_fraction_of_eligible_reference']==.5
    assert [r['cause'] for r in result['rows']]==[None,'candidate_frame_missing','reference_has_no_visible_curve']
    unknown={**ref,'frames':[ref['frames'][-1]]}
    result=compare({'reference':unknown,'candidate':annotation(frames=())})
    assert result['coverage']['supported_fraction_of_eligible_reference'] is None


def test_endpoint_errors_never_swap_labels_or_score_missing_points_as_zero():
    ref=annotation();ref['frames'][0]['endpoints']={'a':{'x':0,'y':0},'b':{'x':1,'y':0}}
    ref['frames'][1]['endpoints']={'a':{'x':.2,'y':.1}}
    cand=annotation();cand['frames'][0]['endpoints']={'a':{'x':1,'y':0},'b':{'x':0,'y':0}}
    result=compare({'reference':ref,'candidate':cand})['endpoint_comparison']
    assert [r['error_distance_px'] for r in result['rows']]==[100,100,None]
    assert result['rows'][0]['error_x_px']==100 and result['rows'][1]['error_x_px']==-100
    assert result['coverage']['supported_endpoints']==2
    assert result['coverage']['missing_candidate_endpoints']==1
    assert result['coverage']['supported_fraction']==pytest.approx(2/3)
    only=compare({'reference':annotation(frames=()),'candidate':cand})['endpoint_comparison']
    assert only['coverage']['candidate_only_endpoints']==2
    assert only['coverage']['supported_fraction'] is None
