"""Small optional research jobs isolated from live synthesis and tracking."""
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import threading
from uuid import uuid4

from ..cache import atomic_json, sha256_file
from .grassmann import Settings


class ResearchService:
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research'/'r01';self.root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.Lock();self.processes={};self.verified={}

    def list(self):
        jobs=[]
        for folder in sorted(self.root.iterdir()):
            if folder.is_symlink() or not folder.is_dir():continue
            try:
                report=json.loads((folder/'manifest.json').read_text())
                if report['status']=='running':
                    process=self.processes.get(folder.name)
                    if process is None or process.poll() is not None:
                        report={'status':'interrupted','error':'No confirmed completion'}
                jobs.append({**report,'id':folder.name,'directory':str(folder)})
            except (OSError,ValueError,KeyError):continue
        return jobs

    def artifact(self, ident, name):
        if not re.fullmatch(r'[a-f0-9]{32}',ident):raise ValueError('Invalid research job id')
        if name not in ('request.json','manifest.json','original.jsonl','global_rotation.jsonl','temporal_shuffle.jsonl','paired.jsonl'):
            raise ValueError('Unknown research artifact')
        folder=self.root/ident
        if folder.is_symlink() or not folder.is_dir():raise ValueError('Research job is unavailable')
        path=folder/name
        if path.is_symlink() or not path.is_file():raise ValueError('Research artifact is unavailable')
        manifest=folder/'manifest.json'
        if manifest.is_symlink():raise ValueError('Research manifest is unavailable')
        report=json.loads(manifest.read_text())
        if name=='manifest.json':return path
        if report.get('status')!='complete':raise ValueError('Research job is not complete')
        if name=='request.json':
            if json.dumps(json.loads(path.read_text()),sort_keys=True,allow_nan=False)!=json.dumps(report['settings'],sort_keys=True,allow_nan=False):raise ValueError('Research request changed')
        else:
            expected=report.get('artifact_hashes',{}).get(name)
            if expected is None:raise ValueError('No verified artifact hash')
            stat=path.stat();fingerprint=(str(path),stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)
            if self.verified.get(fingerprint)!=expected:
                if sha256_file(path)!=expected:raise ValueError('Research artifact changed')
                self.verified[fingerprint]=expected
        return path

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
