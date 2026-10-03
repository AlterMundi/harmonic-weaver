import json

import numpy as np
import pytest

from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.activation_bank import Settings, probe, run
from harmonic_weaver.lab.research.activation_artifacts import verify
from harmonic_weaver.lab.research.activation_shifts import inputs


def config():
    return {'medium': {'sample_rate': 8000}, 'excitation_span_s': .05, 'tail_s': .025,
            'event_count': 4, 'trace_stride': 32,
            'circular_shift_controls': [[0]*6, [100]*6, [0, 7, 11, 19, 23, 29]]}


def test_periodic_power_cross_spectrum_and_nondiscriminating_calendar():
    x = config(); report = probe(x)
    zero, shared, independent = report['circular_shift_controls']
    for name, original in report['conditions'].items():
        assert zero['conditions'][name]['metrics'] == original['metrics']
        assert zero['conditions'][name]['trace'] == original['trace']
        for control in (zero, shared, independent):
            c = control['conditions'][name]
            assert c['input_squared_norm'] == original['input_squared_norm']
            assert c['spectral_preservation']['power_max_relative_error'] < 1e-12
        assert shared['conditions'][name]['spectral_preservation']['cross_spectrum_max_relative_change'] < 1e-12
    # Quarter-period shift of uniform four-event grid produces exactly same input.
    assert shared['conditions']['rational']['spectral_preservation']['changed_input_samples'] == 0
    assert shared['conditions']['rational']['metrics'] == report['conditions']['rational']['metrics']
    assert independent['conditions']['random']['spectral_preservation']['cross_spectrum_max_relative_change'] > .1
    assert shared['conditions']['random']['metrics'] != report['conditions']['random']['metrics']


def test_shift_preserves_dc_and_per_voice_periodogram_on_odd_block():
    calendars, checks = inputs([0, 3, 19, 90], 127, [.2, .4], [5, 31])
    for weight, calendar in zip([.2, .4], calendars):
        a=np.zeros(127);a[[0, 3, 19, 90]]=weight
        b=np.zeros(127);b[calendar]=weight
        np.testing.assert_allclose(abs(np.fft.rfft(a)), abs(np.fft.rfft(b)), atol=1e-12)
        assert a.sum() == b.sum()
    assert checks['shared_shift'] is False


def test_optional_field_keeps_old_result_and_crossed_controls_validate(tmp_path):
    x=config(); legacy={k:v for k,v in x.items() if k!='circular_shift_controls'}
    assert 'circular_shift_controls' not in Settings.model_validate(legacy).model_dump()
    original=probe(legacy); changed=probe(x)
    assert original['conditions'] == changed['conditions']
    x.update(phase_controls=[[.1]*6], replicate_seeds=[18],
             medium_controls=[Settings.model_validate(x).medium.model_dump()])
    run(x,tmp_path/'run');assert verify(tmp_path/'run')['status']=='complete'


@pytest.mark.parametrize('shifts', [[[0]], [[400]*6], [[-1]*6]])
def test_bad_calendar_shapes_and_offsets_rejected(shifts):
    with pytest.raises(ValueError): Settings.model_validate({**config(),'circular_shift_controls':shifts})


def test_spectral_budget_rejected_before_rendering():
    with pytest.raises(ValueError,match='spectral checks'):
        Settings.model_validate({**config(),'excitation_span_s':5,'medium':{'sample_rate':48000},
                                'circular_shift_controls':[[1]*6]*4,'replicate_seeds':list(range(8))})


def test_shift_calendar_corruption_rejected_even_if_rehashed(tmp_path):
    run(config(),tmp_path/'run');folder=tmp_path/'run'
    result=json.loads((folder/'result.json').read_text())
    result['circular_shift_controls'][0]['conditions']['random']['voice_event_samples'][0][0]=1
    atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output_sha256']=sha256_file(folder/'result.json')
    atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='calendar differs'): verify(folder)
