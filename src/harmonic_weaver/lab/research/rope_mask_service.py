"""Local proposal inventory, with explicit current-source recomputation."""
from pathlib import Path
from uuid import uuid4
import re,json,threading
from .rope_mask_run import Request,run,verify


class RopeMaskService:
    def __init__(self,data_dir,reader):
        self.root=Path(data_dir)/'research/r08-masks';self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.reader=reader;self.lock=threading.RLock()
    def folder(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Invalid proposal id')
        folder=self.root/ident
        if folder.is_symlink() or not folder.is_dir():raise ValueError('Proposal unavailable')
        return folder
    def start(self,request,path):
        with self.lock:
            ident=uuid4().hex;manifest=run(request,path,self.root/ident,self.reader)
            return {**manifest,'id':ident}
    def list(self):
        with self.lock:
            rows=[]
            for folder in sorted(self.root.iterdir()):
                if re.fullmatch('[a-f0-9]{32}',folder.name) and folder.is_dir() and not folder.is_symlink():
                    try:
                        manifest=verify(folder);request=Request.model_validate_json((folder/'request.json').read_text())
                        rows.append({**manifest,'id':folder.name,'media_sha256':request.media_sha256,'frame_index':request.frame_index,'time_s':request.time_s})
                    except (OSError,ValueError,KeyError):continue
            return rows
    def artifact(self,ident,name):
        if name not in ('request.json','result.json','manifest.json'):raise ValueError('Unknown proposal artifact')
        folder=self.folder(ident);verify(folder);return folder/name
    def reverify(self,ident,path):
        with self.lock:
            folder=self.folder(ident);verify(folder,path=path,reader=self.reader)
            result=json.loads((folder/'result.json').read_text());verify(folder)
            return result
