#!/usr/bin/env python3
"""Finite, non-recording headless Weaver using its maintained Stage factory."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bounded_log import copy_tail

def main():
    state=Path.home()/'.local/state/harmonic-lab/router';state.mkdir(parents=True,exist_ok=True)
    stop=threading.Event()
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
    child=subprocess.Popen([sys.executable,'-m','uvicorn','harmonic_weaver.server:create_app','--factory','--host','127.0.0.1','--port','8767','--log-level','warning'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    threading.Thread(target=copy_tail,args=(child.stdout,state/'latest.log'),daemon=True).start()
    end=time.monotonic()+8*3600
    try:
        while child.poll() is None and time.monotonic()<end and not stop.wait(.5):pass
    finally:
        if child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
if __name__=='__main__':main()
