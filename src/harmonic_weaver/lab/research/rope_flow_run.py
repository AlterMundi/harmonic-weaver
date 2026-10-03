"""Bounded reproducible flow candidates on exact decoded source frames."""
import argparse
import json
import platform
import re
from pathlib import Path
import cv2
import numpy as np
from pydantic import Field,model_validator,model_serializer
from typing import Literal
from ..contracts import Contract,Number
from ..cache import atomic_json,sha256_file
from .rope_annotations import Point
from .rope_flow import RopeFlow,Settings
from .rope_reader import RopeReader
from .rope_process import DecodeCancelled
from .rope_flow_contract import validate_frames
from .rope_sequence import sequence


class Request(Contract):
    media_sha256:str=Field(pattern='^[a-f0-9]{64}$')
    width_px:int=Field(ge=2,le=32768)
    height_px:int=Field(ge=2,le=32768)
    start_frame_index:int=Field(ge=0)
    frame_times_s:list[Number]=Field(min_length=2,max_length=120)
    seeds:list[Point]=Field(min_length=1,max_length=4096)
    settings:Settings=Field(default_factory=Settings)
    decoder:Literal['individual_png','sequential_png']='individual_png'

    @model_serializer(mode='wrap')
    def serialize(self,handler):
        data=handler(self)
        if self.decoder=='individual_png':data.pop('decoder',None)
        return data

    @model_validator(mode='after')
    def valid(self):
        if self.width_px*self.height_px>4_000_000:raise ValueError('Flow image budget exceeded')
        if self.frame_times_s[0]<0 or any(b<=a for a,b in zip(self.frame_times_s,self.frame_times_s[1:])):raise ValueError('Strict source clock required')
        if len(self.seeds)>self.settings.max_points:raise ValueError('Seed budget exceeded')
        return self


def environment():
    return {'python':platform.python_version(),'numpy':np.__version__,'opencv':cv2.__version__}


def code():
    return {name:sha256_file(Path(__file__).parent/name) for name in
            ('rope_flow.py','rope_flow_contract.py','rope_flow_run.py','rope_sequence.py','rope_annotations.py','rope_reader.py','rope_media.py','rope_process.py','../contracts.py')}


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():raise DecodeCancelled('Flow calculation cancelled')


def calculate(request,path,reader=None,*,cancel=None):
    request=Request.model_validate(request);reader=reader or RopeReader()
    check_cancel(cancel);media=reader.probe(path,cancel=cancel)
    if (media['media_sha256'],media['width_px'],media['height_px'])!=(request.media_sha256,request.width_px,request.height_px):raise ValueError('Flow source identity/dimensions mismatch')
    times=media['frame_times_s'][request.start_frame_index:request.start_frame_index+len(request.frame_times_s)]
    if times!=request.frame_times_s:raise ValueError('Flow source clock mismatch; use exact probe timestamps')
    flow=RopeFlow(request.settings.model_dump());frames=[]
    pngs=sequence(path,request.start_frame_index,len(times),request.media_sha256,media,cancel=cancel) if request.decoder=='sequential_png' else (
        reader.frame(path,request.start_frame_index+offset,request.media_sha256,cancel=cancel) for offset in range(len(times)))
    try:
        for offset,png in enumerate(pngs):
            check_cancel(cancel);index=request.start_frame_index+offset;time_s=request.frame_times_s[offset]
            gray=cv2.imdecode(np.frombuffer(png,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
            if gray is None or gray.shape!=(request.height_px,request.width_px):raise ValueError('Flow decoded dimensions mismatch')
            check_cancel(cancel)
            frames.append(flow.feed(gray,index,time_s,seeds=[p.model_dump() for p in request.seeds] if offset==0 else None))
    finally:pngs.close()
    if reader.probe(path,cancel=cancel)['media_sha256']!=request.media_sha256:raise ValueError('Flow source changed during calculation')
    return {'schema_version':1,'line':'R08','request':request.model_dump(),'frames':frames,
            'limits':frames[0]['limits']+['Exact decoded frame indices and source timestamps; no video/image copies persisted',
                      'Only initial seeds are supplied; lost support requires a separate explicitly seeded run',
                      'An optical correspondence candidate is not a manually accepted annotation or scientific rope benchmark']}


def run(request,path,folder,reader=None,*,cancel=None):
    request=Request.model_validate(request);reader=reader or RopeReader()
    result=calculate(request,path,reader,cancel=cancel);check_cancel(cancel)
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    atomic_json(folder/'request.json',request.model_dump());atomic_json(folder/'result.json',result)
    manifest={'schema_version':1,'line':'R08','kind':'seeded_optical_flow','status':'complete',
              'input_hashes':{'request.json':sha256_file(folder/'request.json')},
              'output':{'file':'result.json','sha256':sha256_file(folder/'result.json')},
              'code_hashes':code(),'environment':environment(),'limits':result['limits']+[
                  'Offline verification checks integrity and bindings, not optical recomputation',
                  'Source recomputation requires current code/environment; version metadata is not identical-build proof or signed custody']}
    if reader.probe(path,cancel=cancel)['media_sha256']!=request.media_sha256:raise ValueError('Flow source changed before publication')
    check_cancel(cancel);atomic_json(folder/'manifest.json',manifest)
    return manifest


def verify(folder,*,path=None,reader=None,cancel=None):
    folder=Path(folder);names=('request.json','result.json','manifest.json')
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular flow directory required')
    for name in names:
        if (folder/name).is_symlink() or not (folder/name).is_file():raise ValueError('Regular flow artifacts required')
    hashes={name:sha256_file(folder/name) for name in names}
    manifest=json.loads((folder/'manifest.json').read_text())
    if (manifest.get('schema_version'),manifest.get('line'),manifest.get('kind'),manifest.get('status'))!=(1,'R08','seeded_optical_flow','complete'):raise ValueError('Complete flow manifest required')
    if manifest.get('input_hashes')!={'request.json':hashes['request.json']} or manifest.get('output')!={'file':'result.json','sha256':hashes['result.json']}:raise ValueError('Flow artifact hash mismatch')
    recorded=manifest.get('code_hashes')
    if not isinstance(recorded,dict) or not recorded or len(recorded)>32 or any(not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for v in recorded.values()):raise ValueError('Invalid flow code inventory')
    if not isinstance(manifest.get('environment'),dict) or not manifest['environment']:raise ValueError('Recorded flow environment required')
    request=Request.model_validate_json((folder/'request.json').read_text())
    result=json.loads((folder/'result.json').read_text());Contract.finite_tree(result)
    if not isinstance(result,dict) or result.get('schema_version')!=1 or result.get('line')!='R08' or result.get('request')!=request.model_dump():raise ValueError('Flow request/result binding mismatch')
    validate_frames(result.get('frames'),request)
    if path is not None:
        if manifest.get('environment')!=environment() or manifest.get('code_hashes')!=code():raise ValueError('Flow code/environment differs')
        if result!=calculate(request,path,reader,cancel=cancel):raise ValueError('Flow recomputation differs')
    for name,digest in hashes.items():
        if (folder/name).is_symlink() or sha256_file(folder/name)!=digest:raise ValueError('Flow artifact changed during verification')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--video',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(json.loads(args.request.read_text()),args.video,args.output)
