"""Persist color proposals without PNG/video copies; optional source recomputation."""
import json,platform
from pathlib import Path
import cv2
import numpy as np
import scipy
from pydantic import Field
from ..contracts import Contract,Number
from ..cache import atomic_json,sha256_file
from .rope_mask import Settings,propose
from .rope_mask_contract import Result
from .rope_reader import RopeReader


class Request(Contract):
    media_sha256:str=Field(pattern='^[a-f0-9]{64}$')
    frame_index:int=Field(ge=0)
    time_s:Number=Field(ge=0)
    width_px:int=Field(ge=1,le=32768)
    height_px:int=Field(ge=1,le=32768)
    settings:Settings=Field(default_factory=Settings)


def environment():return {'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'opencv':cv2.__version__}
def code():return {name:sha256_file(Path(__file__).parent/name) for name in ('rope_mask.py','rope_mask_contract.py','rope_mask_run.py','rope_reader.py','rope_media.py','rope_process.py','../contracts.py')}


def calculate(request,path,reader=None):
    request=Request.model_validate(request);reader=reader or RopeReader();media=reader.probe(path)
    if (media['media_sha256'],media['width_px'],media['height_px'])!=(request.media_sha256,request.width_px,request.height_px):raise ValueError('Mask source identity mismatch')
    if request.frame_index>=len(media['frame_times_s']) or abs(request.time_s-media['frame_times_s'][request.frame_index])>1e-6:raise ValueError('Mask source clock mismatch')
    png=reader.frame(path,request.frame_index,request.media_sha256)
    bgr=cv2.imdecode(np.frombuffer(png,dtype=np.uint8),cv2.IMREAD_COLOR)
    if bgr is None or bgr.shape[:2]!=(request.height_px,request.width_px):raise ValueError('Mask image dimensions mismatch')
    result=propose(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB),request.settings)
    if reader.probe(path)['media_sha256']!=request.media_sha256:raise ValueError('Mask source changed during calculation')
    return {**result,'media_sha256':request.media_sha256,'frame_index':request.frame_index,'time_s':request.time_s}


def run(request,path,folder,reader=None):
    request=Request.model_validate(request);reader=reader or RopeReader();result=calculate(request,path,reader)
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    atomic_json(folder/'request.json',request.model_dump());atomic_json(folder/'result.json',result)
    manifest={'schema_version':1,'line':'R08','kind':'color_candidates','status':'complete',
        'input_hashes':{'request.json':sha256_file(folder/'request.json')},'output':{'file':'result.json','sha256':sha256_file(folder/'result.json')},
        'code_hashes':code(),'environment':environment(),'limits':result['limits']+[
            'Stored hash integrity is not recomputation; current local source required for reverify',
            'No PNG/video copied; no source path retained; proposals are not accepted annotations',
            'Version metadata does not guarantee identical FFmpeg build or signed custody']}
    if reader.probe(path)['media_sha256']!=request.media_sha256:raise ValueError('Mask source changed before publication')
    atomic_json(folder/'manifest.json',manifest);return manifest


def verify(folder,*,path=None,reader=None):
    folder=Path(folder);names=('request.json','result.json','manifest.json')
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular mask directory required')
    for n in names:
        if (folder/n).is_symlink() or not (folder/n).is_file():raise ValueError('Regular mask artifacts required')
    hashes={n:sha256_file(folder/n) for n in names};manifest=json.loads((folder/'manifest.json').read_text())
    if (manifest.get('schema_version'),manifest.get('line'),manifest.get('kind'),manifest.get('status'))!=(1,'R08','color_candidates','complete'):raise ValueError('Complete mask manifest required')
    if manifest.get('input_hashes')!={'request.json':hashes['request.json']} or manifest.get('output')!={'file':'result.json','sha256':hashes['result.json']}:raise ValueError('Mask artifact hash mismatch')
    request=Request.model_validate_json((folder/'request.json').read_text())
    result=json.loads((folder/'result.json').read_text())
    Result.model_validate(result)
    for key in ('media_sha256','frame_index','time_s','width_px','height_px','settings'):
        if result.get(key)!=request.model_dump()[key]:raise ValueError('Mask request/result binding mismatch')
    if path is not None:
        if manifest.get('environment')!=environment() or manifest.get('code_hashes')!=code():raise ValueError('Mask numerical environment/code differs')
        if result!=calculate(request,path,reader):raise ValueError('Mask recomputation differs')
    for n,digest in hashes.items():
        if (folder/n).is_symlink() or sha256_file(folder/n)!=digest:raise ValueError('Mask artifact changed during verification')
    return manifest
