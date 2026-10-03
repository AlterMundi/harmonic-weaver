"""Explicit local measurement publication; no acquisition or silent processing."""
import json
import threading
from pathlib import Path
from uuid import uuid4
from .physiology_sensitivity import Request
from .physiology_sensitivity_run import run,read_verified,FILES
from .experience_response_service import identity
from .experience_transport_service import TransportService


class SensitivityService(TransportService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r12-clock-sensitivity'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def read(self,ident):
        folder=self.folder(ident);manifest=read_verified(folder)
        frozen=Request.model_validate_json((folder/'request.json').read_text())
        if identity(frozen.model_dump())[:32]!=ident:raise ValueError('Physiology content ID differs from frozen request')
        return {**manifest,'id':ident}

    def start(self,request):
        request=Request.model_validate(request);ident=identity(request.model_dump())[:32]
        with self.lock:
            if (self.root/ident).exists():return self.read(ident)
            staging=self.root/f'.pending-{uuid4().hex}'
            run(request,staging)
            # Publish only after all artifacts recompute successfully. Failed staging
            # remains diagnostic; retry uses a new staging folder, never overwrites raw data.
            read_verified(staging)
            try:staging.rename(self.root/ident)
            except FileExistsError:
                return self.read(ident)
            return self.read(ident)

    def artifact(self,ident,name):
        if name not in FILES:raise ValueError('Unknown physiology measurement artifact')
        self.read(ident);return self.folder(ident)/name
