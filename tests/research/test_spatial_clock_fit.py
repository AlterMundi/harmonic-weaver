import pytest
from harmonic_weaver.lab.research.spatial_clock_fit import fit


def data():
    return {'source_clock':'camera','common_clock':'session','evidence_id':'synthetic-flashes',
        'anchor_uncertainty_s':.01,'anchors':[{'source_time_s':t,'common_time_s':2+1.001*t} for t in (0,10,20)]}


def test_known_offset_drift_repeatability_and_residual_envelope():
    body=data();result=fit(body)
    assert result==fit(body)
    assert result['clock']['offset_s']==pytest.approx(2)
    assert result['clock']['rate']==pytest.approx(1.001)
    assert result['clock']['uncertainty_s']==pytest.approx(.01)
    assert result['source_interval_s']==[0,20]
    body['anchors'][1]['common_time_s']+=.03
    noisy=fit(body)
    assert noisy['max_abs_residual_s']==pytest.approx(.02)
    assert noisy['clock']['uncertainty_s']==pytest.approx(.03)


def test_clock_fit_rejects_missing_evidence_duplicate_and_invalid_rates():
    for change in ({'evidence_id':''},{'anchors':data()['anchors'][:2]},
                   {'anchors':[{'source_time_s':0,'common_time_s':i} for i in range(3)]},
                   {'anchors':[{'source_time_s':i*1e155,'common_time_s':i*1e155} for i in range(3)]},
                   {'anchors':[{'source_time_s':i,'common_time_s':3*i} for i in range(3)]}):
        with pytest.raises(ValueError):fit({**data(),**change})


def test_reserved_anchors_do_not_change_fit_or_uncertainty():
    body=data();original=fit(body)
    body['validation_anchors']=[{'source_time_s':5,'common_time_s':7.105},{'source_time_s':30,'common_time_s':32.23}]
    result=fit(body)
    assert result['clock']==original['clock']
    assert result['validation']['count']==2
    assert result['validation']['max_abs_residual_s']==pytest.approx(.2)
    assert [r['extrapolated'] for r in result['validation']['rows']]==[False,True]
    body['validation_anchors']=[body['anchors'][0]]
    with pytest.raises(ValueError,match='separate'):fit(body)
