"""Owned cancellable source recomputation; never rewrite original artifacts."""
from collections import OrderedDict
import threading
import json
import re
from datetime import datetime,timezone,timedelta
from pathlib import Path
from typing import Literal
from pydantic import Field,model_validator
from ..contracts import Contract
from uuid import uuid4
from ..cache import sha256_file,atomic_json
from .rope_flow_run import verify
from .rope_process import DecodeCancelled


class Evidence(Contract):
    schema_version:Literal[1]
    line:Literal['R08']
    id:str=Field(pattern='^[a-f0-9]{32}$')
    source_run_id:str=Field(pattern='^[a-f0-9]{32}$')
    source_manifest_sha256:str=Field(pattern='^[a-f0-9]{64}$')
    status:Literal['complete']
    verification:Literal['recomputed']
    error:None
    checked_at_utc:str=Field(max_length=64)
    environment:dict[str,str]
    code_hashes:dict[str,str]
    evidence_code_hashes:dict[str,str]
    limits:list[str]=Field(max_length=16)

    @model_validator(mode='after')
    def valid(self):
        if datetime.fromisoformat(self.checked_at_utc).utcoffset()!=timedelta(0):raise ValueError('UTC verification timestamp required')
        if not self.environment or len(self.environment)>32 or any(not d or len(d)>32 for d in (self.code_hashes,self.evidence_code_hashes)):raise ValueError('Bounded verification environment/code required')
        if any(not re.fullmatch('[a-f0-9]{64}',v) for d in (self.code_hashes,self.evidence_code_hashes) for v in d.values()):raise ValueError('Verification code digest invalid')
        return self


class RopeFlowVerification:
    def __init__(self,flow,reader):
        self.flow=flow;self.reader=reader;self.lock=threading.RLock()
        self.jobs=OrderedDict();self.closed=False
        self.root=self.flow.root.parent/'r08-flow-verifications'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)

    @staticmethod
    def public(job):
        return {k:job[k] for k in ('id','source_run_id','source_manifest_sha256','status','verification','error')}

    def start(self,ident,path):
        folder=self.flow.folder(ident)
        self.flow.artifact(ident,'manifest.json')
        digest=sha256_file(folder/'manifest.json')
        with self.lock:
            if self.closed:raise ValueError('Flow verification closed')
            if any(j['thread'].is_alive() for j in self.jobs.values()):raise ValueError('A verification is active; cancel or wait')
            while len(self.jobs)>=8:self.jobs.popitem(last=False)
            job={'id':uuid4().hex,'source_run_id':ident,'source_manifest_sha256':digest,
                 'status':'running','verification':None,'error':None,'cancel':threading.Event()}
            def work():
                try:
                    original=verify(folder,path=path,reader=self.reader,cancel=job['cancel'])
                    if sha256_file(folder/'manifest.json')!=digest:raise ValueError('Manifest changed during recomputation')
                    with self.lock:
                        if job['cancel'].is_set():job['status']='cancelled'
                        else:
                            report={**self.public(job),'schema_version':1,'line':'R08','status':'complete','verification':'recomputed',
                                    'checked_at_utc':datetime.now(timezone.utc).isoformat(),
                                    'environment':original['environment'],'code_hashes':original['code_hashes'],
                                    'evidence_code_hashes':{name:sha256_file(Path(__file__).parent/name) for name in ('rope_flow_verification.py','../contracts.py')},
                                    'limits':['Historical record of source recomputation at the recorded time; not current source verification',
                                              'Artifact hashes are not signed custody or optical accuracy validation']}
                            output=self.root/job['id'];output.mkdir(mode=0o700,exist_ok=False)
                            atomic_json(output/'report.json',report)
                            atomic_json(output/'manifest.json',{'schema_version':1,'line':'R08','kind':'flow_recomputation_evidence',
                                        'output':{'file':'report.json','sha256':sha256_file(output/'report.json')}})
                            job['status']='complete';job['verification']='recomputed'
                except DecodeCancelled:
                    with self.lock:job['status']='cancelled'
                except Exception:
                    with self.lock:
                        job['status']='failed';job['error']='Recomputation unavailable or differs; check source integrity, code and environment'
            job['thread']=threading.Thread(target=work,name='rope-flow-verify',daemon=True)
            self.jobs[job['id']]=job;job['thread'].start()
            return self.public(job)

    def report(self,ident):
        with self.lock:
            if ident in self.jobs:return self.public(self.jobs[ident])
            return self.read(ident)

    def read(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Invalid verification id')
        folder=self.root/ident
        if folder.is_symlink() or not folder.is_dir():raise ValueError('Verification evidence unavailable')
        for name in ('report.json','manifest.json'):
            path=folder/name
            if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:raise ValueError('Regular bounded verification evidence required')
        hashes={name:sha256_file(folder/name) for name in ('report.json','manifest.json')}
        manifest=json.loads((folder/'manifest.json').read_text());report=json.loads((folder/'report.json').read_text())
        if manifest!={'schema_version':1,'line':'R08','kind':'flow_recomputation_evidence','output':{'file':'report.json','sha256':hashes['report.json']}}:raise ValueError('Verification evidence hash/envelope mismatch')
        report=Evidence.model_validate(report).model_dump()
        if report['id']!=ident:raise ValueError('Verification report id mismatch')
        for name,digest in hashes.items():
            if (folder/name).is_symlink() or sha256_file(folder/name)!=digest:raise ValueError('Verification evidence changed during reading')
        return report

    def list(self,source_run_id=None):
        rows=[]
        for folder in sorted(self.root.iterdir()):
            try:
                report=self.read(folder.name)
                if source_run_id is None or report['source_run_id']==source_run_id:rows.append({**report,'read_verification':'historical_evidence_integrity_only'})
            except (OSError,ValueError,KeyError):continue
        return rows

    def artifact(self,ident,name):
        if name not in ('report.json','manifest.json'):raise ValueError('Unknown verification artifact')
        self.read(ident);return self.root/ident/name

    def cancel(self,ident):
        with self.lock:
            if ident not in self.jobs:return self.report(ident)
            job=self.jobs[ident]
            if job['status']=='running':job['cancel'].set()
            return self.public(job)

    def close(self):
        with self.lock:
            self.closed=True
            threads=[]
            for job in self.jobs.values():
                if job['status']=='running':job['cancel'].set()
                threads.append(job['thread'])
        for thread in threads:thread.join(timeout=65)
