"""Frozen R13 artifacts and repeatable verification, separate from live synthesis."""
import argparse,json,platform
from pathlib import Path
import numpy as np
from ..cache import atomic_json,sha256_file
from ..contracts import Contract
from ..evaluation.runner import digest
from .heldout import Request,calculate

FILES=('request.json','result.json','predictions.jsonl','manifest.json')
CODE=('heldout.py','heldout_run.py','../contracts.py','../evaluation/runner.py')

def identity():
    return {'code_hashes':{name:sha256_file(Path(__file__).parent/name) for name in CODE},
            'environment':{'python':platform.python_version(),'numpy':np.__version__,'metric':'r13_frozen_forecast_v1'}}

def run(request,folder):
    request=Request.model_validate(request);folder=Path(folder)
    manifest_path=folder/'manifest.json'
    if manifest_path.exists() and json.loads(manifest_path.read_text()).get('status')!='running':
        raise ValueError('Output already contains a result; choose a new folder')
    folder.mkdir(mode=0o700,parents=True,exist_ok=True)
    result=calculate(request);rows=result.pop('rows')
    atomic_json(folder/'request.json',request.model_dump());atomic_json(folder/'result.json',result)
    (folder/'predictions.jsonl').write_text(''.join(json.dumps(row,sort_keys=True,allow_nan=False)+'\n' for row in rows))
    manifest={'schema_version':1,'line':'R13','kind':'heldout_transfer','status':'complete',**identity(),
        'request_sha256':digest(request.model_dump()),'hashes':{name:sha256_file(folder/name) for name in FILES[:-1]},
        'settings':request.settings.model_dump(),'reservation':request.reservation,'results':result['results'],
        'limits':result['limits']+['Historical hash integrity is not current-code recomputation or signed custody']}
    atomic_json(folder/'manifest.json',manifest);return manifest

def verify(folder,*,recompute=False):
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular heldout run required')
    for name in FILES:
        path=folder/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>64*1024*1024:
            raise ValueError('Regular bounded R13 artifacts required')
    hashes={name:sha256_file(folder/name) for name in FILES}
    manifest=json.loads((folder/'manifest.json').read_text());Contract.finite_tree(manifest)
    if (manifest.get('schema_version')!=1 or manifest.get('line')!='R13' or manifest.get('kind')!='heldout_transfer'
        or manifest.get('status')!='complete' or manifest.get('hashes')!={name:hashes[name] for name in FILES[:-1]}):
        raise ValueError('Heldout manifest/hash mismatch')
    raw_request=json.loads((folder/'request.json').read_text())
    request=Request.model_validate(raw_request);request_hash=digest(raw_request)
    result=json.loads((folder/'result.json').read_text());Contract.finite_tree(result)
    if manifest['request_sha256']!=request_hash or result.get('request_sha256')!=request_hash:
        raise ValueError('Heldout frozen request binding differs')
    if manifest['results']!=result['results'] or manifest['settings']!=raw_request['settings']:
        raise ValueError('Heldout manifest summary differs')
    current=all(manifest.get(key)==value for key,value in identity().items())
    if recompute:
        if not current:raise ValueError('Recorded R13 implementation/environment differs')
        expected=calculate(request);rows=expected.pop('rows')
        if result!=expected:raise ValueError('Heldout result recomputation differs')
        recorded=[json.loads(line) for line in (folder/'predictions.jsonl').read_text().splitlines()]
        if recorded!=rows:raise ValueError('Heldout predictions recomputation differs')
    for name,sha in hashes.items():
        if (folder/name).is_symlink() or sha256_file(folder/name)!=sha:raise ValueError('R13 artifact changed while verifying')
    return {**manifest,'read_verification':'recomputed' if recompute else 'integrity_only', 'code_matches_current':current}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();folder=Path(args.output)
    try:run(json.loads(Path(args.request).read_text()),folder)
    except Exception as exc:
        manifest=folder/'manifest.json'
        if not manifest.exists() or json.loads(manifest.read_text()).get('status')=='running':
            atomic_json(manifest,{'line':'R13','status':'failed','error':str(exc)})
        raise

if __name__=='__main__':main()
