import copy
import math
import pytest
from harmonic_weaver.lab.research.neuro_snr import calculate


def config():
    return {'sample_rate_hz':256, 'sample_count':256, 'start_index':0, 'stop_index':256,
        'remove_mean':False, 'signal':{'amplitude':2,'frequency_hz':8,'phase_rad':0,'dc_offset':0},
        'noise':{'amplitude':1,'frequency_hz':16,'phase_rad':0,'dc_offset':0}}


def test_known_power_ratio_repeatability_and_explicit_dc_policy():
    raw=config();before=copy.deepcopy(raw);r=calculate(raw)
    assert raw==before and r==calculate(raw)
    assert r['metrics']['signal_power']==pytest.approx(2)
    assert r['metrics']['noise_power']==pytest.approx(.5)
    assert r['metrics']['snr_db']==pytest.approx(10*math.log10(4))
    assert all(s['mixture']==s['signal']+s['noise'] for s in r['samples'])
    raw['signal']['dc_offset']=3
    assert calculate(raw)['metrics']['signal_power']==pytest.approx(11)
    raw['remove_mean']=True
    assert calculate(raw)['metrics']['signal_power']==pytest.approx(2)


def test_common_support_missing_excluded_window_and_no_interpolation():
    raw=config();raw.update(start_index=10,stop_index=17,missing_indices=[11,13],excluded_indices=[13,15])
    r=calculate(raw);assert r['used_indices']==[10,12,14,16]
    assert r['samples'][11]['signal'] is None and r['samples'][11]['mixture'] is None
    assert r['samples'][13]['explicitly_excluded']
    assert r['samples'][15]['signal'] is not None
    signal=[r['samples'][i]['signal'] for i in r['used_indices']]
    assert r['metrics']['signal_power']==pytest.approx(sum(x*x for x in signal)/4)


@pytest.mark.parametrize('sa,na,status',[(0,0,'both_zero'),(1,0,'noise_zero'),(0,1,'signal_zero')])
def test_zero_power_is_explicit_finite_json(sa,na,status):
    raw=config();raw['signal']['amplitude']=sa;raw['noise']['amplitude']=na
    r=calculate(raw);assert r['metrics']['status']==status and r['metrics']['snr_db'] is None


def test_insufficient_support_and_invalid_control_rejected():
    raw=config();raw.update(start_index=0,stop_index=2,missing_indices=[1])
    r=calculate(raw);assert r['metrics']['status']=='insufficient_support'
    assert r['metrics']['signal_power'] is None and r['metrics']['support_count']==1
    for edit in ('alias','duplicate','outside','window','nan','hardware'):
        raw=config()
        if edit=='alias':raw['signal']['frequency_hz']=128
        elif edit=='duplicate':raw['missing_indices']=[1,1]
        elif edit=='outside':raw['excluded_indices']=[256]
        elif edit=='window':raw['stop_index']=257
        elif edit=='nan':raw['signal']['amplitude']=float('nan')
        else:raw['device']='OpenBCI'
        with pytest.raises(ValueError):calculate(raw)
