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


def test_paired_arm_selection_verifies_unselected_arm_too(tmp_path):
    from harmonic_weaver.lab.research.mechanism_run import run
    from test_mechanism_run import document
    folder = tmp_path/'pair'
    run(document(), {'resonators': {'sample_rate': 8000}}, folder)
    request = {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 1000,
               'grid_x': 4, 'grid_y': 4}
    excited = project(folder, {**request, 'arm': 'excited'})
    mapped = project(folder, {**request, 'arm': 'mapped'})
    assert excited['source_pair_manifest_sha256'] == mapped['source_pair_manifest_sha256']
    assert excited['window']['sample_count'] == mapped['window']['sample_count']
    assert excited['source_component_sha256'] != mapped['source_component_sha256']
    assert excited['window']['rms'] != mapped['window']['rms']
    (folder/'mapped/sum.wav').write_bytes(b'changed')
    with pytest.raises(ValueError): project(folder, {**request, 'arm': 'excited'})


def test_source_mutation_during_projection_is_rejected(tmp_path, monkeypatch):
    from harmonic_weaver.lab.research import membrane_pcm
    folder = tmp_path/'run'
    fixture(folder)
    original = membrane_pcm.FieldWindow.report
    def changed(self, x, y):
        result = original(self, x, y)
        with (folder/'input.json').open('ab') as handle: handle.write(b'changed')
        return result
    monkeypatch.setattr(membrane_pcm.FieldWindow, 'report', changed)
    with pytest.raises(ValueError):
        project(folder, {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 100})


def test_trajectory_single_pass_matches_individual_causal_windows(tmp_path):
    source = tmp_path/'source'
    fixture(source)
    settings = {'membrane': {'sample_rate': 8000}, 'start_sample': 200,
                'stop_sample_exclusive': 1000, 'grid_x': 5, 'grid_y': 4,
                'trajectory': {'window_samples': 300, 'hop_samples': 250}}
    result = project(source, settings)
    assert [f['stop_sample_exclusive'] for f in result['trajectory']] == [450, 700, 950, 1000]
    pcm, _ = sf.read(source/'sum.wav')
    model = Membrane(Settings(sample_rate=8000))
    q = model.render(pcm[:1000])['modal_displacement']
    x, y = np.meshgrid(np.linspace(0, 1, 5), np.linspace(0, 1, 4))
    for frame in result['trajectory']:
        stop = frame['stop_sample_exclusive']
        np.testing.assert_allclose(np.array(frame['rms']).ravel(), model.field_rms(q[max(0,stop-300):stop], x.ravel(), y.ravel()), atol=1e-18)
    alternate = project(source, {**settings, 'block_size': 317})
    assert result['trajectory'] == alternate['trajectory']
