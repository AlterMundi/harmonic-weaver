"""Owned locked writer and frozen-input verification for paired triangulation."""
import fcntl
import json
import platform
from pathlib import Path
import numpy as np
from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .spatial_multiview import Request, calculate
from .spatial_observations import Stream
from .coincidence import inspect_run

FILES=('request.json','result.json','manifest.json')
CODE=('spatial_multiview.py','spatial_multiview_worker.py','spatial_observations.py','../contracts.py')


def implementation():
    return {'code_hashes':{name:sha256_file(Path(__file__).parent/name) for name in CODE},
            'environment':{'python':platform.python_version(),'numpy':np.__version__,'algorithm':'paired_multiview_dlt_v1'}}


def verify(folder,*,recompute=False):
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular multiview folder required')
    for name in FILES:
        path=folder/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>64*1024*1024:raise ValueError('Regular bounded multiview artifacts required')
    hashes={name:sha256_file(folder/name) for name in FILES}
    manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('line')!='R09' or manifest.get('kind')!='paired_multiview_dlt' or manifest.get('status')!='complete':raise ValueError('Complete multiview manifest required')
    if manifest.get('input_hashes')!={'request.json':hashes['request.json']} or manifest.get('output')!={'file':'result.json','sha256':hashes['result.json']}:raise ValueError('Multiview artifact inventory/hash mismatch')
    request=Request.model_validate_json((folder/'request.json').read_text())
    result=json.loads((folder/'result.json').read_text());Contract.finite_tree(result)
    if not isinstance(result,dict) or result.get('schema_version')!=1 or result.get('line')!='R09':raise ValueError('Invalid multiview result contract')
    if result.get('input_kind')!='paired_multiview_dlt' or result.get('request')!=request.model_dump():raise ValueError('Multiview frozen input/result binding mismatch')
    stream=Stream.model_validate(result.get('stream'))
    if (stream.source_id,stream.subject_slot,stream.coordinate_frame,stream.calibration_id)!=(request.source_id,request.subject_slot,request.coordinate_frame,request.calibration_id):raise ValueError('Multiview stream source binding mismatch')
    if stream.dimensions!=3 or stream.units!='metres' or stream.provider!='calibrated_multiview' or any(p.state not in ('inferred','missing') for f in stream.frames for p in f.points):raise ValueError('Multiview output must preserve inferred/missing metric semantics')
    current=implementation();matches=all(manifest.get(key)==value for key,value in current.items())
    if recompute:
        if not matches:raise ValueError('Recorded multiview implementation/environment differs; repeat as a new run')
        if result!=calculate(request):raise ValueError('Multiview recomputation differs')
    if any((folder/name).is_symlink() or sha256_file(folder/name)!=digest for name,digest in hashes.items()):raise ValueError('Multiview artifacts changed during verification')
    return {**manifest,'implementation_matches':matches,'read_verification':'recomputed' if recompute else 'integrity_only'}


def run_frozen(folder):
    folder=Path(folder);request_path=folder/'request.json';lock_path=folder/'worker.lock'
    if folder.is_symlink() or not folder.is_dir() or request_path.is_symlink() or not request_path.is_file() or lock_path.is_symlink():raise ValueError('Regular multiview worker inputs required')
    with lock_path.open('a+b') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('Multiview writer already active') from exc
        if (folder/'manifest.json').exists():raise ValueError('Multiview run already has a manifest')
        digest=sha256_file(request_path)
        job_path=folder/'job.json'
        if job_path.is_symlink() or not job_path.is_file():raise ValueError('Frozen multiview job metadata required')
        job=json.loads(job_path.read_text())
        if job.get('input_hashes')!={'request.json':digest}:raise ValueError('Frozen multiview request changed before calculation')
        manifest={'schema_version':1,'line':'R09','kind':'paired_multiview_dlt','status':'running','input_hashes':{'request.json':digest}}
        atomic_json(folder/'manifest.json',manifest)
        try:
            result=calculate(Request.model_validate_json(request_path.read_text()))
            if request_path.is_symlink() or sha256_file(request_path)!=digest:raise ValueError('Multiview input changed during calculation')
            atomic_json(folder/'result.json',result)
            manifest.update(status='complete',output={'file':'result.json','sha256':sha256_file(folder/'result.json')},**implementation(),limits=result['limits'])
            atomic_json(folder/'manifest.json',manifest)
            return verify(folder)
        except Exception as exc:
            manifest.update(status='failed',error=str(exc));atomic_json(folder/'manifest.json',manifest);raise


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True);args=parser.parse_args();run_frozen(args.folder)
