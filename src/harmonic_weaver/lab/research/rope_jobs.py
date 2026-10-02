"""Owned ephemeral decode jobs: one active, bounded results, no media copies."""
from collections import OrderedDict
from copy import deepcopy
import threading
from uuid import uuid4
from .rope_process import DecodeCancelled


class RopeJobs:
    def __init__(self,reader):
        self.reader=reader;self.jobs=OrderedDict();self.lock=threading.RLock();self.closed=False

    def _public(self,job):
        return {k:job[k] for k in ('id','kind','status','error')}

    def start(self,path,*,index=None,sha256=None):
        if index is not None and (type(index) is not int or index<0 or not isinstance(sha256,str) or len(sha256)!=64):
            raise ValueError('Frame job requires nonnegative index and source SHA256')
        with self.lock:
            if self.closed:raise ValueError('Decode service closed')
            if any(j['thread'].is_alive() for j in self.jobs.values()):raise ValueError('A decode job is active; cancel or wait')
            # Release prior image results; inventories are small and bounded below.
            for j in self.jobs.values():
                if j['kind']=='frame':j['result']=None
            while len(self.jobs)>=8:self.jobs.popitem(last=False)
            ident=uuid4().hex
            job={'id':ident,'kind':'probe' if index is None else 'frame','status':'running','error':None,'result':None,'cancel':threading.Event()}
            def work():
                try:
                    result=self.reader.probe(path,cancel=job['cancel']) if index is None else self.reader.frame(path,index,sha256,cancel=job['cancel'])
                    with self.lock:
                        if job['cancel'].is_set():job['status']='cancelled'
                        else:job['result']=result;job['status']='complete'
                except DecodeCancelled:
                    with self.lock:job['status']='cancelled'
                except Exception:
                    # Do not publish arbitrary exception text carrying local paths.
                    with self.lock:job['status']='failed';job['error']='Video reading failed; check source integrity and decoded frame limits'
            job['thread']=threading.Thread(target=work,name='rope-decode',daemon=True)
            self.jobs[ident]=job;job['thread'].start()
            return self._public(job)

    def report(self,ident):
        with self.lock:return self._public(self.jobs[ident])

    def cancel(self,ident):
        with self.lock:
            job=self.jobs[ident]
            if job['thread'].is_alive():job['cancel'].set()
            return self._public(job)

    def result(self,ident):
        with self.lock:
            job=self.jobs[ident]
            if job['status']!='complete' or job['result'] is None:raise ValueError('Decode result unavailable or expired')
            return deepcopy(job['result'])

    def close(self):
        with self.lock:
            self.closed=True
            threads=[]
            for job in self.jobs.values():job['cancel'].set();threads.append(job['thread'])
        for thread in threads:thread.join(timeout=65)
