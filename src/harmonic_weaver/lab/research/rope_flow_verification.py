"""Owned cancellable source recomputation; never rewrite original artifacts."""
from collections import OrderedDict
import threading
from uuid import uuid4
from ..cache import sha256_file
from .rope_flow_run import verify
from .rope_process import DecodeCancelled


class RopeFlowVerification:
    def __init__(self,flow,reader):
        self.flow=flow;self.reader=reader;self.lock=threading.RLock()
        self.jobs=OrderedDict();self.closed=False

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
                    verify(folder,path=path,reader=self.reader,cancel=job['cancel'])
                    if sha256_file(folder/'manifest.json')!=digest:raise ValueError('Manifest changed during recomputation')
                    with self.lock:
                        if job['cancel'].is_set():job['status']='cancelled'
                        else:job['status']='complete';job['verification']='recomputed'
                except DecodeCancelled:
                    with self.lock:job['status']='cancelled'
                except Exception:
                    with self.lock:
                        job['status']='failed';job['error']='Recomputation unavailable or differs; check source integrity, code and environment'
            job['thread']=threading.Thread(target=work,name='rope-flow-verify',daemon=True)
            self.jobs[job['id']]=job;job['thread'].start()
            return self.public(job)

    def report(self,ident):
        with self.lock:return self.public(self.jobs[ident])

    def cancel(self,ident):
        with self.lock:
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
