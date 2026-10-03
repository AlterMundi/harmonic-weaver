import json
import time

import pytest

from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.sai_fourier import FourierService, Settings, calculate, run_frozen, verify


def config():
    return {'samples': 64, 'hz': 60, 'seeds': [7]}


def finish(service, job):
    deadline = time.monotonic() + 20
    while True:
        report = service.report(job['id'])
        if report['status'] not in ('queued', 'running'):
            assert report['status'] == 'complete', report
            service.processes[job['id']].wait(timeout=5)
            return service.artifact(job['id'], 'result.json').read_bytes()
        assert time.monotonic() < deadline
        time.sleep(.02)


def test_real_workers_repeat_restore_without_recompute_and_tamper_rejection(tmp_path):
    service = FourierService(tmp_path)
    try:
        a = service.start(config()); first = finish(service, a)
        b = service.start(config()); assert finish(service, b) == first
        restored = FourierService(tmp_path)
        try:
            assert restored.processes == {}
            assert restored.artifact(a['id'], 'result.json').read_bytes() == first
            report = json.loads(first)
            assert len(report['bank']['results']) == 3
            provenance = restored.report(a['id'])['code_provenance']
            assert 'harmonic_weaver.lab.models' in provenance['weaver']
            restored.folder(a['id']).joinpath('result.json').write_bytes(b'corrupted')
            with pytest.raises(ValueError, match='hash mismatch'):
                restored.artifact(a['id'], 'result.json')
        finally:
            restored.close()
    finally:
        service.close()


@pytest.mark.parametrize('changes', [
    {'samples': 63}, {'samples': 1201}, {'hz': 0}, {'seeds': [-1]},
    {'seeds': [7, 7]}, {'seeds': list(range(9))}, {'samples': 1200, 'seeds': list(range(5))},
])
def test_bounds_reject_before_execution(changes):
    with pytest.raises(ValueError):
        Settings.model_validate({**config(), **changes})


def test_frozen_support_binding_even_if_rehashed(tmp_path):
    atomic_json(tmp_path / 'request.json', config())
    run_frozen(tmp_path)
    result = json.loads((tmp_path / 'result.json').read_text())
    result['bank']['results'][0]['descriptors']['collective.residual']['total'] = 999
    atomic_json(tmp_path / 'result.json', result)
    manifest = json.loads((tmp_path / 'manifest.json').read_text())
    manifest['output']['sha256'] = sha256_file(tmp_path / 'result.json')
    atomic_json(tmp_path / 'manifest.json', manifest)
    with pytest.raises(ValueError, match='support differs'):
        verify(tmp_path)


def test_request_changes_during_calculation_are_failed_not_published(tmp_path, monkeypatch):
    import harmonic_weaver.lab.research.sai_fourier as wrapper
    atomic_json(tmp_path / 'request.json', config())
    def mutate(settings):
        value = calculate(settings)
        atomic_json(tmp_path / 'request.json', {**config(), 'hz': 30})
        return value
    monkeypatch.setattr(wrapper, 'calculate', mutate)
    with pytest.raises(ValueError, match='input changed'):
        run_frozen(tmp_path)
    assert json.loads((tmp_path / 'manifest.json').read_text())['status'] == 'failed'
    assert not (tmp_path / 'result.json').exists()


def test_owned_worker_can_be_cancelled_without_publication(tmp_path):
    service = FourierService(tmp_path)
    try:
        job = service.start({'samples': 1200, 'hz': 60, 'seeds': [7, 19, 41, 53]})
        report = service.cancel(job['id'])
        assert report['status'] == 'cancelled'
        assert service.processes[job['id']].poll() is not None
        with pytest.raises(ValueError):
            service.artifact(job['id'], 'result.json')
    finally:
        service.close()
