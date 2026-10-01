"""Bounded, seekable float32 listening view; authoritative R05 WAV stays DOUBLE."""
import math
import re
import struct
from pathlib import Path
import numpy as np
import soundfile as sf
from fastapi.responses import Response,StreamingResponse


def preview_response(path,*,gain=1.,range_header=None):
    path=Path(path)
    if not math.isfinite(gain) or not 0<=gain<=10:raise ValueError('Preview gain in 0–10 required')
    if path.is_symlink() or not path.is_file():raise ValueError('Regular preview source required')
    info=sf.info(path)
    if info.channels!=1 or info.subtype!='DOUBLE' or info.format!='WAV':
        raise ValueError('R05 mono DOUBLE source required')
    data_size=info.frames*4;size=44+data_size
    if size-8>=2**32:raise ValueError('Preview exceeds RIFF limit')
    header=struct.pack('<4sI4s4sIHHIIHH4sI',b'RIFF',size-8,b'WAVE',b'fmt ',16,
                       3,1,info.samplerate,info.samplerate*4,4,32,b'data',data_size)
    start=0;end=size;status=200
    if range_header is not None:
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',range_header)
        if not match or not any(match.groups()):
            return Response(status_code=416,headers={'Content-Range':f'bytes */{size}'})
        a,b=match.groups()
        if a:
            start=int(a);end=min(size,int(b)+1) if b else size
        else:start=max(0,size-int(b))
        if start>=size or end<=start:
            return Response(status_code=416,headers={'Content-Range':f'bytes */{size}'})
        status=206
    before=path.stat()
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    def blocks():
        if path.is_symlink() or identity(path.stat())!=identity(before):raise ValueError('Preview source changed')
        if start<44:yield header[start:min(end,44)]
        if end<=44:return
        data_start=max(0,start-44);data_end=end-44
        sample=data_start//4;last=(data_end+3)//4
        with sf.SoundFile(path) as source:
            source.seek(sample)
            while sample<last:
                if path.is_symlink() or identity(path.stat())!=identity(before):raise ValueError('Preview source changed')
                count=min(4096,last-sample);values=source.read(count,dtype='float64')
                if len(values)!=count or not np.isfinite(values).all():raise ValueError('Preview source PCM invalid')
                data=(values*gain).astype('<f4').tobytes()
                a=max(0,data_start-sample*4);b=min(len(data),data_end-sample*4)
                yield data[a:b];sample+=count
        if identity(path.stat())!=identity(before):raise ValueError('Preview source changed')
    headers={'Content-Length':str(end-start),'Accept-Ranges':'bytes',
             'X-R05-Preview':'float64-to-float32; no normalization; no limiter',
             'X-R05-Preview-Gain':str(gain),'Cache-Control':'no-store'}
    if status==206:headers['Content-Range']=f'bytes {start}-{end-1}/{size}'
    return StreamingResponse(blocks(),status_code=status,media_type='audio/wav',headers=headers)
