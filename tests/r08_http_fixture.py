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
parser.add_argument('--slow-flow-first',action='store_true')
parser.add_argument('--spatial-generation',action='store_true')
parser.add_argument('--experience-stimulus',action='store_true')
args=parser.parse_args();args.root.mkdir(parents=True,exist_ok=False)
video=args.root/'synthetic.mp4'
subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',f'testsrc2=size=160x120:rate=10:duration={3 if args.experience_stimulus else .5}','-c:v','libx264',str(video)],check=True)
library=VideoLibrary(args.root/'library')
library.index.write_text(json.dumps({'synthetic':{'id':'synthetic','name':'synthetic.mp4','path':str(video)}}))
library=VideoLibrary(args.root/'library')
if args.spatial_generation:
    from harmonic_weaver.lab.media import VideoJob
    from harmonic_weaver.lab.contracts import MotionFrame,PerceptionSettings
    frames=[MotionFrame.model_validate({'source_id':'synthetic','stream_id':'synthetic-spatial','sequence':i,
        'source_time_s':i*.1,'available_monotonic_s':1.+i,'timestamp_origin':'synthetic','width':160,'height':120,
        'persons':[{'person_id':'slot-1-generation-1','joints':[{'index':0,'position':[.5,.2],
            'confidence':.9,'state':'observed'}]}] if i==0 else []}) for i in (0,2)]
    library.jobs['synthetic-spatial']=VideoJob('synthetic-spatial',video,PerceptionSettings(checkpoint='fixture-only.pt'),
        status='ready',media_id='synthetic',cache_key='a'*64,generation='fixture-generation',
        person_ids=['slot-1-generation-1'],frames=frames,times=[0.,.2],duration_s=.5)
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
if args.slow_flow_first:
    import harmonic_weaver.lab.research.rope_flow_service as flow_module
    from harmonic_weaver.lab.research.rope_process import capture
    original_flow_run=flow_module.run
    flow_first=True
    def slow_flow(request,path,folder,reader,*,cancel=None):
        global flow_first
        if flow_first:
            flow_first=False
            capture([sys.executable,'-c',f'from pathlib import Path;import os,time;Path({str(pidfile)!r}).write_text(str(os.getpid()));time.sleep(30)'],max_bytes=1024,cancel=cancel)
        return original_flow_run(request,path,folder,reader,cancel=cancel)
    flow_module.run=slow_flow
if args.experience_stimulus:
    from test_lab_evaluation import source_fixture
    from harmonic_weaver.lab.evaluation.runner import Request as EvaluationRequest,run as evaluate
    from harmonic_weaver.lab.evaluation.service import EvaluationService
    from harmonic_weaver.lab.store import SessionStore
    from harmonic_weaver.lab.routing import PreparedRoutes
    from harmonic_weaver.lab.presets import initial_presets
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.research.candidate_input import candidate_snapshot
    from harmonic_weaver.lab.research.resonator_run import run as render
    pose_root=args.root/'synthetic-pose';pose_root.mkdir()
    source,_,_=source_fixture(pose_root,media_bytes=video.read_bytes())
    ident='a'*32;folder=args.root/'evaluations'/ident;folder.mkdir(parents=True)
    request=EvaluationRequest(presets=[next(p for p in initial_presets() if p.algorithm.id=='local')],sources=[source])
    atomic_json(folder/'request.json',request.model_dump());evaluate(request,folder/'result')
    store=SessionStore(args.root/'fixture-store',prepare=PreparedRoutes)
    evaluation=EvaluationService(args.root,store,library)
    try:
        document=candidate_snapshot(evaluation,{'evaluation_id':ident,'run_index':0,'signal_id':'zone.1.speed',
            'start_s':.3,'end_s':1.5,'high':.1,'low':.02})
        render(document,{'resonators':{'sample_rate':8000},'render':{'tail_s':.1}},args.root/'research/r05'/('b'*32))
    finally:evaluation.close();store.close()
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
