"""Full production UI/runtime fixture. Controls only: no audio device or camera opened."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
import threading
import uvicorn
from fastapi.staticfiles import StaticFiles
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.cache import TrackingCache,sha256_file
from harmonic_weaver.lab.media import VideoLibrary,VideoJob
from harmonic_weaver.lab.evaluation.runner import Source
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
parser.add_argument('--frozen-evaluation-request',type=Path,help='Local EVAL request JSON with an explicitly selected body; no media/pose recomputation')
parser.add_argument('--source-index',type=int,default=0)
parser.add_argument('--frozen-cache-root',type=Path,help='Explicit existing tracking cache root; originals remain there')
args=parser.parse_args()
if bool(args.frozen_evaluation_request)!=bool(args.frozen_cache_root):
    parser.error('Frozen evaluation request and cache root must be provided together')
if args.source_index<0:parser.error('Source index must be nonnegative')
if not (args.ui/'index.html').is_file() or not args.checkpoint.is_file():
    parser.error('Built production UI and existing checkpoint required')
args.root.mkdir(parents=True,exist_ok=False)
if args.seed_r07_labels:
    from membrane_labels_fixture import seed
    seed(args.root)
store=SessionStore(args.root,prepare=PreparedRoutes);seed_presets(store)
reference=next(p for p in initial_presets() if p.id=='lab-v2-reference-sustained')
store.edit(reference,store.state.desired_revision)
audio=ControlRecorder();library=None;source=None;job=None
if args.frozen_evaluation_request:
    document=json.loads(args.frozen_evaluation_request.read_text())
    if args.source_index>=len(document['sources']):parser.error('Source index unavailable')
    source=Source.model_validate(document['sources'][args.source_index])
    manifest_path=Path(source.cache_manifest)
    if sha256_file(manifest_path)!=source.cache_manifest_sha256:
        raise ValueError('Frozen cache manifest changed')
    manifest=json.loads(manifest_path.read_text())
    track=TrackingCache(args.frozen_cache_root).read(source.media_path,manifest['key'])
    if track is None or not track.frames:raise ValueError('Verified frozen tracking unavailable')
    ids=sorted({person.person_id for frame in track.frames for person in frame.persons})
    if source.person_id not in ids:raise ValueError('Declared frozen person absent from tracking')
    library=VideoLibrary(args.root)
    job=VideoJob('frozen-cache-fixture',Path(source.media_path),
        PerceptionSettings(checkpoint=str(args.checkpoint.resolve()),**manifest['perception']),
        status='ready',requested_device=manifest['perception']['device'],
        media_id=track.frames[0].source_id,cache_key=manifest['key'],
        cache_location=str(manifest_path),generation=manifest['generation'],
        person_ids=ids,cache_hit=True,duration_s=manifest['duration_s'],
        frames=track.frames,times=[frame.source_time_s for frame in track.frames])
    library.jobs[job.id]=job
runtime=LaboratoryRuntime(store,library=library,audio=audio)
if source is not None:
    # Selection belongs to the supplied frozen source, not an inferred person.
    # Deliberately do not transplant its calibration into a new session.
    runtime.kind='video';runtime.job_id=job.id;runtime.person_id=source.person_id
    runtime._selection_explicit=True;runtime.selection_status='explicit'
    runtime._autoplay_pending=False;runtime.transport.seek(source.start_s)
app=create_app(args.root,store=store,runtime=runtime,
    perception=PerceptionSettings(checkpoint=str(args.checkpoint.resolve()),device='cpu'))
@app.get('/api/fixture/controls')
def controls():return audio.controls()
app.mount('/',StaticFiles(directory=args.ui,html=True),name='laboratory-ui')
try:uvicorn.run(app,host='127.0.0.1',port=args.port)
finally:store.close()
