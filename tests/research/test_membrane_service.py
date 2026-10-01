import time
import pytest
from harmonic_weaver.lab.research.membrane_service import MembraneService
from test_resonator_artifacts import fixture


def wait_terminal(service, ident):
    deadline = time.monotonic()+15
    while time.monotonic() < deadline:
        report = service.report(ident)
        if report['status'] in ('complete', 'failed', 'cancelled', 'interrupted') and not report['worker_active']:
            return report
        time.sleep(.02)
    raise AssertionError('Owned worker did not terminate')


def test_real_worker_restore_download_and_closed_service(tmp_path):
    source = tmp_path/'source'
    fixture(source)
    service = MembraneService(tmp_path/'data')
    try:
        job = service.start(source, {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 800})
        assert wait_terminal(service, job['id'])['status'] == 'complete'
        first = service.artifact(job['id'], 'result.json').read_bytes()
        restored = MembraneService(tmp_path/'data')
        try:
            assert restored.list()[0]['status'] == 'complete'
            assert restored.artifact(job['id'], 'result.json').read_bytes() == first
            with pytest.raises(ValueError): restored.cancel(job['id'])
            with pytest.raises(ValueError): restored.artifact(job['id'], 'source.json')
        finally: restored.close()
        service.artifact(job['id'], 'result.json').write_bytes(b'changed')
        with pytest.raises(ValueError): service.artifact(job['id'], 'result.json')
    finally: service.close()
    with pytest.raises(ValueError): service.start(source, {'stop_sample_exclusive': 1})


def test_real_owned_worker_cancel_and_single_process_guard(tmp_path):
    source = tmp_path/'source'
    fixture(source)
    service = MembraneService(tmp_path/'data')
    try:
        job = service.start(source, {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 800})
        with pytest.raises(ValueError):
            service.start(source, {'stop_sample_exclusive': 800})
        report = service.cancel(job['id'])
        assert report['status'] == 'cancelled' and not report['worker_active']
        with pytest.raises(ValueError): service.artifact(job['id'], 'result.json')
    finally: service.close()
