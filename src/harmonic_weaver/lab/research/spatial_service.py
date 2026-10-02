"""Local immutable conversion inventory, separate from the live instrument."""
from pathlib import Path
import shutil
import threading
from uuid import uuid4
from .rope_compare_service import RopeCompareService
from .spatial_run import Input,run,read_verified


class SpatialService(RopeCompareService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r09-conversions'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def start(self,request):
        frozen=Input.model_validate(request)
        with self.lock:
            ident=uuid4().hex;folder=self.root/ident
            try:manifest=run(frozen,folder)
            except Exception:
                if folder.is_dir() and not folder.is_symlink():shutil.rmtree(folder)
                raise
            return {**manifest,'id':ident}

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
        if name not in ('request.json','result.json','manifest.json'):raise ValueError('Unknown spatial conversion artifact')
        folder=self.folder(ident);read_verified(folder)
        return folder/name
