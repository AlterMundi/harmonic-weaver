"""Isolated real-library R08 browser fixture; synthetic video, no devices."""
import argparse,json,subprocess
from pathlib import Path
from types import SimpleNamespace
import uvicorn
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.media import VideoLibrary
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--ui',type=Path,required=True)
parser.add_argument('--port',type=int,default=8879)
args=parser.parse_args();args.root.mkdir(parents=True,exist_ok=False)
video=args.root/'synthetic.mp4'
subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
library=VideoLibrary(args.root/'library')
library.index.write_text(json.dumps({'synthetic':{'id':'synthetic','name':'synthetic.mp4','path':str(video)}}))
library=VideoLibrary(args.root/'library')
runtime=SimpleNamespace(library=library,start=lambda:None,close=lambda:None)
uvicorn.run(create_app(args.root,runtime=runtime,ui_dir=args.ui),host='127.0.0.1',port=args.port)
