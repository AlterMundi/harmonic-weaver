"""Persistent owned triangulation workers; retries recover receipts, never relaunch."""
import hashlib
import re
import json
import threading
import subprocess
from pathlib import Path
from uuid import uuid4
from typing import Annotated
from pydantic import Field
from ..cache import atomic_json
from .coincidence_service import CoincidenceService
from .spatial_multiview import Request
from .spatial_multiview_worker import verify


class StartRequest(Request):
    idempotency_key:Annotated[str,Field(pattern='^[a-f0-9]{32}$')]|None=None


class MultiviewService(CoincidenceService):
    line='R09'
    module='harmonic_weaver.lab.research.spatial_multiview_worker'
    artifacts=('request.json','result.json','manifest.json')

    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r09-multiview';self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.receipts=self.root.parent/'r09-multiview-starts';self.receipts.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock();self.processes={};self.closed=False

    def start(self,body):
        parsed=StartRequest.model_validate(body)
        request=Request.model_validate(parsed.model_dump(exclude={'idempotency_key'})).model_dump()
        digest=hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        with self.lock:
            receipt=self.receipts/f'{parsed.idempotency_key}.json' if parsed.idempotency_key else None
            if receipt is not None and receipt.exists():
                if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>4096:raise ValueError('Regular bounded multiview receipt required')
                previous=json.loads(receipt.read_text())
                if not isinstance(previous.get('id'),str) or not re.fullmatch('[a-f0-9]{32}',previous['id']):raise ValueError('Invalid multiview receipt ID')
                if previous.get('request_sha256')!=digest:raise ValueError('Multiview key reused with different inputs')
                if not (self.root/previous['id']).exists():return {'id':previous['id'],'line':'R09','status':'interrupted','error':'Start receipt has no frozen job; use a new explicit attempt'}
                return self.report(previous['id'])
            if self.closed:raise ValueError('Multiview service is closed')
            if any(p.poll() is None for p in self.processes.values()):raise ValueError('A multiview worker is already active')
            ident=uuid4().hex
            if receipt is not None:atomic_json(receipt,{'id':ident,'request_sha256':digest})
            return self._start({'request.json':request},ident=ident)

    def report(self,ident):
        report=super().report(ident)
        if report['status']=='complete':
            try:report.update(verify(self.folder(ident)))
            except (OSError,ValueError) as exc:report.update(status='invalid',error=str(exc))
        return report

    def verification(self,ident,*,recompute=False):
        return {**verify(self.folder(ident),recompute=recompute),'id':ident}

    def repeat(self,ident):
        return self.start(json.loads(self.artifact(ident,'request.json').read_text()))

    def close(self):
        with self.lock:
            self.closed=True
            for ident,process in self.processes.items():
                if process.poll() is None:
                    try:self.cancel(ident,shutdown=True)
                    except (OSError,ValueError):
                        # Corrupt artifacts cannot prevent stopping an owned child.
                        if process.poll() is None:
                            process.terminate()
                            try:process.wait(timeout=5)
                            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
