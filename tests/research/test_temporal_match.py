import pytest
from harmonic_weaver.lab.research.temporal_match import compare_events


def test_one_candidate_cannot_explain_multiple_marks():
    result=compare_events([1,1.1],[1.08],[(0,2)],[(0,2)],tolerance_s=.2)
    assert len(result['matches'])==1
    assert result['matches'][0]['mark_index']==1
    assert result['precision']==1 and result['recall']==.5


def test_common_support_excludes_gaps_and_exclusive_endpoint():
    result=compare_events([1,2,3,4],[1,2,3,4],[(0,2),(3,5)],[(0,4)],tolerance_s=0)
    assert result['eligible_marks']==2 and result['excluded_marks']==2
    assert result['support_duration_s']==3
    assert len(result['matches'])==2


def test_declared_offset_shifts_marks_and_their_support():
    result=compare_events([1],[1.3],[(1,1.2)],[(1.3,1.5)],mark_offset_s=.3,tolerance_s=.01)
    assert len(result['matches'])==1 and result['matches'][0]['delta_s']==0
    assert result==compare_events([1],[1.3],[(1,1.2)],[(1.3,1.5)],mark_offset_s=.3,tolerance_s=.01)


def test_no_support_is_unknown_not_perfect_accuracy():
    result=compare_events([1],[3],[(0,2)],[(2,4)])
    assert result['precision'] is None and result['recall'] is None


@pytest.mark.parametrize('kwargs',[{'tolerance_s':float('nan')},{'mark_offset_s':11}])
def test_invalid_settings_are_rejected(kwargs):
    with pytest.raises(ValueError):compare_events([1],[1],[(0,2)],[(0,2)],**kwargs)


def test_tolerance_does_not_bridge_a_tracking_gap():
    result=compare_events([1.9],[2.2],[(0,1.95),(2.1,3)],[(0,1.95),(2.1,3)],tolerance_s=1)
    assert result['matches']==[] and result['precision']==0
