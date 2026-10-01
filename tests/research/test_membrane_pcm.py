import numpy as np
import pytest
import soundfile as sf
from harmonic_weaver.lab.research.membrane import Membrane, Settings
from harmonic_weaver.lab.research.membrane_pcm import project
from test_resonator_artifacts import fixture


def test_verified_mix_causal_history_partition_and_repeat(tmp_path):
    folder = tmp_path/'run'
    fixture(folder)
    request = {'membrane': {'sample_rate': 8000}, 'start_sample': 200,
               'stop_sample_exclusive': 1300, 'grid_x': 5, 'grid_y': 4}
    report = project(folder, request)
    assert report == project(folder, request)
    other = project(folder, {**request, 'block_size': 317})
    np.testing.assert_allclose(report['window']['rms'], other['window']['rms'], rtol=1e-12, atol=1e-18)
    pcm, _ = sf.read(folder/'sum.wav')
    model = Membrane(Settings(sample_rate=8000))
    q = model.render(pcm[:1300])['modal_displacement'][200:]
    x, y = np.meshgrid(np.linspace(0, 1, 5), np.linspace(0, 1, 4))
    np.testing.assert_allclose(np.array(report['window']['rms']).ravel(), model.field_rms(q, x.ravel(), y.ravel()), rtol=1e-12, atol=1e-18)
    assert report['window']['sample_count'] == 1100
    assert report['history_start_sample'] == 0


def test_invalid_clock_window_and_tampering_rejected(tmp_path):
    folder = tmp_path/'run'
    fixture(folder)
    for request in ({'stop_sample_exclusive': 100},
                    {'membrane': {'sample_rate': 8000}, 'start_sample': 100, 'stop_sample_exclusive': 100},
                    {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 1000000}):
        with pytest.raises(ValueError): project(folder, request)
    with (folder/'sum.wav').open('ab') as handle: handle.write(b'changed')
    with pytest.raises(ValueError): project(folder, {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 100})
