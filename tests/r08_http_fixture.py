"""Isolated real-library R08 browser fixture; synthetic video, no devices."""
import argparse,json,subprocess,os,sys
from pathlib import Path
from types import SimpleNamespace
import uvicorn
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.media import VideoLibrary
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--ui',type=Path,required=True)
parser.add_argument('--port',type=int,default=8879)
parser.add_argument('--slow-probe-first',action='store_true')
parser.add_argument('--slow-frame-first',action='store_true')
parser.add_argument('--historical-artifacts',action='store_true')
args=parser.parse_args();args.root.mkdir(parents=True,exist_ok=False)
video=args.root/'synthetic.mp4'
subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
library=VideoLibrary(args.root/'library')
library.index.write_text(json.dumps({'synthetic':{'id':'synthetic','name':'synthetic.mp4','path':str(video)}}))
library=VideoLibrary(args.root/'library')
runtime=SimpleNamespace(library=library,start=lambda:None,close=lambda:None)
pidfile=args.root/'decode.pid'
if args.slow_probe_first or args.slow_frame_first:
    import harmonic_weaver.lab.app as app_module
    from harmonic_weaver.lab.research.rope_reader import RopeReader
    from harmonic_weaver.lab.research.rope_process import capture
    class SlowFirstReader(RopeReader):
        probe_first=True
        frame_first=True
        def slow(self,cancel):
            capture([sys.executable,'-c',f'from pathlib import Path;import os,time;Path({str(pidfile)!r}).write_text(str(os.getpid()));time.sleep(30)'],max_bytes=1024,cancel=cancel)
        def probe(self,path,*,cancel=None):
            if args.slow_probe_first and self.probe_first:
                self.probe_first=False
                self.slow(cancel)
            return super().probe(path,cancel=cancel)
        def frame(self,path,index,expected_sha256,*,cancel=None):
            if args.slow_frame_first and self.frame_first:
                self.frame_first=False
                self.slow(cancel)
            return super().frame(path,index,expected_sha256,cancel=cancel)
    app_module.RopeReader=SlowFirstReader
app=create_app(args.root,runtime=runtime,ui_dir=args.ui)
if args.historical_artifacts:
    import numpy as np
    from harmonic_weaver.lab.research.rope_media import probe
    from harmonic_weaver.lab.research.rope_compare_service import RopeCompareService
    from harmonic_weaver.lab.research.rope_path_service import RopePathService
    from harmonic_weaver.lab.research.rope_mask import propose
    media=probe(video)
    annotation={'media_sha256':media['media_sha256'],'width_px':160,'height_px':120,
                'frames':[{'frame_index':0,'time_s':0,'state':'observed',
                           'visible_segments':[[{'x':0,'y':0},{'x':1,'y':1}]]}]}
    comparison=RopeCompareService(args.root)
    comparison_job=comparison.start({'reference':annotation,'candidate':annotation})
    paths=RopePathService(args.root)
    mask={**propose(np.full((120,160,3),255,dtype=np.uint8),
                   {'distance_rgb':0,'min_component_px':1}),
          'media_sha256':media['media_sha256'],'frame_index':0,'time_s':0}
    path_job=paths.start({'mask':mask,'mask_manifest_sha256':'b'*64,
                          'settings':{'component_id':1,'start':{'x':0,'y':0},'stop':{'x':1,'y':1}}})
    # Fixture simulates a recorded older environment; production has no mutation route.
    for service,job in ((comparison,comparison_job),(paths,path_job)):
        manifest_path=service.folder(job['id'])/'manifest.json'
        manifest=json.loads(manifest_path.read_text())
        manifest['environment']['python']='older-fixture'
        manifest_path.write_text(json.dumps(manifest))
@app.get('/test/decode-live')
def decode_live():
    try:os.kill(int(pidfile.read_text()),0);return {'live':True}
    except (OSError,ValueError):return {'live':False}
# Insert the fixture-only probe before the production catch-all static mount.
app.router.routes.insert(0,app.router.routes.pop())
uvicorn.run(app,host='127.0.0.1',port=args.port)
