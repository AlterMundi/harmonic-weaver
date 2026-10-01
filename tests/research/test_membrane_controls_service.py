import time
import subprocess
import sys
import pytest
from harmonic_weaver.lab.research.membrane_controls_service import ControlService


def test_real_control_worker_repeat_restore_and_tamper(tmp_path):
    service=ControlService(tmp_path);outputs=[];ids=[]
    try:
        for i in range(2):
            job=service.start({'duration_samples':800,'forcing_samples':400});ident=job['id'];ids.append(ident)
            deadline=time.monotonic()+15
            while True:
                report=service.report(ident)
                if report['status'] not in ('queued','running') and not report['worker_active']:break
                assert time.monotonic()<deadline;time.sleep(.02)
            assert report['status']=='complete'
            outputs.append(service.artifact(ident,'result.json').read_bytes())
        assert outputs[0]==outputs[1]
        restored=ControlService(tmp_path)
        try:
            assert len(restored.list())==2
            assert restored.artifact(ids[0],'result.json').read_bytes()==outputs[0]
            with pytest.raises(ValueError):restored.cancel(ids[0])
            restored.folder(ids[0]).joinpath('result.json').write_bytes(b'changed')
            with pytest.raises(ValueError):restored.artifact(ids[0],'result.json')
        finally:restored.close()
    finally:service.close()


def test_cancel_running_control_worker(tmp_path):
    service=ControlService(tmp_path)
    try:
        job=service.start({'duration_samples':96000,'forcing_samples':48000});ident=job['id']
        deadline=time.monotonic()+15
        while service.report(ident)['status']=='queued':
            assert time.monotonic()<deadline;time.sleep(.01)
        assert service.report(ident)['status']=='running'
        assert service.cancel(ident)['status']=='cancelled'
        with pytest.raises(ValueError):service.artifact(ident,'result.json')
        assert service.artifact(ident,'manifest.json').is_file()
    finally:service.close()


def test_real_death_after_control_result_promotion_preserves_incomplete(tmp_path):
    from harmonic_weaver.lab.cache import atomic_json,sha256_file
    service=ControlService(tmp_path);ident='a'*32;folder=service.root/ident;folder.mkdir()
    atomic_json(folder/'request.json',{'duration_samples':800,'forcing_samples':400})
    script='''
import sys,time
from pathlib import Path
from harmonic_weaver.lab.research.membrane_controls_worker import run_frozen
root=Path(sys.argv[1]);original=Path.replace
def held(self,target):
 value=original(self,target)
 if Path(target)==root/'result.json':
  (root/'promoted.marker').write_text('ready');time.sleep(30)
 return value
Path.replace=held
run_frozen(root)
'''
    process=subprocess.Popen([sys.executable,'-c',script,str(folder)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+15
        while not (folder/'promoted.marker').exists():
            assert process.poll() is None
            assert time.monotonic()<deadline;time.sleep(.02)
        assert service.report(ident)['status']=='running'
        with pytest.raises(ValueError):service.artifact(ident,'result.json')
        digest=sha256_file(folder/'result.json')
        process.kill();process.wait(timeout=5)
        restored=ControlService(tmp_path)
        try:
            assert restored.report(ident)['status']=='interrupted'
            assert sha256_file(folder/'result.json')==digest
            with pytest.raises(ValueError):restored.artifact(ident,'result.json')
            assert restored.artifact(ident,'manifest.json').is_file()
        finally:restored.close()
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=5)
        process.stderr.close();service.close()
