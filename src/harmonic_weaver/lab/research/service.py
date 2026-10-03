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
        if name not in ('request.json','manifest.json','input.json','original.jsonl','global_rotation.jsonl','temporal_shuffle.jsonl','paired.jsonl'):
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
            from .body import BodyRequest
            contract = BodyRequest if report.get('input_kind') == 'evaluation_features' else Settings
            # The worker validates numeric fields again: JSON 0 and 0.0 may
            # differ in spelling while describing the same typed request.
            actual = contract.model_validate_json(path.read_text()).model_dump()
            expected = contract.model_validate(report['settings']).model_dump()
            if actual != expected:raise ValueError('Research request changed')
        else:
            expected=report.get('artifact_hashes',{}).get(name)
            if expected is None:raise ValueError('No verified artifact hash')
            stat=path.stat();fingerprint=(str(path),stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)
            if self.verified.get(fingerprint)!=expected:
                if sha256_file(path)!=expected:raise ValueError('Research artifact changed')
                self.verified[fingerprint]=expected
        return path

    def compare(self, request):
        from .grassmann_compare import compare
        return compare(self, request)

    def start(self,settings):
        settings=Settings.model_validate(settings)
        return self._launch(settings.model_dump(),'harmonic_weaver.lab.research.grassmann')

    def start_body(self, request, evaluation):
        from .body import BodyRequest, snapshot
        request=BodyRequest.model_validate(request)
        if request.input_sha256 is not None:raise ValueError('Input hash is assigned when freezing the selected trace')
        document=snapshot(evaluation,request)
        return self._launch(request.model_dump(),'harmonic_weaver.lab.research.body',document)

    def _launch(self, settings, module, document=None):
        with self.lock:
            if any(p.poll() is None for p in self.processes.values()):raise ValueError('Ya hay un banco R01 corriendo')
            ident=uuid4().hex;folder=self.root/ident;folder.mkdir(mode=0o700)
            if document is not None:
                atomic_json(folder/'input.json',document)
                settings={**settings,'input_sha256':sha256_file(folder/'input.json')}
            atomic_json(folder/'request.json',settings);atomic_json(folder/'manifest.json',{'status':'running','line':'R01'})
            env=dict(os.environ)
            env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
            with (folder/'worker.log').open('wb') as log:
                process=subprocess.Popen([sys.executable,'-m',module,
                    '--request',str(folder/'request.json'),'--output',str(folder)],env=env,stdout=log,stderr=log)
            self.processes[ident]=process
            return {'id':ident,'status':'running','directory':str(folder)}

    def cancel(self, ident, *, shutdown=False):
        if not re.fullmatch(r'[a-f0-9]{32}',ident):raise ValueError('Invalid research job id')
        with self.lock:
            folder=self.root/ident
            if folder.is_symlink() or not folder.is_dir():raise ValueError('Research job is unavailable')
            manifest=folder/'manifest.json'
            if manifest.is_symlink():raise ValueError('Research manifest is unavailable')
            process=self.processes.get(ident)
            if process is not None and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            # The worker can finish during cancellation. Preserve its committed
            # result instead of relabelling a complete experiment as cancelled.
            report=json.loads(manifest.read_text())
            if report.get('status')=='running':
                report={**report,'status':'cancelled' if process is not None and not shutdown else 'interrupted',
                        'error':('Service shutdown' if shutdown else 'Cancelled by user') if process is not None else 'No owned worker to cancel'}
                atomic_json(manifest,report)
            return {**report,'id':ident,'directory':str(folder)}

    def close(self):
        for ident in list(self.processes):
            self.cancel(ident,shutdown=True)
