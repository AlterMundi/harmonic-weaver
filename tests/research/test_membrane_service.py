import time
import os
import subprocess
import sys
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


def test_real_death_after_promotion_restores_interrupted_not_downloadable(tmp_path):
    from harmonic_weaver.lab.cache import atomic_json, sha256_file
    source = tmp_path/'source'
    fixture(source)
    service = MembraneService(tmp_path/'data')
    ident = 'a'*32
    folder = service.root/ident
    folder.mkdir()
    atomic_json(folder/'source.json', {'directory': str(source)})
    atomic_json(folder/'request.json', {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 800})
    # Instrument only this child: pause immediately after the real atomic
    # promotion, keeping the actual worker flock held until killed.
    script = '''
import sys,time
from pathlib import Path
from harmonic_weaver.lab.research.membrane_worker import run_frozen
root=Path(sys.argv[1]); original=Path.replace
def held(self,target):
    value=original(self,target)
    if Path(target)==root/'result.json':
        (root/'promoted.marker').write_text('ready')
        time.sleep(30)
    return value
Path.replace=held
run_frozen(root)
'''
    process = subprocess.Popen([sys.executable, '-c', script, str(folder)], env=dict(os.environ),
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic()+15
        while not (folder/'promoted.marker').exists():
            assert process.poll() is None, process.stderr.read().decode()
            assert time.monotonic() < deadline
            time.sleep(.02)
        assert service.report(ident)['status'] == 'running'
        before = sha256_file(folder/'result.json')
        with pytest.raises(ValueError): service.artifact(ident, 'result.json')
        process.kill()
        process.wait(timeout=5)
        assert service.report(ident)['status'] == 'interrupted'
        assert sha256_file(folder/'result.json') == before
        with pytest.raises(ValueError): service.artifact(ident, 'result.json')
        assert service.artifact(ident, 'manifest.json').is_file()
    finally:
        if process.poll() is None: process.kill(); process.wait(timeout=5)
        process.stderr.close()
        service.close()


def test_invalid_source_and_clock_never_enqueue(tmp_path):
    source = tmp_path/'source'
    fixture(source)
    service = MembraneService(tmp_path/'data')
    try:
        for request in ({'stop_sample_exclusive': 100},
                        {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 99999},
                        {'arm': 'mapped', 'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 100}):
            with pytest.raises(ValueError): service.start(source, request)
        assert service.list() == [] and not list(service.root.iterdir())
    finally: service.close()


def test_cancel_actual_running_calculation_preserves_inputs(tmp_path):
    from harmonic_weaver.lab.cache import sha256_file
    from harmonic_weaver.lab.research.resonator_run import run
    from test_mechanism_run import document
    source = tmp_path/'source'
    run(document(), {'resonators': {'sample_rate': 8000}, 'render': {'tail_s': 10}}, source)
    service = MembraneService(tmp_path/'data')
    try:
        job = service.start(source, {'membrane': {'sample_rate': 8000, 'modes_x': 16, 'modes_y': 16},
                                     'stop_sample_exclusive': 80000})
        ident = job['id']
        deadline = time.monotonic()+15
        while service.report(ident)['status'] == 'queued':
            assert time.monotonic() < deadline
            time.sleep(.01)
        assert service.report(ident)['status'] == 'running'
        before = {name: sha256_file(service.folder(ident)/name) for name in ('request.json','source.json')}
        report = service.cancel(ident)
        assert report['status'] == 'cancelled' and not report['worker_active']
        for name, digest in before.items(): assert sha256_file(service.folder(ident)/name) == digest
        with pytest.raises(ValueError): service.artifact(ident, 'result.json')
        assert service.artifact(ident, 'manifest.json').is_file()
    finally: service.close()
