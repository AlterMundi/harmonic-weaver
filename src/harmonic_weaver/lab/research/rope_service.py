"""Local immutable rope revision inventory; caller resolves authorized media."""
from pathlib import Path
from uuid import uuid4
import threading
import re
from .rope_run import run,verify
from .rope_annotations import Annotation


class RopeService:
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r08'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def folder(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Invalid rope revision id')
        folder=self.root/ident
        if folder.is_symlink() or not folder.is_dir():raise ValueError('Rope revision unavailable')
        return folder

    def save(self,annotation,media_path,*,parent_id=None):
        annotation=Annotation.model_validate(annotation)
        with self.lock:
            parent=self.folder(parent_id) if parent_id is not None else None
            ident=uuid4().hex
            manifest=run(annotation,media_path,self.root/ident,parent=parent)
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
        if name not in ('annotation.json','media.json','result.json','manifest.json'):raise ValueError('Unknown rope artifact')
        folder=self.folder(ident);verify(folder)
        return folder/name

    def rebind(self,ident,media_path):
        from .rope_media import bind
        folder=self.folder(ident);verify(folder)
        annotation=Annotation.model_validate_json((folder/'annotation.json').read_text())
        result=bind(annotation,media_path)
        verify(folder)
        return result
