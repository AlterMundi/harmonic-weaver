"""Optional file-video export from sampled capture timeline; originals stay put."""
import json
from pathlib import Path
from typing import Literal
import subprocess
import threading
import time
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
    camera_clock: Literal['collector_monotonic_s','available_monotonic_s','captured_monotonic_s'] = 'collector_monotonic_s'
    recovered_prefix: bool = False
    skeleton_overlay: bool = False
    skeleton_people: Literal['selected','all'] = 'selected'
    skeleton_confidence: Number = Field(default=0,ge=0,le=1)
    skeleton_max_offset_s: Number = Field(default=.1,ge=0,le=1)
    skeleton_line_px: int = Field(default=2,ge=1,le=12)
    browser_preview: bool = False
    preview_audio_kbps: int = Field(default=192,ge=64,le=320)


def browser_preview(folder, settings, cancelled):
    temporary=folder/'preview.partial.mp4';output=folder/'preview.mp4'
    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(folder/'capture.mkv'),
        '-map','0:v:0','-map','0:a:0','-c:v','copy','-c:a','aac','-b:a',f'{settings.preview_audio_kbps}k',
        '-threads','2','-movflags','+faststart',str(temporary)]
    with (folder/'preview-encoder.log').open('wb') as log:
        process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=log)
        try:
            deadline=time.monotonic()+300
            while process.poll() is None:
                if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
                if time.monotonic()>deadline:raise ValueError('Browser preview encoder timed out')
                try:process.wait(timeout=.1)
                except subprocess.TimeoutExpired:pass
            if process.returncode:raise ValueError('Browser preview encoder failed: '+(folder/'preview-encoder.log').read_text()[-2000:])
            if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
        finally:
            if process.poll() is None:process.kill();process.wait(timeout=5)
    temporary.replace(output)
    return {'status':'complete','file':output.name,'sha256':sha256_file(output),
        'video':'copied H264 stream','audio':'lossy AAC derived from confirmed PCM',
        'audio_kbps':settings.preview_audio_kbps,'limits':['AAC may introduce padding and compression; not exact PCM']}


def read_lines(path, project=lambda row:row):
    with Path(path).open() as handle:
        return [project(json.loads(line)) for line in handle if line.strip()]


def render_capture(manifest, folder, settings, *, cancelled=None, progress=None):
    import cv2
    import numpy as np
    settings=ExportSettings.model_validate(settings)
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    session=Path(manifest['directory']);driver=manifest['shaper'];audio=Path(driver['directory'])/'audio.wav'
    partial=None
    if settings.recovered_prefix:
        from .capture_recovered_input import recovered_input
        partial=recovered_input(manifest)
        session=Path(partial['journal']['timeline.jsonl']).parent
        audio=Path(partial['audio']);driver={'directory':str(audio.parent)}
    if not partial and (manifest['status']!='complete' or driver['status']!='complete'):
        raise ValueError('Only confirmed complete captures can be exported')
    for name in ('timeline.jsonl','events.jsonl'):
        if sha256_file(session/name)!=(partial['input_hashes'] if partial else manifest['hashes'])[name]:raise ValueError(f'Capture artifact changed: {name}')
    blocks_path=Path(driver['directory'])/'blocks.jsonl'
    blocks=read_lines(blocks_path,lambda row:{key:row[key] for key in
        ('sample_rate','capture_file_sample_start','capture_frames','generated_monotonic_s')})
    observations=read_lines(session/'timeline.jsonl',lambda row:{
        'sampled_monotonic_s':row['sampled_monotonic_s'],
        'state':{key:row['state'].get(key) for key in (('source','session','runtime','motion_frame') if settings.skeleton_overlay else ('source','session','runtime'))}})
    camera_frames=[]
    camera_manifest=(manifest.get('recovery',{}).get('camera') if partial else manifest.get('camera'))
    camera_folder=session/'camera'
    if partial and camera_manifest and camera_manifest.get('status')!='recovered':camera_manifest=None
    if camera_manifest:
        if camera_manifest['status'] not in ('complete','recovered'):raise ValueError('Camera capture is not complete')
        if partial:
            camera_folder=Path(camera_manifest['frame_root'])
            index=Path(camera_manifest['directory'])/'frames.jsonl'
        else:index=camera_folder/'frames.jsonl'
        if camera_folder.is_symlink() or index.parent.is_symlink() or index.is_symlink():raise ValueError('Camera prefix unavailable')
        if sha256_file(index)!=camera_manifest['index_sha256']:raise ValueError('Camera index changed')
        camera_frames=read_lines(index)
    # Audio count and per-block digital clock are the authoritative duration.
    import soundfile as sf
    info=sf.info(audio)
    if not blocks or info.frames!=sum(b['capture_frames'] for b in blocks) or info.samplerate!=blocks[0]['sample_rate']:
        raise ValueError('PCM and block manifest disagree')
    inputs={'audio.wav':sha256_file(audio),'blocks.jsonl':sha256_file(blocks_path),**(partial['input_hashes'] if partial else manifest['hashes'])}
    output=folder/'capture.mkv';temporary=folder/'capture.partial.mkv'
    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo',
             '-pix_fmt','bgr24','-s',f'{settings.width}x{settings.height}','-r',str(settings.fps),
             '-i','pipe:0','-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264',
             '-preset','veryfast','-threads','2','-pix_fmt','yuv420p','-c:a','pcm_f32le',str(temporary)]
    decoder=None;path=None;last_position=None;image=None;count=0;gaps={};sources={}
    report={'schema_version':1,'capture_id':manifest['id'],'settings':settings.model_dump(),
            'capture_completeness':'recovered_partial' if partial else 'complete',
            'partial_limits':partial['limits'] if partial else [],
            'recovery_provenance':({**partial['provenance'],
                'camera':({'directory':camera_manifest['directory'],'frame_root':str(camera_folder),
                           'index_sha256':camera_manifest['index_sha256'],
                           'verified_frames':camera_manifest.get('verified_frames'),
                           'stop_reason':camera_manifest.get('stop_reason'),
                           'source_hashes_declared':camera_manifest.get('source_hashes',{})}
                          if camera_manifest else None)} if partial else None),
            'alignment':'sampled source hold against generated digital audio callback clock',
            'limits':['Not a measurement of audiovisual or acoustic latency',
                      'Unrecorded/missing/stale camera intervals rendered black; processed preview only',
                      'Video may outlast PCM by less than one output frame',
                      'Original file identity is declared, not rehashed during export',
                      'No harmonic figure overlay; skeleton uses sampled observed joints only'],
            'skeleton_overlay':{'enabled':settings.skeleton_overlay,'frames':0,'omissions':{}},
            'input_hashes':inputs,'status':'rendering','frames':0,'gaps':gaps,'sources':sources}
    atomic_json(folder/'manifest.json',report)
    process=None
    try:
        with (folder/'encoder.log').open('wb') as log, (folder/'frames.jsonl').open('w') as timeline:
            process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
            for row in frame_plan(blocks,observations,**{k:getattr(settings,k) for k in ('fps','offset_s','max_gap_s','camera_clock')},camera_frames=camera_frames):
                if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
                source=row['source'];frame=None;source_size=None
                if source and source.get('kind')=='camera':
                    filename=source['file']
                    if Path(filename).name!=filename:raise ValueError('Invalid recorded camera frame name')
                    jpeg=camera_folder/filename
                    if jpeg.is_symlink() or sha256_file(jpeg)!=source['sha256']:raise ValueError('Recorded camera frame changed')
                    decoded=cv2.imread(str(jpeg))
                    if decoded is None:raise ValueError('Recorded camera frame is undecodable')
                    h,w=decoded.shape[:2];source_size=(w,h);scale=min(settings.width/w,settings.height/h)
                    resized=cv2.resize(decoded,(max(1,round(w*scale)),max(1,round(h*scale))))
                    frame=np.zeros((settings.height,settings.width,3),dtype=np.uint8)
                    rh,rw=resized.shape[:2];y=(settings.height-rh)//2;x=(settings.width-rw)//2
                    frame[y:y+rh,x:x+rw]=resized
                elif source:
                    if source['path']!=path:
                        if decoder is not None:decoder.release()
                        path=source['path'];decoder=cv2.VideoCapture(path);last_position=None;image=None
                        if not decoder.isOpened():raise ValueError('Source video is unavailable or undecodable')
                        sources[path]={'media_id':source['media_id'],'identity_verified':False}
                    if source['position_s']!=last_position:
                        decoder.set(cv2.CAP_PROP_POS_MSEC,source['position_s']*1000)
                        ok,image=decoder.read();last_position=source['position_s']
                        if not ok:raise ValueError('Could not decode requested source position')
                    h,w=image.shape[:2];source_size=(w,h);scale=min(settings.width/w,settings.height/h)
                    resized=cv2.resize(image,(max(1,round(w*scale)),max(1,round(h*scale))))
                    frame=np.zeros((settings.height,settings.width,3),dtype=np.uint8)
                    rh,rw=resized.shape[:2];y=(settings.height-rh)//2;x=(settings.width-rw)//2
                    frame[y:y+rh,x:x+rw]=resized
                else:
                    frame=np.zeros((settings.height,settings.width,3),dtype=np.uint8)
                    gaps[row['reason']]=gaps.get(row['reason'],0)+1
                if settings.skeleton_overlay:
                    from .capture_skeleton import draw_skeleton
                    observation=(observations[row['observation_index']] if 'observation_index' in row else None)
                    overlay=draw_skeleton(frame,row,observation,settings,source_size=source_size)
                    row['skeleton_overlay']=overlay
                    if overlay['status']=='drawn':report['skeleton_overlay']['frames']+=1
                    else:
                        omissions=report['skeleton_overlay']['omissions']
                        omissions[overlay['reason']]=omissions.get(overlay['reason'],0)+1
                process.stdin.write(frame.tobytes());timeline.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
                count+=1
                if progress:progress(count)
            process.stdin.close()
            if process.wait(timeout=30)!=0:raise ValueError('Encoder failed: '+(folder/'encoder.log').read_text()[-2000:])
        # Reject concurrent edits rather than certifying mixed generations.
        input_paths={'audio.wav':audio,'blocks.jsonl':blocks_path,
                     'timeline.jsonl':session/'timeline.jsonl','events.jsonl':session/'events.jsonl'}
        for name,path_to_check in input_paths.items():
            if path_to_check.is_symlink() or sha256_file(path_to_check)!=inputs[name]:
                raise ValueError(f'Capture input changed during export: {name}')
        if camera_manifest:
            if index.is_symlink() or sha256_file(index)!=camera_manifest['index_sha256']:
                raise ValueError('Camera index changed during export')
            for reference in camera_frames:
                jpeg=camera_folder/reference['file']
                if jpeg.is_symlink() or sha256_file(jpeg)!=reference['sha256']:
                    raise ValueError('Recorded camera frame changed during export')
        if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
        temporary.replace(output)
        report.update(status='complete',frames=count,camera_index_sha256=camera_manifest['index_sha256'] if camera_manifest else None,output={'file':output.name,'sha256':sha256_file(output)},
                      frame_plan_sha256=sha256_file(folder/'frames.jsonl'))
        if settings.browser_preview:
            try:report['preview']=browser_preview(folder,settings,cancelled)
            except (OSError,ValueError) as exc:
                if cancelled and cancelled.is_set():raise
                report['preview']={'status':'failed','error':str(exc)}
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
        self.jobs={}
        self.verified={}
        for capture in captures.list():
            root=Path(capture['directory'])/'exports'
            if not root.exists(): continue
            for folder in sorted(root.iterdir()):
                if folder.is_symlink() or not folder.is_dir(): continue
                try:
                    report=json.loads((folder/'manifest.json').read_text())
                    if report['status']=='rendering':
                        report.update(status='interrupted',error='Export process stopped before confirmed close')
                        atomic_json(folder/'manifest.json',report)
                    job={**report,'id':folder.name,'capture_id':capture['id'],'directory':str(folder)}
                    self.jobs[folder.name]=job
                except (OSError,ValueError,KeyError): continue

    def list(self):
        return [json.loads(json.dumps(dict(job))) for job in list(self.jobs.values())]

    def artifact(self, ident, name):
        job=self.jobs.get(ident)
        if job is None: raise ValueError('Unknown export')
        if name not in ('capture.mkv','preview.mp4','frames.jsonl','manifest.json'):raise ValueError('Unknown export artifact')
        folder=Path(job['directory'])
        if folder.is_symlink(): raise ValueError('Export directory is unavailable')
        folder=folder.resolve();path=folder/name
        if path.is_symlink() or not path.is_file():raise ValueError('Export artifact is unavailable')
        if name!='manifest.json':
            if job['status']!='complete':raise ValueError('Export is not complete')
            if name=='preview.mp4':
                if job.get('preview',{}).get('status')!='complete':raise ValueError('Browser preview is unavailable')
                expected=job['preview']['sha256']
            else:expected=job['output']['sha256'] if name=='capture.mkv' else job['frame_plan_sha256']
            stat=path.stat();fingerprint=(str(path),stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)
            if self.verified.get(fingerprint)!=expected:
                if sha256_file(path)!=expected:raise ValueError('Export artifact changed')
                self.verified[fingerprint]=expected
        return path

    def start(self,ident,settings):
        settings=ExportSettings.model_validate(settings)
        with self.lock:
            if self.thread and self.thread.is_alive():raise ValueError('Ya hay una exportación activa')
            jobs={j['id']:j for j in self.captures.list()}
            if ident not in jobs:raise ValueError('Elegí una captura conocida')
            if settings.recovered_prefix:
                from .capture_recovered_input import recovered_input
                recovered_input(jobs[ident])
            elif jobs[ident]['status']!='complete':raise ValueError('Elegí una captura completa')
            manifest=jobs[ident];export_id=uuid4().hex;folder=Path(manifest['directory'])/'exports'/export_id
            self.job={'id':export_id,'status':'rendering','capture_id':ident,'directory':str(folder),'frames':0}
            self.jobs[export_id]=self.job
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
