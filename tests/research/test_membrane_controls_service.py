import time
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
