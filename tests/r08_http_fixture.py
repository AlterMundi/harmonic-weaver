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
@app.get('/test/decode-live')
def decode_live():
    try:os.kill(int(pidfile.read_text()),0);return {'live':True}
    except (OSError,ValueError):return {'live':False}
# Insert the fixture-only probe before the production catch-all static mount.
app.router.routes.insert(0,app.router.routes.pop())
uvicorn.run(app,host='127.0.0.1',port=args.port)

