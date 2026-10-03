"""Full production UI/runtime fixture. Controls only: no audio device or camera opened."""
import argparse
from dataclasses import asdict
from pathlib import Path
import threading
import uvicorn
from fastapi.staticfiles import StaticFiles
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.contracts import PerceptionSettings
from harmonic_weaver.lab.presets import initial_presets,seed_presets
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.runtime import LaboratoryRuntime
from harmonic_weaver.lab.store import SessionStore


class ControlRecorder:
    def __init__(self):
        self.lock=threading.RLock();self.targets=[];self.revision=-1
    def start(self):pass
    def close(self):pass
    def submit(self,targets,revision):
        with self.lock:self.targets=[asdict(t) for t in targets];self.revision=revision
    def snapshot(self):
        return {'shaper':{'applied_revision':-1,'error':'Fixture: control targets only; no audio device',
            'telemetry_valid':False},'voice_frame':None}
    def controls(self):
        with self.lock:return {'mode':'control_targets_only','revision':self.revision,'targets':self.targets}


parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--ui',type=Path,required=True)
parser.add_argument('--checkpoint',type=Path,required=True)
parser.add_argument('--port',type=int,default=8879)
parser.add_argument('--seed-r07-labels',action='store_true',help='Create synthetic EVAL/PCM/figures before services restore their inventory')
args=parser.parse_args()
if not (args.ui/'index.html').is_file() or not args.checkpoint.is_file():
    parser.error('Built production UI and existing checkpoint required')
args.root.mkdir(parents=True,exist_ok=False)
if args.seed_r07_labels:
    from membrane_labels_fixture import seed
    seed(args.root)
store=SessionStore(args.root,prepare=PreparedRoutes);seed_presets(store)
reference=next(p for p in initial_presets() if p.id=='lab-v2-reference-sustained')
store.edit(reference,store.state.desired_revision)
audio=ControlRecorder();runtime=LaboratoryRuntime(store,audio=audio)
app=create_app(args.root,store=store,runtime=runtime,
    perception=PerceptionSettings(checkpoint=str(args.checkpoint.resolve()),device='cpu'))
@app.get('/api/fixture/controls')
def controls():return audio.controls()
app.mount('/',StaticFiles(directory=args.ui,html=True),name='laboratory-ui')
try:uvicorn.run(app,host='127.0.0.1',port=args.port)
finally:store.close()
