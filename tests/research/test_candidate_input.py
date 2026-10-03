from unittest.mock import patch
import pytest
from harmonic_weaver.lab.research.candidate_input import CandidateRequest,candidate_snapshot


def test_adapter_keeps_units_invalidity_and_causal_candidate_timestamps():
    request=dict(evaluation_id='a'*32,run_index=0,signal_id='zone.speed',end_s=1,high=1,low=.2)
    doc={'rows':[{'time_s':0,'values':[0]},{'time_s':.03,'values':[2]},
                 {'time_s':.06,'values':None,'invalid_signals':{'zone.speed':'missing'}},
                 {'time_s':.09,'values':[2]}],
         'unit':'T/s','provenance':{'trace_sha256':'frozen'},'duplicate_control_holds_excluded':3}
    with patch('harmonic_weaver.lab.research.candidate_input.snapshot',return_value=doc) as read:
        result=candidate_snapshot(object(),request)
        assert read.call_args.args[1].signal_ids==['zone.speed']
    assert result['unit']=='T/s' and result['provenance']==doc['provenance']
    assert result['rows'][2]['invalid_signals']=={'zone.speed':'missing'}
    assert [e['time_s'] for e in result['candidates']['events']]==[.03]
    assert result['duplicate_control_holds_excluded']==3


def test_candidate_request_rejects_inverted_thresholds_and_segments():
    base=dict(evaluation_id='a'*32,run_index=0,signal_id='zone.speed',end_s=1,high=1,low=.2)
    for change in ({'low':2},{'end_s':121},{'high':float('nan')}):
        with pytest.raises(ValueError):CandidateRequest(**{**base,**change})
