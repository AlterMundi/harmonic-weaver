"""Optional file-video export from sampled capture timeline; originals stay put."""
import json
from pathlib import Path
import subprocess
import threading
from uuid import uuid4

from pydantic import Field
from .contracts import Contract, Number
from .cache import atomic_json, sha256_file
from .capture_timeline import frame_plan


class ExportSettings(Contract):
    fps: int = Field(default=30,ge=1,le=120)
    width: int = Field(default=1280,ge=64,le=1920,multiple_of=2)
    height: int = Field(default=720,ge=64,le=1080,multiple_of=2)
    offset_s: Number = Field(default=0,ge=-5,le=5)
    max_gap_s: Number = Field(default=.25,gt=0,le=5)


def read_lines(path, project=lambda row:row):
    with Path(path).open() as handle:
        return [project(json.loads(line)) for line in handle if line.strip()]


def render_capture(manifest, folder, settings, *, cancelled=None, progress=None):
    import cv2
    import numpy as np
    settings=ExportSettings.model_validate(settings)
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    session=Path(manifest['directory']);driver=manifest['shaper'];audio=Path(driver['directory'])/'audio.wav'
    if manifest['status']!='complete' or driver['status']!='complete':
        raise ValueError('Only confirmed complete captures can be exported')
    for name in ('timeline.jsonl','events.jsonl'):
        if sha256_file(session/name)!=manifest['hashes'][name]:raise ValueError(f'Capture artifact changed: {name}')
    blocks_path=Path(driver['directory'])/'blocks.jsonl'
    blocks=read_lines(blocks_path,lambda row:{key:row[key] for key in
        ('sample_rate','capture_file_sample_start','capture_frames','generated_monotonic_s')})
    observations=read_lines(session/'timeline.jsonl',lambda row:{
        'sampled_monotonic_s':row['sampled_monotonic_s'],
        'state':{key:row['state'].get(key) for key in ('source','session','runtime')}})
    # Audio count and per-block digital clock are the authoritative duration.
    import soundfile as sf
    info=sf.info(audio)
    if not blocks or info.frames!=sum(b['capture_frames'] for b in blocks) or info.samplerate!=blocks[0]['sample_rate']:
        raise ValueError('PCM and block manifest disagree')
    inputs={'audio.wav':sha256_file(audio),'blocks.jsonl':sha256_file(blocks_path),**manifest['hashes']}
    output=folder/'capture.mkv';temporary=folder/'capture.partial.mkv'
    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo',
             '-pix_fmt','bgr24','-s',f'{settings.width}x{settings.height}','-r',str(settings.fps),
             '-i','pipe:0','-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264',
             '-preset','veryfast','-threads','2','-pix_fmt','yuv420p','-c:a','pcm_f32le',str(temporary)]
    decoder=None;path=None;last_position=None;image=None;count=0;gaps={};sources={}
    report={'schema_version':1,'capture_id':manifest['id'],'settings':settings.model_dump(),
            'alignment':'sampled source hold against generated digital audio callback clock',
            'limits':['Not a measurement of audiovisual or acoustic latency',
                      'No camera pixels: camera/missing/stale intervals rendered black',
                      'Video may outlast PCM by less than one output frame',
                      'Original file identity is declared, not rehashed during export',
                      'No skeleton or harmonic figure overlay in this export'],
            'input_hashes':inputs,'status':'rendering','frames':0,'gaps':gaps,'sources':sources}
    atomic_json(folder/'manifest.json',report)
    process=None
    try:
        with (folder/'encoder.log').open('wb') as log, (folder/'frames.jsonl').open('w') as timeline:
            process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
            for row in frame_plan(blocks,observations,**{k:getattr(settings,k) for k in ('fps','offset_s','max_gap_s')}):
                if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
                source=row['source'];frame=None
                if source:
                    if source['path']!=path:
                        if decoder is not None:decoder.release()
                        path=source['path'];decoder=cv2.VideoCapture(path);last_position=None;image=None
                        if not decoder.isOpened():raise ValueError('Source video is unavailable or undecodable')
                        sources[path]={'media_id':source['media_id'],'identity_verified':False}
                    if source['position_s']!=last_position:
                        decoder.set(cv2.CAP_PROP_POS_MSEC,source['position_s']*1000)
                        ok,image=decoder.read();last_position=source['position_s']
                        if not ok:raise ValueError('Could not decode requested source position')
                    h,w=image.shape[:2];scale=min(settings.width/w,settings.height/h)
                    resized=cv2.resize(image,(max(1,round(w*scale)),max(1,round(h*scale))))
                    frame=np.zeros((settings.height,settings.width,3),dtype=np.uint8)
                    rh,rw=resized.shape[:2];y=(settings.height-rh)//2;x=(settings.width-rw)//2
                    frame[y:y+rh,x:x+rw]=resized
                else:
                    frame=np.zeros((settings.height,settings.width,3),dtype=np.uint8)
                    gaps[row['reason']]=gaps.get(row['reason'],0)+1
                process.stdin.write(frame.tobytes());timeline.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
                count+=1
                if progress:progress(count)
            process.stdin.close()
            if process.wait(timeout=30)!=0:raise ValueError('Encoder failed: '+(folder/'encoder.log').read_text()[-2000:])
        temporary.replace(output)
        report.update(status='complete',frames=count,output={'file':output.name,'sha256':sha256_file(output)},
                      frame_plan_sha256=sha256_file(folder/'frames.jsonl'))
        atomic_json(folder/'manifest.json',report);return report
    except Exception as exc:
        if process is not None and process.poll() is None:process.kill();process.wait(timeout=5)
        report.update(status='failed',error=str(exc),frames=count)
        atomic_json(folder/'manifest.json',report)
        raise
    finally:
        if decoder is not None:decoder.release()


class CaptureExports:
    def __init__(self,captures):
        self.captures=captures;self.thread=None;self.cancelled=threading.Event();self.job={'status':'idle'}
        self.lock=threading.Lock()

    def start(self,ident,settings):
        settings=ExportSettings.model_validate(settings)
        with self.lock:
            if self.thread and self.thread.is_alive():raise ValueError('Ya hay una exportación activa')
            jobs={j['id']:j for j in self.captures.list()}
            if ident not in jobs or jobs[ident]['status']!='complete':raise ValueError('Elegí una captura completa')
            manifest=jobs[ident];folder=Path(manifest['directory'])/'exports'/uuid4().hex
            self.job={'status':'rendering','capture_id':ident,'directory':str(folder),'frames':0}
            self.cancelled.clear()
            def work():
                try:
                    report=render_capture(manifest,folder,settings,cancelled=self.cancelled,
                                          progress=lambda count:self.job.update(frames=count))
                    self.job.update(report)
                except Exception as exc:
                    self.job.update(status='failed',error=str(exc))
                    if folder.exists() and not (folder/'manifest.json').exists():
                        try: atomic_json(folder/'manifest.json',self.snapshot())
                        except OSError: pass
            self.thread=threading.Thread(target=work,daemon=True,name='capture-export');self.thread.start()
            return self.snapshot()

    def snapshot(self):return json.loads(json.dumps(dict(self.job)))
    def cancel(self):self.cancelled.set();return self.snapshot()
    def close(self):
        self.cancelled.set()
        if self.thread:self.thread.join()
