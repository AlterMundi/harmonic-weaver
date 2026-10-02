"""Bounded streaming PNG sequence, one owned cancellable decoder process."""
import os
import selectors
import subprocess
import time
import zlib
from pathlib import Path
from .rope_process import DecodeCancelled


def png_frames(command,count,*,max_frame_bytes=32_000_000,timeout=60,cancel=None):
    if type(count)!=int or not 1<=count<=120 or max_frame_bytes<33 or timeout<=0:raise ValueError('Invalid PNG sequence budget')
    if cancel is not None and cancel.is_set():raise DecodeCancelled('Sequence decoding cancelled')
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    selector=selectors.DefaultSelector();deadline=time.monotonic()+timeout
    buffer=bytearray();frame=bytearray();seen=0;eof=False
    try:
        os.set_blocking(process.stdout.fileno(),False);selector.register(process.stdout,selectors.EVENT_READ)
        while not eof or process.poll() is None:
            if cancel is not None and cancel.is_set():raise DecodeCancelled('Sequence decoding cancelled')
            remaining=deadline-time.monotonic()
            if remaining<=0:raise ValueError('Sequence decoding timed out')
            if eof:
                try:process.wait(timeout=min(.05,remaining))
                except subprocess.TimeoutExpired:pass
                continue
            for key,_ in selector.select(min(.05,remaining)):
                data=os.read(key.fileobj.fileno(),65536)
                if not data:eof=True;selector.unregister(key.fileobj);break
                buffer.extend(data)
                while True:
                    if not frame:
                        if len(buffer)<8:break
                        if buffer[:8]!=b'\x89PNG\r\n\x1a\n' or seen>=count:raise ValueError('Unexpected PNG sequence frame')
                        frame.extend(buffer[:8]);del buffer[:8]
                    if len(buffer)<8:break
                    length=int.from_bytes(buffer[:4],'big');kind=bytes(buffer[4:8]);size=length+12
                    if length>1_000_000 or len(frame)+size>max_frame_bytes:raise ValueError('PNG chunk/frame budget exceeded')
                    if len(buffer)<size:break
                    chunk=bytes(buffer[:size]);del buffer[:size]
                    if zlib.crc32(chunk[4:-4])!=int.from_bytes(chunk[-4:],'big'):raise ValueError('PNG chunk CRC mismatch')
                    if len(frame)==8 and (kind!=b'IHDR' or length!=13):raise ValueError('PNG image header required')
                    frame.extend(chunk)
                    if kind==b'IEND':
                        if length!=0:raise ValueError('Invalid PNG image end')
                        seen+=1;yield bytes(frame);frame.clear()
                        if cancel is not None and cancel.is_set():raise DecodeCancelled('Sequence decoding cancelled')
        if process.returncode or seen!=count or buffer or frame:raise ValueError('Incomplete or failed PNG sequence')
    finally:
        selector.close()
        if process.poll() is None:process.kill()
        process.wait();process.stdout.close()


def sequence(path,start,count,sha256,media,*,cancel=None):
    from .rope_process import file_hash
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Regular sequence source required')
    if media.get('media_sha256')!=sha256:raise ValueError('Sequence inventory identity mismatch')
    if type(start)!=int or start<0 or type(count)!=int or not 1<=count<=120 or start+count>len(media['frame_times_s']):raise ValueError('Sequence outside decoded frame inventory')
    if media['width_px']*media['height_px']>4_000_000:raise ValueError('Sequence image dimensions exceed budget')
    if file_hash(path,cancel=cancel)!=sha256:raise ValueError('Sequence source identity mismatch')
    command=['ffmpeg','-v','error','-noautorotate','-i',str(path),'-map','0:v:0',
             '-vf',f'select=between(n\\,{start}\\,{start+count-1})','-vsync','0',
             '-frames:v',str(count),'-f','image2pipe','-c:v','png','pipe:1']
    stream=png_frames(command,count,cancel=cancel)
    try:yield from stream
    finally:stream.close()
    if path.is_symlink() or not path.is_file() or file_hash(path,cancel=cancel)!=sha256:raise ValueError('Sequence source changed during decoding')
