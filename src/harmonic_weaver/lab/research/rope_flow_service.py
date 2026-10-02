"""Owned, cancellable temporal flow runs; persistent verified JSON results."""
from collections import OrderedDict
from pathlib import Path
from uuid import uuid4
import re
import shutil
import threading
import hashlib
import json
from ..cache import atomic_json
from .rope_flow_run import Request,run,verify
from .rope_process import DecodeCancelled


class RopeFlowService:
    def __init__(self,data_dir,reader):
        self.root=Path(data_dir)/'research/r08-flow'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.receipts=Path(data_dir)/'research/r08-flow-starts'
        self.receipts.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.reader=reader;self.lock=threading.RLock();self.jobs=OrderedDict();self.closed=False

    def folder(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Invalid flow id')
        folder=self.root/ident
        if folder.is_symlink() or not folder.is_dir():raise ValueError('Flow run unavailable')
        return folder

    @staticmethod
    def public(job):return {k:job[k] for k in ('id','status','error')}

    def start(self,path,request,*,idempotency_key=None):
        request=Request.model_validate(request)
        if idempotency_key is not None and (not isinstance(idempotency_key,str) or not re.fullmatch('[a-f0-9]{32}',idempotency_key)):raise ValueError('Invalid flow start key')
        digest=hashlib.sha256(json.dumps(request.model_dump(),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        with self.lock:
            if self.closed:raise ValueError('Flow service closed')
            receipt=self.receipts/f'{idempotency_key}.json' if idempotency_key else None
            if receipt is not None and receipt.exists():
                if receipt.is_symlink() or not receipt.is_file():raise ValueError('Regular flow receipt required')
                previous=json.loads(receipt.read_text())
                if previous.get('request_sha256')!=digest:raise ValueError('Flow start key reused with different request')
                # Never launch again after restart, eviction or interrupted publication.
                return self.report(previous['id'])
            if any(j['thread'].is_alive() for j in self.jobs.values()):raise ValueError('A flow run is active; cancel or wait')
            while len(self.jobs)>=8:self.jobs.popitem(last=False)
            ident=uuid4().hex;folder=self.root/ident
            job={'id':ident,'status':'running','error':None,'cancel':threading.Event()}
            def work():
                try:
                    run(request,path,folder,self.reader,cancel=job['cancel'])
                    with self.lock:
                        if job['cancel'].is_set():
                            shutil.rmtree(folder);job['status']='cancelled'
                        else:job['status']='complete'
                except Exception as exc:
                    # Only this job's newly generated folder may be removed.
                    cleanup_failed=False
                    try:
                        if folder.exists() and not folder.is_symlink():shutil.rmtree(folder)
                    except OSError:cleanup_failed=True
                    with self.lock:
                        job['status']='cancelled' if not cleanup_failed and (isinstance(exc,DecodeCancelled) or job['cancel'].is_set()) else 'failed'
                        if job['status']=='failed':job['error']='Flow calculation failed; check source, clock, seeds and limits'
            job['thread']=threading.Thread(target=work,name='rope-flow',daemon=True)
            if receipt is not None:atomic_json(receipt,{'id':ident,'request_sha256':digest})
            self.jobs[ident]=job;job['thread'].start()
            return self.public(job)

    def report(self,ident):
        with self.lock:
            if ident in self.jobs:return self.public(self.jobs[ident])
            verify(self.folder(ident))
            return {'id':ident,'status':'complete','error':None}

    def cancel(self,ident):
        with self.lock:
            if ident not in self.jobs:return self.report(ident)
            job=self.jobs[ident]
            if job['status']=='running':job['cancel'].set()
            return self.public(job)

    def list(self):
        with self.lock:
            rows=[]
            for folder in sorted(self.root.iterdir()):
                if re.fullmatch('[a-f0-9]{32}',folder.name) and folder.is_dir() and not folder.is_symlink():
                    if folder.name in self.jobs and self.jobs[folder.name]['status']!='complete':continue
                    try:rows.append({**verify(folder),'id':folder.name,'read_verification':'integrity_only'})
                    except (OSError,ValueError,KeyError):continue
            return rows

    def artifact(self,ident,name):
        if name not in ('request.json','result.json','manifest.json'):raise ValueError('Unknown flow artifact')
        with self.lock:
            if ident in self.jobs and self.jobs[ident]['status']!='complete':raise ValueError('Flow result unavailable')
            folder=self.folder(ident);verify(folder)
            return folder/name

    def close(self):
        with self.lock:
            self.closed=True
            threads=[]
            for job in self.jobs.values():
                if job['status']=='running':job['cancel'].set()
                threads.append(job['thread'])
        for thread in threads:thread.join(timeout=65)
