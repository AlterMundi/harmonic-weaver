import os
import sys
import time
import pytest
from harmonic_weaver.lab.research.rope_flow_service import RopeFlowService
from harmonic_weaver.lab.research.rope_process import capture


def test_owned_cancel_stops_real_process_and_cleans_only_own_run(tmp_path,monkeypatch):
    import harmonic_weaver.lab.research.rope_flow_service as module
    marker=tmp_path/'pid'
    untouched=tmp_path/'keep';untouched.write_text('preserved')
    def slow(request,path,folder,reader,*,cancel):
        folder.mkdir();(folder/'partial.json').write_text('{}')
        capture([sys.executable,'-c',f'from pathlib import Path;import os,time;Path({str(marker)!r}).write_text(str(os.getpid()));time.sleep(30)'],max_bytes=1024,cancel=cancel)
    monkeypatch.setattr(module,'run',slow)
    service=RopeFlowService(tmp_path,None)
    request={'media_sha256':'a'*64,'width_px':160,'height_px':120,'start_frame_index':0,
             'frame_times_s':[0,.1],'seeds':[{'x':.5,'y':.5}]}
    try:
        job=service.start(tmp_path/'unused',request)
        deadline=time.monotonic()+3
        while not marker.exists() and time.monotonic()<deadline:time.sleep(.01)
        assert marker.exists();pid=int(marker.read_text());os.kill(pid,0)
        with pytest.raises(ValueError,match='active'):service.start(tmp_path/'unused',request)
        with pytest.raises(ValueError):service.cancel('b'*32)
        os.kill(pid,0) # Foreign cancellation did not stop the owned process.
        service.cancel(job['id'])
        while service.report(job['id'])['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        assert service.report(job['id'])['status']=='cancelled'
        with pytest.raises(ProcessLookupError):os.kill(pid,0)
        assert not (service.root/job['id']).exists()
        assert service.list()==[] and untouched.read_text()=='preserved'
    finally:service.close()
    with pytest.raises(ValueError,match='closed'):service.start(tmp_path/'unused',request)


def test_cancel_after_publication_and_failure_have_no_completed_artifacts(tmp_path,monkeypatch):
    import harmonic_weaver.lab.research.rope_flow_service as module
    request={'media_sha256':'a'*64,'width_px':160,'height_px':120,'start_frame_index':0,
             'frame_times_s':[0,.1],'seeds':[{'x':.5,'y':.5}]}
    for cancelled in (True,False):
        def work(request,path,folder,reader,*,cancel):
            folder.mkdir();(folder/'manifest.json').write_text('{}')
            if cancelled:cancel.set()
            else:raise ValueError('/private/source/path should not be returned')
        monkeypatch.setattr(module,'run',work)
        service=RopeFlowService(tmp_path/str(cancelled),None)
        try:
            job=service.start(tmp_path/'unused',request)
            deadline=time.monotonic()+3
            while service.report(job['id'])['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
            result=service.report(job['id'])
            assert result['status']==('cancelled' if cancelled else 'failed')
            assert '/private/' not in str(result)
            assert not (service.root/job['id']).exists() and service.list()==[]
        finally:service.close()
