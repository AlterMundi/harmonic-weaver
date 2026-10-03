"""Bounded in-memory R08 decode cache; rehash source even on cache hits."""
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
import threading
from .rope_process import file_hash
from .rope_media import probe,_frame_png


class RopeReader:
    def __init__(self,*,max_image_bytes=32_000_000,max_media=4):
        if type(max_image_bytes) is not int or max_image_bytes<0 or type(max_media) is not int or max_media<1:
            raise ValueError('Invalid rope cache budget')
        self.max_image_bytes=max_image_bytes;self.max_media=max_media
        self.media=OrderedDict();self.images=OrderedDict();self.image_bytes=0
        self.lock=threading.RLock()

    def _identity(self,path,*,cancel=None):
        path=Path(path)
        if path.is_symlink() or not path.is_file():raise ValueError('Regular library video required')
        value=file_hash(path,cancel=cancel)
        if path.is_symlink() or not path.is_file():raise ValueError('Video changed during hashing')
        return value

    def probe(self,path,*,cancel=None):
        with self.lock:
            key=self._identity(path,cancel=cancel)
            if key not in self.media:
                result=probe(path,cancel=cancel)
                if result['media_sha256']!=key:raise ValueError('Video changed during preparation')
                self.media[key]=result
                while len(self.media)>self.max_media:self.media.popitem(last=False)
            self.media.move_to_end(key)
            result=deepcopy(self.media[key])
            if self._identity(path,cancel=cancel)!=key:raise ValueError('Video changed during preparation')
            return result

    def frame(self,path,index,expected_sha256,*,cancel=None):
        with self.lock:
            media=self.probe(path,cancel=cancel)
            if media['media_sha256']!=expected_sha256:raise ValueError('Video changed since editor preparation')
            if type(index) is not int or not 0<=index<len(media['frame_times_s']):raise ValueError('Frame outside inventory')
            key=(expected_sha256,index)
            if key not in self.images:
                data=_frame_png(path,index,expected_sha256,media,cancel=cancel)
                if len(data)<=self.max_image_bytes:
                    while self.images and self.image_bytes+len(data)>self.max_image_bytes:
                        _,old=self.images.popitem(last=False);self.image_bytes-=len(old)
                    self.images[key]=data;self.image_bytes+=len(data)
            else:data=self.images[key];self.images.move_to_end(key)
            if self._identity(path,cancel=cancel)!=expected_sha256:raise ValueError('Video changed during image retrieval')
            return data
