"""Small bounded transfer jobs, separate from PCM/owned subprocess jobs."""
from pathlib import Path
from uuid import uuid4
import re
import threading
from .membrane_transfer_run import run,verify


class TransferService:
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r07-transfer'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def folder(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Invalid transfer id')
        folder=self.root/ident
        if folder.is_symlink() or not folder.is_dir():raise ValueError('Transfer job unavailable')
        return folder

    def start(self,request):
        with self.lock:
            ident=uuid4().hex
            manifest=run(request,self.root/ident)
            return {**manifest,'id':ident}

    def list(self):
        with self.lock:
            rows=[]
            for folder in sorted(self.root.iterdir()):
                if re.fullmatch('[a-f0-9]{32}',folder.name) and folder.is_dir() and not folder.is_symlink():
                    try:rows.append({**verify(folder),'id':folder.name})
                    except (OSError,ValueError,KeyError):continue
            return rows

    def artifact(self,ident,name):
        if name not in ('request.json','result.json','manifest.json'):raise ValueError('Unknown transfer artifact')
        folder=self.folder(ident);verify(folder)
        return folder/name
