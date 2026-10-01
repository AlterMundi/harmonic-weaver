from copy import deepcopy
import pytest
from harmonic_weaver.lab.research.excitation import prepare


def document(rows):return {'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=1,high=1,low=.2),
    'unit':'T/s','rows':[{'time_s':t,'value':v,'valid':v is not None} for t,v in rows],'provenance':{'fixture':'synthetic'}}


def test_threshold_held_initial_and_gap_recovery_do_not_repluck():
    doc=document([(0,2),(.03,2),(.06,0),(.09,2),(.12,2),(.15,None),(.18,2),(.21,0),(.24,2)])
    result=prepare(doc,{},sample_rate=8000,voices=6)
    assert [e['time_s'] for e in result['events']]==[.09,.24]
    assert len(result['events'][0]['voice_impulses'])==6
    assert all(e['sample_index']/8000>=e['time_s'] for e in result['events'])
    assert result==prepare(doc,{},sample_rate=8000,voices=6)


def test_positive_delta_consumes_refractory_and_has_no_held_delayed_event():
    doc=document([(0,0),(.03,1),(.06,2),(.09,2),(.12,2),(.15,2),(.18,2),(.21,2),(.24,2),(.27,3)])
    settings={'mode':'positive_delta','reference_scale':2,'gain':1}
    result=prepare(doc,settings,sample_rate=8000,voices=6)
    assert [e['time_s'] for e in result['events']]==[.03,.27]
    assert all(e['strength']==.5 for e in result['events'])
    prefix=deepcopy(doc);prefix['rows']=prefix['rows'][:5]
    assert prepare(prefix,settings,sample_rate=8000,voices=6)['events']==result['events'][:1]


def test_invalid_weights_units_and_segment_do_not_get_inferred():
    doc=document([(0,0),(.03,2)])
    with pytest.raises(ValueError,match='weight'):prepare(doc,{},sample_rate=8000,voices=7)
    with pytest.raises(ValueError,match='unit'):prepare({**doc,'unit':None},{},sample_rate=8000,voices=6)
    doc['rows'][1]['time_s']=2
    with pytest.raises(ValueError,match='outside'):prepare(doc,{},sample_rate=8000,voices=6)
