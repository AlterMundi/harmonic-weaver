"""Explicit local raw observation publication; no acquisition or silent processing."""
import json
import threading
from pathlib import Path
from .neuro_observations import Stream
from .neuro_run import run,read_verified,FILES
from .experience_response_service import identity
from .experience_transport_service import TransportService


class NeuroService(TransportService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r11-observations'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def read(self,ident):
        folder=self.folder(ident);manifest=read_verified(folder)
        frozen=Stream.model_validate_json((folder/'request.json').read_text())
        if identity(frozen.model_dump())[:32]!=ident:raise ValueError('Neuro content ID differs from frozen stream')
        return {**manifest,'id':ident}

    def start(self,request):
        stream=Stream.model_validate(request);ident=identity(stream.model_dump())[:32]
        with self.lock:
            if (self.root/ident).exists():return self.read(ident)
            run(stream,self.root/ident)
            return self.read(ident)

    def artifact(self,ident,name):
        if name not in FILES:raise ValueError('Unknown neuro observation artifact')
        self.read(ident);return self.folder(ident)/name
