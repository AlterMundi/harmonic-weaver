"""R04-specific failure gates, including a killed real writer after computation."""
import fcntl
import json
import subprocess
import sys
import time
from uuid import uuid4
import pytest
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.research import relational_worker
from harmonic_weaver.lab.research.relational_service import RelationalService


@pytest.mark.parametrize('mutation',['request','request_symlink','result','manifest_symlink'])
def test_changed_inputs_or_output_cannot_commit(tmp_path,monkeypatch,mutation):
    atomic_json(tmp_path/'request.json',{'samples':10})
    original=relational_worker.run
    def mutate(settings,folder):
        original(settings,folder)
        if mutation=='request':atomic_json(tmp_path/'request.json',{'samples':11})
        elif mutation=='request_symlink':
            backup=tmp_path/'copy.json';backup.write_bytes((tmp_path/'request.json').read_bytes())
            (tmp_path/'request.json').unlink();(tmp_path/'request.json').symlink_to(backup)
        elif mutation=='result':(folder/'result.json').write_text('{}')
        else:
            backup=folder/'copy.json';backup.write_bytes((folder/'manifest.json').read_bytes())
            (folder/'manifest.json').unlink();(folder/'manifest.json').symlink_to(backup)
    monkeypatch.setattr(relational_worker,'run',mutate)
    with pytest.raises(ValueError):relational_worker.run_frozen(tmp_path)
    report=json.loads((tmp_path/'manifest.json').read_text())
    assert report['status']=='failed' and 'output' not in report
    assert not (tmp_path/'result.json').exists()


def test_held_lock_and_bad_settings_never_create_complete_result(tmp_path):
    atomic_json(tmp_path/'request.json',{'samples':1})
    with (tmp_path/'worker.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='active'):relational_worker.run_frozen(tmp_path)
        assert not (tmp_path/'manifest.json').exists()
    with pytest.raises(ValueError):relational_worker.run_frozen(tmp_path)
    assert json.loads((tmp_path/'manifest.json').read_text())['status']=='failed'
    assert not (tmp_path/'result.json').exists()


def test_real_writer_crash_after_internal_result_restores_interrupted(tmp_path):
    service=RelationalService(tmp_path);ident=uuid4().hex;folder=service.root/ident;folder.mkdir()
    atomic_json(folder/'request.json',{'samples':10})
    program="""import sys,time
from pathlib import Path
from harmonic_weaver.lab.research import relational_worker
folder=Path(sys.argv[1]);original=relational_worker.run
def hold(settings,output):
 original(settings,output)
 (folder/'ready').write_text('ready')
 time.sleep(30)
relational_worker.run=hold
relational_worker.run_frozen(folder)
"""
    process=subprocess.Popen([sys.executable,'-c',program,str(folder)])
    try:
        deadline=time.monotonic()+5
        while not (folder/'ready').exists():
            assert process.poll() is None and time.monotonic()<deadline
            time.sleep(.01)
        assert service.report(ident)['status']=='running'
        assert (folder/'computed/result.json').is_file()
        process.kill();process.wait(timeout=5)
        restored=RelationalService(tmp_path)
        report=restored.report(ident)
        assert report['status']=='interrupted' and report['input_hashes']
        assert restored.report(ident)==report
        with pytest.raises(ValueError,match='unavailable'):restored.artifact(ident,'result.json')
        assert not (folder/'result.json').exists()
        restored.close()
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=5)
        service.close()
