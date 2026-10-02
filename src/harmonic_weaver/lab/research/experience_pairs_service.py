"""Verified-source R10 analysis publication and content retry recovery."""
import json
import threading
import shutil
from pathlib import Path
from typing import Annotated
from pydantic import Field,model_validator
from ..contracts import Contract
from ..cache import sha256_file
from .experience_pairs import Selection,preview
from .experience_pairs_run import run,read_verified,FILES
from .experience_transport_service import TransportService
from .experience_response_service import identity


class Expected(Contract):
    id:Annotated[str,Field(pattern=r'^[a-f0-9]{32}$')]
    manifest_sha256:Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]


class SaveRequest(Selection):
    expected_sources:list[Expected]=Field(min_length=1,max_length=256)

    @model_validator(mode='after')
    def expected(self):
        if [s.id for s in self.expected_sources]!=self.ids():
            raise ValueError('Expected sources must match sorted selected responses')
        return self


class PairService(TransportService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r10-pairs'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def read(self,ident):
        folder=self.folder(ident);manifest=read_verified(folder)
        frozen=json.loads((folder/'request.json').read_text())
        body={'pairs':frozen['selection']['pairs'],
            'expected_sources':[{k:s[k] for k in ('id','manifest_sha256')} for s in frozen['analysis']['sources']]}
        if identity(body)[:32]!=ident:raise ValueError('Pair content ID differs from frozen source selection')
        return {**manifest,'id':ident}

    def start(self,responses,request):
        request=SaveRequest.model_validate(request);body=request.model_dump();ident=identity(body)[:32]
        with self.lock:
            if (self.root/ident).exists():return self.read(ident)
            result=preview(responses,request.model_dump(exclude={'expected_sources'}))
            actual=[{k:s[k] for k in ('id','manifest_sha256')} for s in result['input']['analysis']['sources']]
            if actual!=[s.model_dump() for s in request.expected_sources]:
                raise ValueError('Response sources changed since preview')
            frozen=result['input']
            folder=self.root/ident
            try:
                run(frozen,folder)
                for s in actual:
                    if sha256_file(responses.artifact(s['id'],'manifest.json'))!=s['manifest_sha256']:
                        raise ValueError('Response changed during analysis publication')
            except Exception:
                if folder.is_dir() and not folder.is_symlink():shutil.rmtree(folder)
                raise
            return self.read(ident)

    def artifact(self,ident,name):
        if name not in FILES:raise ValueError('Unknown pair artifact')
        self.read(ident);return self.folder(ident)/name
