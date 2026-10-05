import json
import pytest
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.research.membrane_worker import run_frozen
from harmonic_weaver.lab.research.membrane_run import verify
from test_resonator_artifacts import fixture


def test_worker_publication_and_no_rerun(tmp_path):
    source = tmp_path/'source'
    fixture(source)
    folder = tmp_path/'worker'
    folder.mkdir()
    atomic_json(folder/'source.json', {'directory': str(source)})
    atomic_json(folder/'request.json', {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 800})
    assert run_frozen(folder) == verify(folder)
    with pytest.raises(ValueError): run_frozen(folder)


def test_worker_failed_source_has_no_published_result(tmp_path):
    folder = tmp_path/'worker'
    folder.mkdir()
    atomic_json(folder/'source.json', {'directory': str(tmp_path/'missing')})
    atomic_json(folder/'request.json', {'stop_sample_exclusive': 800})
    with pytest.raises(ValueError): run_frozen(folder)
    manifest = json.loads((folder/'manifest.json').read_text())
    assert manifest['status'] == 'failed' and 'output' not in manifest
    assert not (folder/'result.json').exists()


def test_publication_rechecks_source_without_recomputing(tmp_path, monkeypatch):
    from harmonic_weaver.lab.research import membrane_run
    source = tmp_path/'source'
    fixture(source)
    folder = tmp_path/'worker'
    folder.mkdir()
    atomic_json(folder/'source.json', {'directory': str(source)})
    atomic_json(folder/'request.json', {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 800})
    original = membrane_run.project
    calls = []
    def mutated(*args):
        result = original(*args)
        calls.append(1)
        with (source/'sum.wav').open('ab') as handle: handle.write(b'changed')
        return result
    monkeypatch.setattr(membrane_run, 'project', mutated)
    with pytest.raises(ValueError): run_frozen(folder)
    assert calls == [1]
    assert json.loads((folder/'manifest.json').read_text())['status'] == 'failed'
    assert not (folder/'result.json').exists()
