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


def test_adjacent_support_intervals_do_not_create_an_artificial_gap():
    result=compare_events([.95],[1.05],[(0,1),(1,2)],[(0,2)],tolerance_s=.2)
    assert len(result['matches'])==1
    assert result['common_support']==[(0,2)]


def test_matching_objective_agrees_with_exhaustive_assignments():
    from itertools import combinations,permutations
    times=[.1,.4,.8]
    sets=[combo for count in range(4) for combo in combinations(times,count)]
    for marks in sets:
        for candidates in sets:
            best=(0,0.)
            for count in range(1,min(len(marks),len(candidates))+1):
                for subset in combinations(range(len(marks)),count):
                    for assignment in permutations(range(len(candidates)),count):
                        distances=[abs(marks[i]-candidates[j]) for i,j in zip(subset,assignment)]
                        if all(d<=.35 for d in distances):best=max(best,(count,-sum(distances)))
            result=compare_events(marks,candidates,[(0,1)],[(0,1)],tolerance_s=.35)
            assert len(result['matches'])==best[0]
            assert sum(abs(pair['delta_s']) for pair in result['matches'])==pytest.approx(-best[1])
