"""Local immutable clock-fit inventory, separate from live clocks."""
from pathlib import Path
import shutil
import json
import hashlib
from typing import Annotated
from ..cache import atomic_json
import threading
from uuid import uuid4
from .rope_compare_service import RopeCompareService
from .spatial_clock_run import Input,run,read_verified
from pydantic import Field


Key=Annotated[str,Field(pattern=r'^[a-f0-9]{32}$')]


class SaveRequest(Input):
    idempotency_key:Key|None=None


class SpatialClockService(RopeCompareService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r09-clock-fits'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.receipts=self.root.parent/'r09-clock-fit-starts'
        self.receipts.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def publish(self,kind,selection,key,resolve):
        digest=hashlib.sha256(json.dumps({'kind':kind,'selection':selection},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        with self.lock:
            receipt=self.receipts/f'{key}.json' if key else None
            if receipt is not None and receipt.exists():
                if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>4096:
                    raise ValueError('Regular bounded spatial receipt required')
                previous=json.loads(receipt.read_text())
                if previous.get('request_sha256')!=digest:raise ValueError('Spatial start key reused with different request')
                return {**read_verified(self.folder(previous['id'])),'id':previous['id']}
            frozen=Input.model_validate(resolve())
            ident=uuid4().hex;folder=self.root/ident
            if receipt is not None:atomic_json(receipt,{'id':ident,'request_sha256':digest})
            try:manifest=run(frozen,folder)
            except Exception:
                if folder.is_dir() and not folder.is_symlink():shutil.rmtree(folder)
                raise
            return {**manifest,'id':ident}

    def start(self,request):
        body=SaveRequest.model_validate(request)
        frozen=body.model_dump(exclude={'idempotency_key'})
        return self.publish('declared',frozen,body.idempotency_key,lambda:frozen)

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
        if name not in ('request.json','result.json','manifest.json'):raise ValueError('Unknown clock fit artifact')
        folder=self.folder(ident);read_verified(folder)
        return folder/name

