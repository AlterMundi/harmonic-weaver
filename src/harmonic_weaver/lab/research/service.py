"""Small optional research jobs isolated from live synthesis and tracking."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from uuid import uuid4

from ..cache import atomic_json
from .grassmann import Settings


class ResearchService:
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research'/'r01';self.root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.Lock();self.processes={}

    def list(self):
        jobs=[]
        for folder in sorted(self.root.iterdir()):
            try:
                report=json.loads((folder/'manifest.json').read_text())
                if report['status']=='running':
                    process=self.processes.get(folder.name)
                    if process is None or process.poll() is not None:
                        report={'status':'interrupted','error':'No confirmed completion'}
                jobs.append({**report,'id':folder.name,'directory':str(folder)})
            except (OSError,ValueError,KeyError):continue
        return jobs

    def start(self,settings):
        settings=Settings.model_validate(settings)
        with self.lock:
            if any(p.poll() is None for p in self.processes.values()):raise ValueError('Ya hay un banco R01 corriendo')
            ident=uuid4().hex;folder=self.root/ident;folder.mkdir(mode=0o700)
            atomic_json(folder/'request.json',settings.model_dump());atomic_json(folder/'manifest.json',{'status':'running','line':'R01'})
            env=dict(os.environ)
            env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
            with (folder/'worker.log').open('wb') as log:
                process=subprocess.Popen([sys.executable,'-m','harmonic_weaver.lab.research.grassmann',
                    '--request',str(folder/'request.json'),'--output',str(folder)],env=env,stdout=log,stderr=log)
            self.processes[ident]=process
            return {'id':ident,'status':'running','directory':str(folder)}

    def close(self):
        for process in self.processes.values():
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
