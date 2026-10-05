"""Bounded local reproduction using the unchanged production perception worker.

No pose/video output and no cache writes. Run each condition in a fresh process.
"""
from __future__ import annotations
import argparse
from contextlib import redirect_stdout
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace


def save(path, data):
    path=Path(path)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,allow_nan=False,indent=2))
    temp.replace(path)


def child(request, report_path):
    report={'status':'running','stage':'imports','completed_frames':0,'frame_sequence':None,
            'source_time_s':None,'request':request,'pid':os.getpid(),
            'diagnostic_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    started=time.monotonic()
    def mark(stage):
        report['stage']=stage
        save(report_path,report)
    save(report_path,report)
    try:
        sys.path.insert(0,str(Path(request['harmocap_dir'])/'src'))
        import torch
        report['environment']={'torch':torch.__version__,'cuda_runtime':torch.version.cuda,
                               'cuda_launch_blocking':os.environ.get('CUDA_LAUNCH_BLOCKING'),
                               'cuda_available':torch.cuda.is_available()}
        if request['settings']['device'].startswith('cuda'):
            if not torch.cuda.is_available():raise RuntimeError('CUDA requested but unavailable; no CPU fallback')
            report['environment']['gpu']=torch.cuda.get_device_name(request['settings']['device'])
        module_path=Path(__file__).with_name('perception_worker.py')
        spec=importlib.util.spec_from_file_location('diagnostic_perception_worker',module_path)
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        mark('provenance')
        report['extractor']=worker.probe(request['harmocap_dir'])
        if 'checkpoint' in request['settings']:
            report['checkpoint_sha256']=worker.file_hash(request['settings']['checkpoint'])
        from harmocap import perception,identity
        native_backend=perception.PoseBackend
        native_update=identity.SlotManager.update
        native_frames=worker.file_frames
        class Backend:
            def __init__(self,**kwargs):
                mark('backend_initialization')
                self.backend=native_backend(**kwargs)
            def track_frame(self,image):
                mark('inference')
                return self.backend.track_frame(image)
        def update(manager,*args,**kwargs):
            mark('identity_association')
            result=native_update(manager,*args,**kwargs)
            mark('frame_projection')
            return result
        def frames(path):
            iterator=native_frames(path)
            try:
                for _ in range(request['frames']):
                    mark('decode')
                    try:image,timing=next(iterator)
                    except StopIteration:break
                    report['frame_sequence']=timing['sequence']
                    report['source_time_s']=timing['source_time_s']
                    yield image,timing
            finally:
                iterator.close()
        def emit(message):
            if message['type']=='frame':
                report['completed_frames']+=1
            elif message['type']=='complete':report['worker_completed']=True
        perception.PoseBackend=Backend;identity.SlotManager.update=update;worker.file_frames=frames
        try:
            worker.run(SimpleNamespace(config_json=json.dumps(request['settings']),
                video=request['video'],camera=0,source_id='diagnostic',stream_id='diagnostic'),emit)
        finally:
            perception.PoseBackend=native_backend;identity.SlotManager.update=native_update
        if not report.get('worker_completed'):
            raise RuntimeError('Worker returned without completion')
        report['status']='complete';report['stage']='complete'
    except Exception as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
    finally:
        report['elapsed_s']=time.monotonic()-started
        save(report_path,report)
    return 0 if report['status']=='complete' else 1


def launch(request, output, python, timeout):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    request_path=output/'request.json';report_path=output/'report.json'
    save(request_path,request)
    command=[str(python),str(Path(__file__).resolve()),'--child-request',str(request_path.resolve()),
             '--report',str(report_path.resolve())]
    env=dict(os.environ,PYTHONUNBUFFERED='1',CUDA_LAUNCH_BLOCKING='1' if request['cuda_synchronous'] else '0')
    with (output/'worker.log').open('w') as log:
        try:
            result=subprocess.run(command,stdout=log,stderr=log,env=env,timeout=timeout,
                                  cwd=request['harmocap_dir'])
            returncode=result.returncode
        except subprocess.TimeoutExpired:
            returncode=None
    report=json.loads(report_path.read_text()) if report_path.exists() else {'status':'failed','stage':'startup'}
    report['process_returncode']=returncode
    if returncode != 0 or report.get('status')!='complete':
        report.update(status='failed',process_returncode=returncode)
        if returncode is None:report['process_error']='Diagnostic timeout; child process stopped'
        elif not report.get('error'):report['process_error']='Child exited without a complete diagnostic'
    save(report_path,report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video');parser.add_argument('--checkpoint');parser.add_argument('--settings-json')
    parser.add_argument('--device',choices=['cpu','cuda:0'],default='cuda:0')
    parser.add_argument('--frames',type=int,default=240);parser.add_argument('--imgsz',type=int,default=320)
    parser.add_argument('--cuda-synchronous',action='store_true')
    parser.add_argument('--harmocap-dir',default=str(Path.home()/'Projects/HarMoCAP'))
    parser.add_argument('--python');parser.add_argument('--output');parser.add_argument('--timeout',type=float,default=180)
    parser.add_argument('--child-request',help=argparse.SUPPRESS);parser.add_argument('--report',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.child_request:
        with redirect_stdout(sys.stderr):return child(json.loads(Path(args.child_request).read_text()),args.report)
    if not args.video or not args.output or not (args.checkpoint or args.settings_json):
        parser.error('--video, --output and --checkpoint or --settings-json required')
    if not 1<=args.frames<=100000 or args.timeout<=0:parser.error('Positive bounded frames and timeout required')
    from harmonic_weaver.lab.contracts import PerceptionSettings
    settings=json.loads(Path(args.settings_json).read_text()) if args.settings_json else {'checkpoint':args.checkpoint,'imgsz':args.imgsz}
    settings['device']=args.device
    settings=PerceptionSettings.model_validate(settings).model_dump()
    for key in ('checkpoint',):settings[key]=str(Path(settings[key]).resolve(strict=True))
    video=Path(args.video).resolve(strict=True)
    stat=video.stat()
    request={'video':str(video), 'video_stat':{'size':stat.st_size,'mtime_ns':stat.st_mtime_ns}, 'settings':settings,
             'frames':args.frames,'cuda_synchronous':args.cuda_synchronous,
             'harmocap_dir':str(Path(args.harmocap_dir).resolve(strict=True))}
    python=args.python or str(Path(request['harmocap_dir'])/'.venv/bin/python')
    report=launch(request,args.output,python,args.timeout)
    print(json.dumps({k:report.get(k) for k in ('status','stage','completed_frames','process_returncode')}))
    return 0 if report['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
