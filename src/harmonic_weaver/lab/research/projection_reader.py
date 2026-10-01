"""Bounded verification cache for repeated local model-state window reads."""
from collections import OrderedDict
from pathlib import Path
import stat
import threading
from .resonator_artifacts import verify as verify_arm
from .mechanism_run import verify as verify_pair


class ProjectionReader:
    def __init__(self):
        self.lock=threading.RLock();self.cache=OrderedDict();self.capacity=8

    def fingerprint(self,folder,arm):
        folder=Path(folder)
        directories=[folder]
        files=['manifest.json','input.json','request.json']
        components=['manifest.json','input.json','request.json','sum.wav','voices.wav','quadrature.wav']
        if arm=='single':files=components
        else:
            files+=['result.json'];directories+=[folder/'excited',folder/'mapped']
            files += [f'{a}/{name}' for a in ('excited','mapped') for name in components]
        result=[]
        for path,kind in [(d,'directory') for d in directories]+[(folder/name,'file') for name in files]:
            try:info=path.lstat()
            except OSError as exc:raise ValueError('Projection artifact unavailable') from exc
            if not (stat.S_ISDIR(info.st_mode) if kind=='directory' else stat.S_ISREG(info.st_mode)):
                raise ValueError('Regular projection artifacts required')
            result.append((str(path),info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,info.st_ctime_ns))
        return tuple(result)

    def prepare(self,folder,arm):
        folder=Path(folder);key=(str(folder.absolute()),arm)
        with self.lock:
            try:before=self.fingerprint(folder,arm)
            except ValueError:self.cache.pop(key,None);raise
            cached=self.cache.get(key)
            if cached is not None and cached[0]==before:
                self.cache.move_to_end(key);return cached[1],before
            self.cache.pop(key,None)
            if arm=='single':manifest=verify_arm(folder)
            else:
                verify_pair(folder);manifest=verify_arm(folder/arm)
            if self.fingerprint(folder,arm)!=before:
                raise ValueError('Projection artifacts changed during verification')
            self.cache[key]=(before,manifest)
            while len(self.cache)>self.capacity:self.cache.popitem(last=False)
            return manifest,before

    def check(self,folder,arm,expected):
        with self.lock:
            try:
                if self.fingerprint(folder,arm)!=expected:
                    raise ValueError('Projection artifacts changed during read')
            except ValueError:
                self.cache.pop((str(Path(folder).absolute()),arm),None);raise

    def close(self):
        with self.lock:self.cache.clear()
