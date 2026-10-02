import subprocess,threading,time
import pytest
from harmonic_weaver.lab.research.rope_reader import RopeReader
from harmonic_weaver.lab.research.rope_jobs import RopeJobs
from harmonic_weaver.lab.research.rope_process import DecodeCancelled


def wait(service,ident):
    end=time.monotonic()+5
    while service.report(ident)['status']=='running' and time.monotonic()<end:time.sleep(.01)
    return service.report(ident)['status']


def test_actual_probe_decode_result_and_expiry(tmp_path):
    video=tmp_path/'video.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    service=RopeJobs(RopeReader())
    try:
        probe=service.start(video)['id'];assert wait(service,probe)=='complete'
        media=service.result(probe)
        frame=service.start(video,index=2,sha256=media['media_sha256'])['id'];assert wait(service,frame)=='complete'
        assert service.result(frame).startswith(b'\x89PNG')
        again=service.start(video)['id'];assert wait(service,again)=='complete'
        with pytest.raises(ValueError):service.result(frame)
        bad=service.start(video,index=8,sha256=media['media_sha256'])['id'];assert wait(service,bad)=='failed'
        with pytest.raises(ValueError):service.result(bad)
    finally:service.close()


def test_owned_cancel_active_guard_and_shutdown():
    entered=threading.Event()
    class Reader:
        def probe(self,path,*,cancel):
            entered.set();cancel.wait(3)
            if cancel.is_set():raise DecodeCancelled('cancelled')
            return {}
    service=RopeJobs(Reader());ident=service.start('unused')['id']
    assert entered.wait(1)
    with pytest.raises(ValueError):service.start('unused')
    with pytest.raises(KeyError):service.cancel('foreign')
    service.cancel(ident);assert wait(service,ident)=='cancelled'
    with pytest.raises(ValueError):service.result(ident)
    service.close()
    with pytest.raises(ValueError):service.start('unused')
