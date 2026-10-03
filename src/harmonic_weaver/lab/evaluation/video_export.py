"""Optional local video+PCM+all-oscillator figure export of a verified comparison."""
import json,math,subprocess,threading,time
from pathlib import Path
from typing import Literal
from pydantic import Field
from ..contracts import Contract,VisualSettings
from ..cache import atomic_json,sha256_file
from .figure_render import RasterFigure,voices_at


class Settings(Contract):
    schema_version:Literal[1]=1
    fps:int=Field(default=30,ge=1,le=60)
    width:int=Field(default=1280,ge=128,le=1920,multiple_of=4)
    height:int=Field(default=720,ge=64,le=1080,multiple_of=2)
    format:Literal['mkv','mp4']='mkv'
    video_crf:int=Field(default=18,ge=0,le=40)
    audio_kbps:int=Field(default=192,ge=64,le=320)
    visual:VisualSettings|None=None


def render(evaluation,ident,run_index,settings,folder,*,cancelled=None,progress=None):
    import soundfile as sf
    import cv2
    import numpy as np
    settings=Settings.model_validate(settings);folder=Path(folder)
    report=evaluation.report(ident)
    if type(run_index) is not int or not 0<=run_index<len(report['manifest']['runs']):raise ValueError('Run outside comparison')
    run=report['manifest']['runs'][run_index]
    if not run.get('pcm'):raise ValueError('Render PCM first to export video and figure')
    source=report['manifest']['request']['sources'][run['source_index']]
    preset=report['manifest']['request']['presets'][run['preset_index']]
    paths={'request':evaluation.artifact(ident,'request.json'),
           'manifest':evaluation.artifact(ident,'manifest.json'),
           'video':evaluation.source_file(ident,run['source_index']),
           'audio':evaluation.artifact(ident,run['pcm']['file']),
           'oscillators':evaluation.artifact(ident,run['pcm']['voice_frames'])}
    inputs={name:sha256_file(path) for name,path in paths.items()}
    if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
    info=sf.info(paths['audio']);duration=info.frames/info.samplerate
    if not 0<duration<=120:raise ValueError('Choose a PCM segment of at most 120 seconds')
    if info.frames!=run['pcm']['samples'] or info.samplerate!=run['pcm']['settings']['sample_rate']:raise ValueError('PCM metadata mismatch')
    if paths['oscillators'].stat().st_size>128*1024*1024:raise ValueError('Oscillator inventory exceeds 128 MiB; choose a shorter comparison')
    blocks=[]
    with paths['oscillators'].open() as handle:
        for line in handle:
            if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
            block=json.loads(line)
            if block['sample_rate']!=info.samplerate or len(block['voices'])>32:raise ValueError('Invalid oscillator frame')
            if blocks and block['audio_file_sample_start']<=blocks[-1]['audio_file_sample_start']:raise ValueError('Oscillator order changed')
            blocks.append(block)
    if not blocks:raise ValueError('Missing oscillator state')
    visual=settings.visual or VisualSettings.model_validate(preset['visual'])
    folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    output=folder/f'comparison.{settings.format}';partial=folder/f'comparison.partial.{settings.format}'
    start=run['pcm']['segment_source_start_s'];visual_duration=max(0.,source['end_s']-start)
    count=math.ceil(info.frames*settings.fps/info.samplerate)
    graph=(f'[0:v]trim=duration={visual_duration:.12f},setpts=PTS-STARTPTS,'
           f'{"hflip," if visual.mirror_video else ""}'
           f'scale={settings.width//2}:{settings.height}:force_original_aspect_ratio=decrease,'
           f'pad={settings.width//2}:{settings.height}:(ow-iw)/2:(oh-ih)/2:color=black,'
           f'tpad=stop_mode=clone:stop_duration={duration:.12f},fps={settings.fps},setsar=1[left];'
           '[left][2:v]hstack=inputs=2:shortest=0[out]')
    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-threads','2',
        '-ss',f'{start:.12f}','-i',str(paths['video']),'-i',str(paths['audio']),
        '-f','rawvideo','-pix_fmt','bgr24','-s',f'{settings.width//2}x{settings.height}',
        '-framerate',str(settings.fps),'-i','pipe:0','-filter_complex_threads','1',
        '-filter_complex',graph,'-map','[out]','-map','1:a:0','-c:v','libx264',
        '-preset','veryfast','-crf',str(settings.video_crf),'-threads','2','-pix_fmt','yuv420p',
        '-c:a','copy' if settings.format=='mkv' else 'aac']
    if settings.format=='mp4':command+=['-b:a',f'{settings.audio_kbps}k','-movflags','+faststart']
    command+=['-t',f'{duration:.12f}',str(partial)]
    version=subprocess.run(['ffmpeg','-version'],capture_output=True,text=True,timeout=10).stdout.splitlines()[0]
    manifest={'schema_version':1,'status':'rendering','evaluation_id':ident,'run_index':run_index,
        'settings':settings.model_dump(),'visual_effective':visual.model_dump(exclude={'show_skeleton','on_disconnect'}),'input_hashes':inputs,
        'code_hashes':{p.name:sha256_file(p) for p in (Path(__file__),Path(__file__).with_name('figure_render.py'))},
        'environment':{'numpy':np.__version__,'opencv':cv2.__version__,'soundfile':sf.__version__},
        'ffmpeg_version':version,'duration_s':duration,'sample_rate':info.samplerate,'samples':info.frames,
        'frames':0,'planned_frames':count,'clock':'PCM file sample zero, figure frame n at n/fps',
        'source_start_s':start,'source_visual_duration_s':visual_duration,
        'audio':'original PCM packets copied' if settings.format=='mkv' else 'lossy AAC derived from original PCM',
        'figure_stage':'oscillators_pre_shape_limiter',
        'limits':['Logical export clock, not measured physical audiovisual synchronization',
          'All oscillator phasors; no two-channel reduction or measured physical cymatics',
          'Raster/display styling differs from WebGL; persistence depends on output fps',
          'Original video is resized/reencoded; output video duration quantized to frames',
          'Video holds last selected frame during instrument tail; original video audio excluded',
          'MP4 AAC may introduce padding/loss; original WAV remains authoritative',
          'Skeleton and disconnect styling are not rendered in this export',
          'Private local body footage/output; no automatic upload']}
    atomic_json(folder/'manifest.json',manifest)
    process=None;stop=threading.Event();guard=None
    try:
        with (folder/'encoder.log').open('wb') as log,(folder/'frames.jsonl').open('w') as timeline:
            process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
            deadline=time.monotonic()+600
            def watchdog():
                while not stop.wait(.05):
                    if (cancelled and cancelled.is_set()) or time.monotonic()>deadline:
                        if process.poll() is None:process.kill()
                        return
            guard=threading.Thread(target=watchdog,daemon=True);guard.start()
            figure=RasterFigure(settings.width//2,settings.height)
            for index in range(count):
                if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
                seconds=index/settings.fps;voices=voices_at(blocks,seconds)
                process.stdin.write(figure.draw(voices,visual,preset['fundamental_hz']).tobytes())
                timeline.write(json.dumps({'frame':index,'audio_time_s':seconds,'audio_sample':seconds*info.samplerate,
                    'source_time_s':min(source['end_s'],start+seconds),'voice_count':len(voices)},sort_keys=True)+'\n')
                manifest['frames']=index+1
                if progress:progress(index+1,count)
            process.stdin.close()
            if process.wait(timeout=30)!=0:raise ValueError('Encoder failed; inspect local encoder.log')
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames',
            '-show_streams','-of','json',str(partial)],timeout=60))
        video_streams=[stream for stream in probe['streams'] if stream['codec_type']=='video']
        audio_streams=[stream for stream in probe['streams'] if stream['codec_type']=='audio']
        if len(video_streams)!=1 or len(audio_streams)!=1:raise ValueError('Output stream inventory mismatch')
        video_stream=video_streams[0];audio_stream=audio_streams[0]
        if (video_stream['width']!=settings.width or video_stream['height']!=settings.height
            or int(video_stream.get('nb_read_frames',0))!=count):raise ValueError('Output video frame inventory mismatch')
        if int(audio_stream['sample_rate'])!=info.samplerate or audio_stream['channels']!=info.channels:
            raise ValueError('Output audio format mismatch')
        manifest['output_streams']={'video':{key:video_stream.get(key) for key in
            ('codec_name','width','height','nb_read_frames','avg_frame_rate')},
            'audio':{key:audio_stream.get(key) for key in ('codec_name','sample_rate','channels')}}
        for name,path in paths.items():
            if path.is_symlink() or sha256_file(path)!=inputs[name]:raise ValueError(f'Export input changed: {name}')
        if cancelled and cancelled.is_set():raise ValueError('Export cancelled')
        partial.replace(output)
        manifest.update(status='complete',output={'file':output.name,'sha256':sha256_file(output)},
            timeline_sha256=sha256_file(folder/'frames.jsonl'))
        atomic_json(folder/'manifest.json',manifest);return manifest
    except Exception as exc:
        manifest.update(status='cancelled' if cancelled and cancelled.is_set() else 'failed',error=str(exc))
        atomic_json(folder/'manifest.json',manifest);raise
    finally:
        stop.set()
        if process is not None:
            if process.poll() is None:process.kill()
            process.wait()
            if process.stdin and not process.stdin.closed:
                try:process.stdin.close()
                except OSError:pass
        if guard:guard.join(timeout=1)
