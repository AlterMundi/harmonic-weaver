import pytest
from harmonic_weaver.lab.research.temporal_controls import compare_shifts


def test_shift_controls_repeat_and_pair_identical_support_across_gaps():
    args=([2,6],[2,6],[(0,4),(5,9)],[(0,4),(5,9)])
    result=compare_shifts(*args,offsets_s=[1,-1],tolerance_s=.1)
    assert result==compare_shifts(*args,offsets_s=[1,-1],tolerance_s=.1)
    assert result['common_support']==[(1,3),(6,8)]
    conditions=result['conditions']
    assert all(c['paired']['common_support']==result['common_support'] for c in conditions)
    assert all(c['paired']['support_duration_s']==4 for c in conditions)
    assert len(conditions[0]['paired']['matches'])==2
    assert all(not c['paired']['matches'] for c in conditions[1:])
    assert conditions[0]['available']['support_duration_s']==8


def test_empty_common_support_is_unknown_not_zero_score():
    result=compare_shifts([.5],[.5],[(0,1)],[(0,1)],offsets_s=[2])
    assert result['support_duration_s']==0
    assert all(c['paired']['precision'] is None and c['paired']['recall'] is None for c in result['conditions'])


@pytest.mark.parametrize('offsets',[[],[0],[1,1],[True],[float('nan')],[11],list(range(1,18))])
def test_invalid_controls_rejected(offsets):
    with pytest.raises(ValueError):compare_shifts([],[],[],[],offsets_s=offsets)


def test_combined_offset_rejected_without_optimization():
    with pytest.raises(ValueError,match='Combined'):compare_shifts([],[],[],[],offsets_s=[2],mark_offset_s=9)


def test_timing_sensitivity_samples_fixed_support_without_changing_nominal_match():
    from harmonic_weaver.lab.research.temporal_controls import timing_sensitivity
    args=([2,6],[2.2,6.2],[(0,4),(5,9)],[(0,4),(5,9)])
    result=timing_sensitivity(*args,half_width_s=.5,steps_per_side=2,tolerance_s=.1)
    assert result==timing_sensitivity(*args,half_width_s=.5,steps_per_side=2,tolerance_s=.1)
    assert result['sampled_offsets_s']==[-.5,-.25,0,.25,.5]
    assert result['common_support']==[(.5,3.5),(5.5,8.5)]
    assert all(row['paired']['common_support']==result['common_support'] for row in result['conditions'])
    assert [len(row['paired']['matches']) for row in result['conditions']]==[0,0,0,2,0]
    assert result['sampled_metric_ranges']['precision']=={'min':0,'max':1,'defined_conditions':5}
    assert 'best_offset' not in result


def test_timing_sensitivity_does_not_report_zero_for_absent_support():
    from harmonic_weaver.lab.research.temporal_controls import timing_sensitivity
    result=timing_sensitivity([.5],[.5],[(0,1)],[(0,1)],half_width_s=2)
    assert result['support_duration_s']==0
    assert result['sampled_metric_ranges']['recall']=={'min':None,'max':None,'defined_conditions':0}


@pytest.mark.parametrize('kwargs',[{'half_width_s':0},{'half_width_s':True},
    {'half_width_s':float('nan')},{'half_width_s':6},
    {'half_width_s':1,'steps_per_side':True},{'half_width_s':1,'steps_per_side':1.5},
    {'half_width_s':1,'steps_per_side':9},{'half_width_s':2,'mark_offset_s':9}])
def test_invalid_timing_sensitivity_rejected(kwargs):
    from harmonic_weaver.lab.research.temporal_controls import timing_sensitivity
    with pytest.raises(ValueError):timing_sensitivity([],[],[],[],**kwargs)
