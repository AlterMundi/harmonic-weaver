"""Opt-in bounded storage of processed camera previews, outside tracking/audio."""
import base64
import fcntl
from collections import deque
import hashlib
from pathlib import Path
import threading
import time

from .cache import atomic_json, sha256_file


class CameraCapture:
    def __init__(self, folder, *, queue_frames=8, max_frames=10000, max_bytes=256*1024*1024):
        self.folder=Path(folder)/'camera';self.folder.mkdir(mode=0o700)
        self.writer_lock=(self.folder/'writer.lock').open('w+b')
        fcntl.flock(self.writer_lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.queue=deque(maxlen=queue_frames)
        self.max_frames,self.max_bytes=max_frames,max_bytes
        self.stop_event=threading.Event();self.error=None
        self.offer_lock=threading.Lock()
        self.accepted=self.written=self.bytes=self.sequence_gaps=0
        self.last=None;self.status='recording'
        self.thread=threading.Thread(target=self._write,daemon=True,name='camera-capture-writer')
        try:
            atomic_json(self.folder/'manifest.json',self.snapshot());self.thread.start()
        except Exception:
            self.writer_lock.close()
            raise

    def offer(self, packet):
        with self.offer_lock:
            if self.stop_event.is_set():raise ValueError('Camera capture is closed')
            return self._offer(packet)

    def _offer(self, packet):
        if self.error:raise ValueError(self.error)
        if packet is None:return None
        key=(packet['stream_id'],packet['sequence'])
        if key==self.last:return None
        if self.last and key[0]==self.last[0] and key[1]<self.last[1]:
            raise ValueError('Camera sequence moved backwards within stream')
        encoded=packet['jpeg']
        if len(encoded)>6*1024*1024:raise ValueError('Camera preview exceeds frame size limit')
        jpeg=base64.b64decode(encoded,validate=True)
        if self.accepted>=self.max_frames or self.bytes+len(jpeg)>self.max_bytes:
            raise ValueError('Camera capture storage budget exceeded')
        if len(self.queue)>=self.queue.maxlen:raise ValueError('Camera capture queue overflow')
        gap=max(0,key[1]-self.last[1]-1) if self.last and key[0]==self.last[0] else 0
        ref={k:v for k,v in packet.items() if k!='jpeg'}
        ref.update(file=f'{self.accepted:08d}.jpg',sha256=hashlib.sha256(jpeg).hexdigest(),
                   collector_monotonic_s=time.monotonic(),sequence_gap=gap)
        self.queue.append((jpeg,ref));self.accepted+=1;self.bytes+=len(jpeg)
        self.sequence_gaps+=gap;self.last=key
        return ref

    def _write(self):
        import json
        try:
            with (self.folder/'frames.jsonl').open('w') as index:
                while not self.stop_event.is_set() or self.queue:
                    try:jpeg,ref=self.queue.popleft()
                    except IndexError:self.stop_event.wait(.005);continue
                    (self.folder/ref['file']).write_bytes(jpeg)
                    index.write(json.dumps(ref,sort_keys=True,allow_nan=False)+'\n');index.flush()
                    self.written+=1
            self.status='failed' if self.error else 'complete'
        except Exception as exc:self.error=str(exc);self.status='failed'
        finally:
            try:atomic_json(self.folder/'manifest.json',self.snapshot())
            except OSError as exc:self.error=str(exc);self.status='failed'
            finally:self.writer_lock.close()

    def snapshot(self):
        return {'status':self.status,'error':self.error,'directory':str(self.folder),
                'accepted_frames':self.accepted,'written_frames':self.written,'jpeg_bytes':self.bytes,
                'observed_sequence_gaps':self.sequence_gaps,'queue_frames':self.queue.maxlen,
                'max_frames':self.max_frames,'max_bytes':self.max_bytes,
                'index_sha256':sha256_file(self.folder/'frames.jsonl') if not self.thread.is_alive() and (self.folder/'frames.jsonl').is_file() else None,
                'limits':['Processed JPEG preview, not raw camera acquisition',
                          'Sequence gaps include acquisition/pose/collector decimation; cause not inferred',
                          'Captured/available/collector clocks are software timestamps, not measured AV latency']}

    def close(self, error=None):
        with self.offer_lock:
            if error:self.error=error
            self.stop_event.set()
        self.thread.join()
        if self.error:self.status='failed'
        state=self.snapshot();atomic_json(self.folder/'manifest.json',state);return state
