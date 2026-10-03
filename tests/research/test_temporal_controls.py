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
