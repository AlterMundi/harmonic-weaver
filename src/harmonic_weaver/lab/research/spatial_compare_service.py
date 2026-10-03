"""Immutable spatial comparison inventory; imported streams remain declared."""
from pathlib import Path
from uuid import uuid4
import shutil
import json
import hashlib
from ..cache import atomic_json
from .spatial_service import Key
from pydantic import Field
from ..contracts import Contract
from ..cache import sha256_file
from .spatial_compare import Settings
import threading
from .rope_compare_service import RopeCompareService
from .spatial_compare_run import Input,run,read_verified


class SaveRequest(Input):
    idempotency_key:Key|None=None


class Selection(Contract):
    idempotency_key:Key|None=None
    reference_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    candidate_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    settings:Settings


class SpatialCompareService(RopeCompareService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r09-comparisons'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.receipts=self.root.parent/'r09-comparison-starts'
        self.receipts.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def publish(self,kind,selection,key,resolve):
        digest=hashlib.sha256(json.dumps({'kind':kind,'selection':selection},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        with self.lock:
            receipt=self.receipts/f'{key}.json' if key else None
            if receipt is not None and receipt.exists():
                if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>4096:raise ValueError('Regular bounded comparison receipt required')
                previous=json.loads(receipt.read_text())
                if previous.get('request_sha256')!=digest:raise ValueError('Comparison key reused with different request')
                return {**read_verified(self.folder(previous['id'])),'id':previous['id']}
            request,check=resolve()
            request=Input.model_validate(request)
            check()
            ident=uuid4().hex;folder=self.root/ident
            if receipt is not None:atomic_json(receipt,{'id':ident,'request_sha256':digest})
            try:
                manifest=run(request,folder)
                check()
            except Exception:
                if folder.is_dir() and not folder.is_symlink():shutil.rmtree(folder)
                raise
            return {**manifest,'id':ident}

    def start(self,request):
        body=SaveRequest.model_validate(request)
        frozen=body.model_dump(exclude={'idempotency_key'})
        return self.publish('declared',frozen,body.idempotency_key,lambda:(frozen,lambda:None))

    def list(self):
        rows=[]
        with self.lock:
            for folder in sorted(self.root.iterdir()):
                try:
                    self.folder(folder.name);rows.append({**read_verified(folder),'id':folder.name})
                except (OSError,ValueError,KeyError):continue
        return rows

    def artifact(self,ident,name):
        if name not in ('request.json','result.json','manifest.json'):raise ValueError('Unknown spatial comparison artifact')
        folder=self.folder(ident);read_verified(folder)
        return folder/name


    def from_conversions(self,conversions,selection):
        selection=Selection.model_validate(selection)
        def resolve():
            sources={};streams={}
            for role,ident in (('reference',selection.reference_id),('candidate',selection.candidate_id)):
                manifest=conversions.artifact(ident,'manifest.json')
                sources[role]={'id':ident,'manifest_sha256':sha256_file(manifest)}
                streams[role]=json.loads(conversions.artifact(ident,'result.json').read_text())['stream']
            def unchanged():
                for source in sources.values():
                    if sha256_file(conversions.artifact(source['id'],'manifest.json'))!=source['manifest_sha256']:
                        raise ValueError('Spatial comparison source changed during publication')
            return {'comparison':{**selection.settings.model_dump(),**streams},'sources':sources},unchanged
        return self.publish('conversions',selection.model_dump(exclude={'idempotency_key'}),selection.idempotency_key,resolve)
