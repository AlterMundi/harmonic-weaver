import sys,threading,time
import pytest
from harmonic_weaver.lab.research.rope_process import capture,DecodeCancelled


def test_bounded_capture_success_overflow_timeout_and_live_cancel(tmp_path):
    assert capture([sys.executable,'-c','print("ok",end="")'],max_bytes=2)==b'ok'
    with pytest.raises(ValueError,match='budget'):
        capture([sys.executable,'-c','import sys;sys.stdout.write("x"*1000000);sys.stdout.flush()'],max_bytes=10)
    with pytest.raises(ValueError,match='timed out'):
        capture([sys.executable,'-c','import time;time.sleep(30)'],max_bytes=10,timeout=.1)
    ready=tmp_path/'ready';stopped=threading.Event();errors=[]
    def work():
        try:capture([sys.executable,'-c',f'from pathlib import Path;import time;Path({str(ready)!r}).write_text("ready");time.sleep(30)'],max_bytes=10,cancel=stopped)
        except Exception as exc:errors.append(exc)
    worker=threading.Thread(target=work);worker.start()
    deadline=time.monotonic()+3
    while not ready.exists() and time.monotonic()<deadline:stopped.wait(.01)
    assert ready.exists() and worker.is_alive()
    stopped.set();worker.join(timeout=2)
    assert not worker.is_alive() and len(errors)==1 and isinstance(errors[0],DecodeCancelled)
    with pytest.raises(DecodeCancelled):capture([sys.executable,'-c','raise Exception()'],max_bytes=10,cancel=stopped)


def test_hash_matches_sha256_and_stops_between_reads(tmp_path):
    import hashlib
    from harmonic_weaver.lab.research.rope_process import file_hash
    path=tmp_path/'data';data=b'x'*(3*1024*1024+7);path.write_bytes(data)
    assert file_hash(path)==hashlib.sha256(data).hexdigest()
    class CancelDuringReads:
        def __init__(self):self.calls=0
        def is_set(self):self.calls+=1;return self.calls>=4
    event=CancelDuringReads()
    with pytest.raises(DecodeCancelled,match='hashing'):file_hash(path,cancel=event)
    assert event.calls==4
    stopped=threading.Event();stopped.set()
    with pytest.raises(DecodeCancelled):file_hash(tmp_path/'does-not-exist',cancel=stopped)
