"""Explicit synthetic-only network harness, never starts audio/perception devices.
Run from repo: PYTHONPATH=src:tests python tests/r03_http_fixture.py --root ... --ui ...
"""
import argparse
from pathlib import Path
from uuid import uuid4
import uvicorn
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.evaluation.runner import Request,run
from harmonic_weaver.lab.evaluation.service import EvaluationService
from harmonic_weaver.lab.presets import initial_presets
from harmonic_weaver.lab.research.candidate_input import candidate_snapshot
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.store import SessionStore
from test_lab_evaluation import source_fixture


class Runtime:
    library=None
    def start(self):pass
    def close(self):pass


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--ui',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8879)
    parser.add_argument('--synthetic-video',type=Path,help='Optional generated MP4; not participant media')
    args=parser.parse_args()
    args.root.mkdir(parents=True,exist_ok=False)
    source,_,_=source_fixture(args.root,media_bytes=args.synthetic_video.read_bytes() if args.synthetic_video else None)
    root=args.root/'session';ident=uuid4().hex;folder=root/'evaluations'/ident
    folder.mkdir(parents=True)
    preset=next(p for p in initial_presets() if p.algorithm.id=='local')
    request=Request(presets=[preset],sources=[source]);atomic_json(folder/'request.json',request.model_dump())
    run(request,folder/'result')
    store=SessionStore(root,prepare=PreparedRoutes);evaluation=EvaluationService(root,store,None)
    try:
        features=candidate_snapshot(evaluation,dict(evaluation_id=ident,run_index=0,signal_id='zone.1.speed',start_s=.2,end_s=2,high=.1,low=.02))
        record=features['provenance']['source_record'];cache=record['cache_manifest']
        identity=dict(kind='video',cache_manifest_sha256=record['cache_manifest_sha256'],
                      generation=cache['generation'],cache_key=cache['key'],media_id=cache['media_sha256'])
        store.state.source_id='synthetic-live';store.state.person_id='one';store.state.position_s=.5
        store.mark('Synthetic fixture; not human evidence',category='deployment',observed_epoch=2,transport_epoch=2,source_identity=identity)
        uvicorn.run(create_app(root,store=store,runtime=Runtime(),ui_dir=args.ui),host='127.0.0.1',port=args.port)
    finally:evaluation.close();store.close()


if __name__=='__main__':main()
