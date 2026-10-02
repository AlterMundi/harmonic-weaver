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
