import os
import sys
import time
from types import SimpleNamespace
import pytest
from harmonic_weaver.lab.research.rope_flow_verification import RopeFlowVerification
from harmonic_weaver.lab.research.rope_process import capture


def test_owned_reverification_cancel_stops_process_without_mutating_original(tmp_path,monkeypatch):
    import harmonic_weaver.lab.research.rope_flow_verification as module
    folder=tmp_path/'original';folder.mkdir();manifest=folder/'manifest.json';manifest.write_text('{}')
    original=manifest.read_bytes();pidfile=tmp_path/'pid'
    def slow(*args,cancel=None,**kwargs):
        capture([sys.executable,'-c',f'from pathlib import Path;import os,time;Path({str(pidfile)!r}).write_text(str(os.getpid()));time.sleep(30)'],max_bytes=1024,cancel=cancel)
    monkeypatch.setattr(module,'verify',slow)
    flow=SimpleNamespace(root=tmp_path/'r08-flow',folder=lambda ident:folder,artifact=lambda ident,name:folder/name)
    service=RopeFlowVerification(flow,None)
    try:
        job=service.start('a'*32,tmp_path/'video')
        deadline=time.monotonic()+3
        while not pidfile.exists() and time.monotonic()<deadline:time.sleep(.01)
        assert pidfile.exists();pid=int(pidfile.read_text());os.kill(pid,0)
        with pytest.raises(ValueError,match='active'):service.start('a'*32,tmp_path/'video')
        with pytest.raises(ValueError):service.cancel('b'*32)
        service.cancel(job['id'])
        while service.report(job['id'])['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        report=service.report(job['id']);assert report['status']=='cancelled' and report['verification'] is None
        with pytest.raises(ProcessLookupError):os.kill(pid,0)
        assert manifest.read_bytes()==original
    finally:service.close()
