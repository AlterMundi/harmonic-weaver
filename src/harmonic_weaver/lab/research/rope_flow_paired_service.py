"""Paired banks resolved from verified frozen endpoint benchmark artifacts."""
import json
import hashlib
import shutil
import threading
from pathlib import Path
from typing import Annotated
from uuid import uuid4
from pydantic import Field,model_validator
from ..contracts import Contract
from ..cache import sha256_file,atomic_json
from .rope_compare_service import RopeCompareService
from .rope_flow_paired_run import Input,Identifier,run,read_verified


class Selection(Contract):
    conditions:dict[Annotated[str,Field(min_length=1,max_length=80)],Identifier]=Field(min_length=2,max_length=16)

    idempotency_key:Identifier|None=None

    @model_validator(mode='after')
    def distinct(self):
        if len(set(self.conditions.values()))!=len(self.conditions):
            raise ValueError('Select distinct benchmark artifacts for paired conditions')
        return self


class RopeFlowPairedService(RopeCompareService):
    def __init__(self,data_dir,benchmarks):
        self.root=Path(data_dir)/'research/r08-flow-paired'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.receipts=self.root.parent/'r08-flow-paired-starts'
        self.receipts.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock();self.benchmarks=benchmarks

    def start(self,selection):
        selection=Selection.model_validate(selection)
        digest=hashlib.sha256(json.dumps(selection.model_dump(exclude={'idempotency_key'}),sort_keys=True,separators=(',',':')).encode()).hexdigest()
        with self.lock:
            receipt=self.receipts/f'{selection.idempotency_key}.json' if selection.idempotency_key else None
            if receipt is not None and receipt.exists():
                if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>4096:
                    raise ValueError('Regular bounded paired receipt required')
                previous=json.loads(receipt.read_text())
                if previous.get('selection_sha256')!=digest:raise ValueError('Paired start key reused with different selection')
                manifest=read_verified(self.folder(previous['id']))
                return {**manifest,'id':previous['id'],'source_resolution':'frozen_receipt_recovery'}
            sources={};conditions={} 
            for name,ident in selection.conditions.items():
                manifest=self.benchmarks.artifact(ident,'manifest.json')
                sources[name]={'id':ident,'manifest_sha256':sha256_file(manifest)}
                frozen=json.loads(self.benchmarks.artifact(ident,'request.json').read_text())
                conditions[name]=frozen['benchmark']
            frozen=Input.model_validate({'benchmark':{'conditions':conditions},'sources':sources})
            def unchanged():
                for source in sources.values():
                    path=self.benchmarks.artifact(source['id'],'manifest.json')
                    if sha256_file(path)!=source['manifest_sha256']:
                        raise ValueError('Paired source changed during publication')
            unchanged();ident=uuid4().hex;folder=self.root/ident
            if receipt is not None:atomic_json(receipt,{'id':ident,'selection_sha256':digest})
            try:
                manifest=run(frozen,folder);unchanged()
            except Exception:
                if folder.is_dir() and not folder.is_symlink():shutil.rmtree(folder)
                raise
            return {**manifest,'id':ident,'source_resolution':'verified_local_benchmarks_at_creation'}

    def list(self):
        with self.lock:
            rows=[]
            for folder in sorted(self.root.iterdir()):
                try:
                    self.folder(folder.name)
                    rows.append({**read_verified(folder),'id':folder.name})
                except (OSError,ValueError,KeyError):continue
            return rows

    def artifact(self,ident,name):
        if name not in ('request.json','result.json','manifest.json'):raise ValueError('Unknown paired artifact')
        folder=self.folder(ident);read_verified(folder)
        return folder/name
