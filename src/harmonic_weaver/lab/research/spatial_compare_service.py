"""Immutable spatial comparison inventory; imported streams remain declared."""
from pathlib import Path
from uuid import uuid4
import shutil
import json
from pydantic import Field
from ..contracts import Contract
from ..cache import sha256_file
from .spatial_compare import Settings
import threading
from .rope_compare_service import RopeCompareService
from .spatial_compare_run import Input,run,read_verified


class Selection(Contract):
    reference_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    candidate_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    settings:Settings


class SpatialCompareService(RopeCompareService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r09-comparisons'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def start(self,request):
        request=Input.model_validate(request)
        with self.lock:
            ident=uuid4().hex;folder=self.root/ident
            try:manifest=run(request,folder)
            except Exception:
                if folder.is_dir() and not folder.is_symlink():shutil.rmtree(folder)
                raise
            return {**manifest,'id':ident}

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
        with self.lock:
            sources={};streams={}
            for role,ident in (('reference',selection.reference_id),('candidate',selection.candidate_id)):
                manifest=conversions.artifact(ident,'manifest.json')
                sources[role]={'id':ident,'manifest_sha256':sha256_file(manifest)}
                streams[role]=json.loads(conversions.artifact(ident,'result.json').read_text())['stream']
            def unchanged():
                for source in sources.values():
                    if sha256_file(conversions.artifact(source['id'],'manifest.json'))!=source['manifest_sha256']:
                        raise ValueError('Spatial comparison source changed during publication')
            unchanged()
            saved=self.start({'comparison':{**selection.settings.model_dump(),**streams},'sources':sources})
            try:unchanged()
            except Exception:
                shutil.rmtree(self.folder(saved['id']));raise
            return saved
