import pytest
from harmonic_weaver.lab.research.event_candidates import extract_candidates


def run(values,**kwargs):
    return extract_candidates([{'time_s':i*.05,'value':v} for i,v in enumerate(values)],high=1,low=.2,**kwargs)


def test_held_high_is_not_repeated_and_initial_high_is_not_activation():
    assert run([2,2,2])['events']==[]
    result=run([0,2,2,2])
    assert [e['index'] for e in result['events']]==[1]


def test_refractory_suppression_does_not_emit_a_delayed_held_event():
    assert [e['index'] for e in run([0,2,0,2,2,2,2])['events']]==[1]
    assert [e['index'] for e in run([0,2,0,2,2,2,0,2])['events']]==[1,7]


def test_missing_and_gap_require_fresh_low_before_activation():
    result=run([0,2,None,2,0,2])
    assert [e['index'] for e in result['events']]==[1,5]
    rows=[{'time_s':0,'value':0},{'time_s':1,'value':2},{'time_s':1.05,'value':0},{'time_s':1.1,'value':2}]
    result=extract_candidates(rows,high=1,low=.2)
    assert [e['index'] for e in result['events']]==[3]
    assert result['resets'][0]['reason']=='tracking_gap'


def test_future_append_preserves_emitted_prefix():
    prefix=run([0,2,2,0])
    longer=run([0,2,2,0,2,0,2,2])
    assert [e for e in longer['events'] if e['index']<4]==prefix['events']


def test_bad_timestamps_and_settings_rejected():
    with pytest.raises(ValueError):extract_candidates([{'time_s':1,'value':0},{'time_s':0,'value':2}],high=1,low=0)
    with pytest.raises(ValueError):run([0],max_gap_s=0)
