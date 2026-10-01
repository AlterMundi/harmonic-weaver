"""Own real children for cancellation and same-service admission races."""
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest
from harmonic_weaver.lab.research.coincidence_service import CoincidenceService


def launch_fixture(monkeypatch,mode):
    original=subprocess.Popen
    program="""import sys,time
from pathlib import Path
from harmonic_weaver.lab.research import coincidence
folder=Path(sys.argv[1]);mode=sys.argv[2]
if mode=='queued':
 (folder/'ready').write_text('ready')
 time.sleep(30)
else:
 def fixture(*args,**kwargs):
  (folder/'ready').write_text('ready')
  if mode=='running':time.sleep(30)
  return {'synthetic':True}
 coincidence.compare_frozen=fixture
 coincidence.run_frozen(folder)
"""
    def launch(command,**kwargs):
        return original([sys.executable,'-c',program,command[-1],mode],**kwargs)
    monkeypatch.setattr(subprocess,'Popen',launch)


def ready(service,job):
    process=service.processes[job['id']];deadline=time.monotonic()+5
    while not (service.folder(job['id'])/'ready').exists():
        assert process.poll() is None
        assert time.monotonic()<deadline
        time.sleep(.01)
    return process


@pytest.mark.parametrize('mode,shutdown,expected',[
    ('queued',False,'cancelled'),('running',False,'cancelled'),
    ('running',True,'interrupted'),('complete',False,'complete')])
def test_owned_cancel_terminal_state_restart_and_no_live_child(tmp_path,monkeypatch,mode,shutdown,expected):
    launch_fixture(monkeypatch,mode)
    service=CoincidenceService(tmp_path)
    try:
        job=service.start({}, {}, {})
        process=ready(service,job)
        if mode=='complete':assert process.wait(timeout=5)==0
        before=service.report(job['id'])
        if shutdown:service.close();after=service.report(job['id'])
        else:after=service.cancel(job['id'])
        assert after['status']==expected
        assert process.poll() is not None
        assert after['input_hashes']==before['input_hashes']
        if expected=='complete':assert after['output']==before['output']
        else:
            assert not (service.folder(job['id'])/'result.json').exists()
            with pytest.raises(ValueError,match='complete|unavailable'):service.artifact(job['id'],'result.json')
        restored=CoincidenceService(tmp_path)
        assert restored.report(job['id'])['status']==expected
        with pytest.raises(ValueError,match='owned'):restored.cancel(job['id'])
        assert restored.report(job['id'])['status']==expected
        if not shutdown:assert service.cancel(job['id'])['status']==expected
        restored.close()
    finally:service.close()


def test_simultaneous_start_accepts_only_one_worker_per_service(tmp_path,monkeypatch):
    launch_fixture(monkeypatch,'running')
    service=CoincidenceService(tmp_path);barrier=threading.Barrier(2)
    def start():
        barrier.wait(timeout=5)
        try:return service.start({}, {}, {})
        except ValueError as exc:return str(exc)
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results=list(executor.map(lambda _:start(),range(2)))
        jobs=[v for v in results if isinstance(v,dict)]
        assert len(jobs)==1
        assert len([v for v in results if isinstance(v,str) and 'already active' in v])==1
        assert len(service.processes)==1
        assert len(service.list())==1
        process=ready(service,jobs[0])
        service.cancel(jobs[0]['id'])
        assert process.poll() is not None
        # After cancellation admission opens again, with a new immutable folder.
        replacement=service.start({}, {}, {})
        assert replacement['id']!=jobs[0]['id']
        ready(service,replacement)
    finally:service.close()
    assert all(p.poll() is not None for p in service.processes.values())
    with pytest.raises(ValueError,match='closed'):service.start({}, {}, {})
    assert len(service.list())==2
