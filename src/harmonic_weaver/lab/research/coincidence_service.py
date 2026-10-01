"""Owned R03 workers; private frozen inputs never touch live synthesis."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
from uuid import uuid4

from ..cache import atomic_json,sha256_file
from .coincidence import inspect_run


class CoincidenceService:
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research'/'r03';self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock();self.processes={}

    def folder(self,ident):
        if not isinstance(ident,str) or not re.fullmatch(r'[a-f0-9]{32}',ident):raise ValueError('Invalid R03 job id')
        folder=self.root/ident
        if folder.is_symlink() or not folder.is_dir():raise ValueError('R03 job unavailable')
        return folder

    def start(self,request,marks,features):
        with self.lock:
            if any(p.poll() is None for p in self.processes.values()):raise ValueError('An R03 worker is already active')
            ident=uuid4().hex;folder=self.root/ident;folder.mkdir(mode=0o700)
            for name,value in (('request.json',request),('marks.json',marks),('features.json',features)):
                atomic_json(folder/name,value)
            job={'schema_version':1,'status':'queued','line':'R03',
                 'input_hashes':{name:sha256_file(folder/name) for name in ('request.json','marks.json','features.json')}}
            atomic_json(folder/'job.json',job)
            try:
                env=dict(os.environ);env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
                with (folder/'worker.log').open('wb') as log:
                    self.processes[ident]=subprocess.Popen([sys.executable,'-m','harmonic_weaver.lab.research.coincidence',
                        '--folder',str(folder)],env=env,stdout=log,stderr=log)
            except Exception as exc:
                job.update(status='failed',error=str(exc));atomic_json(folder/'job.json',job);raise
            return {**job,'id':ident,'directory':str(folder)}

    def report(self,ident):
        with self.lock:
            folder=self.folder(ident)
            if (folder/'manifest.json').exists():report=inspect_run(folder)
            else:
                path=folder/'job.json'
                if path.is_symlink():raise ValueError('R03 job metadata unavailable')
                report=json.loads(path.read_text());process=self.processes.get(ident)
                if report['status']=='queued' and (process is None or process.poll() is not None):
                    report.update(status='interrupted',error='No owned worker and no manifest')
                    atomic_json(path,report)
            return {**report,'id':ident,'directory':str(folder)}

    def list(self):
        jobs=[]
        with self.lock:
            for folder in sorted(self.root.iterdir()):
                if not folder.is_symlink() and folder.is_dir() and re.fullmatch(r'[a-f0-9]{32}',folder.name):
                    try:jobs.append(self.report(folder.name))
                    except (OSError,ValueError,KeyError):continue
        return jobs

    def artifact(self,ident,name):
        if name not in ('request.json','marks.json','features.json','result.json','manifest.json'):raise ValueError('Unknown R03 artifact')
        folder=self.folder(ident);report=self.report(ident);path=folder/name
        if path.is_symlink() or not path.is_file():raise ValueError('R03 artifact unavailable')
        if name=='manifest.json':return path
        if report['status']!='complete':raise ValueError('R03 result is not complete')
        expected=report['output']['sha256'] if name=='result.json' else report['input_hashes'].get(name)
        if not expected or sha256_file(path)!=expected:raise ValueError('R03 artifact changed')
        return path

    def cancel(self,ident,*,shutdown=False):
        with self.lock:
            folder=self.folder(ident);process=self.processes.get(ident)
            if process is None:raise ValueError('No owned R03 worker to cancel')
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            report=self.report(ident)
            if report['status'] in ('queued','running','interrupted'):
                target=folder/('manifest.json' if (folder/'manifest.json').exists() else 'job.json')
                value={k:v for k,v in report.items() if k not in ('id','directory')}
                value.update(status='interrupted' if shutdown else 'cancelled',error='Service shutdown' if shutdown else 'Cancelled by user')
                atomic_json(target,value)
            return self.report(ident)

    def close(self):
        for ident in list(self.processes):
            if self.processes[ident].poll() is None:self.cancel(ident,shutdown=True)
