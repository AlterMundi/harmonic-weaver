"""Owned R13 subprocess and verified evaluation-feature snapshots."""
import json,os,re,subprocess,sys,threading
from pathlib import Path
from uuid import uuid4
from ..cache import atomic_json
from ..contracts import Contract
from pydantic import Field
from typing import Literal
from .service import ResearchService
from .heldout import Request,Sequence
from .heldout_run import verify,FILES
from .body import BodyRequest,snapshot

class SequenceSelection(Contract):
    id: str = Field(min_length=1,max_length=80)
    role: Literal['train','test']
    subject_group: str = Field(min_length=1,max_length=80)
    task_id: str = Field(min_length=1,max_length=80)
    selection: BodyRequest


class HeldoutService(ResearchService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r13-heldout';self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.Lock();self.processes={};self.verified={}

    def start(self,request):
        request=Request.model_validate(request)
        with self.lock:
            if any(p.poll() is None for p in self.processes.values()):raise ValueError('Ya hay un banco R13 corriendo')
            ident=uuid4().hex;folder=self.root/ident;folder.mkdir(mode=0o700)
            atomic_json(folder/'request.json',request.model_dump());atomic_json(folder/'manifest.json',{'status':'running','line':'R13'})
            env=dict(os.environ);env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
            with (folder/'worker.log').open('wb') as log:
                process=subprocess.Popen([sys.executable,'-m','harmonic_weaver.lab.research.heldout_run',
                    '--request',str(folder/'request.json'),'--output',str(folder)],env=env,stdout=log,stderr=log)
            self.processes[ident]=process
            return {'id':ident,'status':'running','line':'R13'}

    def list(self):
        rows=super().list()
        for row in rows:
            if row['status']=='complete':
                try:row.update(verify(self.root/row['id']))
                except (OSError,ValueError,KeyError) as exc:row.update(status='invalid',error=str(exc))
        return rows

    def artifact(self,ident,name):
        if not re.fullmatch(r'[a-f0-9]{32}',ident) or name not in FILES:raise ValueError('Unknown R13 artifact')
        folder=self.root/ident
        verify(folder)
        return folder/name

    def repeat(self,ident):
        return self.start(json.loads(self.artifact(ident,'request.json').read_text()))

    def freeze(self,evaluation,body):
        # The adapter is shared with R01: observed only, causal, unique times, same unit.
        body=SequenceSelection.model_validate(body).model_dump()
        document=snapshot(evaluation,BodyRequest.model_validate(body['selection']))
        return Sequence(id=body['id'],role=body['role'],provider='evaluation_features',
            recording_id=document['provenance']['source_record']['cache_manifest']['media_sha256'],
            subject_group=body['subject_group'],task_id=body['task_id'],
            observations=[{'time_s':row['time_s'],'values':row['values'],
                'cause':json.dumps(row.get('invalid_signals') or row.get('reason') or 'Unavailable',sort_keys=True)[:240] if row['values'] is None else None} for row in document['rows']],
            provenance={**document['provenance'],'feature_ids':document['signal_ids'],'unit':document['unit'],
                'duplicate_control_holds_excluded':document['duplicate_control_holds_excluded']}).model_dump()
