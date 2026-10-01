"""Isolated R07 UI server with synthetic PCM only; no audio device."""
import argparse
from pathlib import Path
import uvicorn
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.research.resonator_run import run

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--ui',type=Path,required=True)
parser.add_argument('--port',type=int,default=8879)
args=parser.parse_args()
args.root.mkdir(parents=True,exist_ok=False)
document={'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),
          'unit':'T/s','rows':[{'time_s':0.,'value':0.,'valid':True}, {'time_s':.03,'value':2.,'valid':True}],
          'provenance':{'fixture':'synthetic'}}
run(document,{'resonators':{'sample_rate':8000}},args.root/'research/r05'/('a'*32))
uvicorn.run(create_app(args.root,ui_dir=args.ui),host='127.0.0.1',port=args.port)
