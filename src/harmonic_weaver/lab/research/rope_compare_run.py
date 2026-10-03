"""Reproducible R08 sampled curve comparison, with same-environment recomputation."""
import argparse
import json
import platform
from pathlib import Path
import numpy as np
from ..cache import atomic_json,sha256_file
from .rope_compare import Request,compare


def environment():
    return {'python':platform.python_version(),'numpy':np.__version__,'metric':'sampled_curve_v1'}


def run(request,folder):
    request=Request.model_validate(request)
    result=compare(request)
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    atomic_json(folder/'request.json',request.model_dump())
    atomic_json(folder/'result.json',result)
    manifest={'schema_version':1,'line':'R08','kind':'sampled_curve_comparison','status':'complete',
        'input_hashes':{'request.json':sha256_file(folder/'request.json')},
        'output':{'file':'result.json','sha256':sha256_file(folder/'result.json')},
        'code_hashes':{name:sha256_file((Path(__file__).parent/name)) for name in
            ('rope_annotations.py','rope_compare.py','rope_compare_run.py','../contracts.py')},
        'environment':environment(),'limits':result['limits']+[
            'Exact recomputation verifier requires the recorded Python/NumPy versions',
            'Version matching alone does not prove identical numerical backend/build',
            'Local hashes and recomputation are not signed custody or physical validation']}
    atomic_json(folder/'manifest.json',manifest)
    return manifest


def verify(folder,*,recompute=True):
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular curve comparison directory required')
    names=('request.json','result.json','manifest.json')
    for name in names:
        if (folder/name).is_symlink() or not (folder/name).is_file():raise ValueError('Regular curve comparison artifacts required')
    hashes={name:sha256_file(folder/name) for name in names}
    manifest=json.loads((folder/'manifest.json').read_text())
    if (manifest.get('schema_version'),manifest.get('line'),manifest.get('kind'),manifest.get('status'))!=(1,'R08','sampled_curve_comparison','complete'):
        raise ValueError('Complete curve comparison manifest required')
    if manifest.get('input_hashes')!={'request.json':hashes['request.json']} or manifest.get('output')!={'file':'result.json','sha256':hashes['result.json']}:
        raise ValueError('Curve comparison inventory/hash mismatch')
    if recompute and manifest.get('environment')!=environment():raise ValueError('Recorded numerical environment differs; exact verification unavailable')
    expected={name:sha256_file((Path(__file__).parent/name)) for name in ('rope_annotations.py','rope_compare.py','rope_compare_run.py','../contracts.py')}
    if recompute and manifest.get('code_hashes')!=expected:raise ValueError('Curve comparison implementation changed; exact verification unavailable')
    from ..contracts import Contract
    import re
    recorded=manifest.get('code_hashes')
    if not isinstance(recorded,dict) or not recorded or len(recorded)>32 or any(not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for v in recorded.values()):raise ValueError('Invalid recorded code inventory')
    if not isinstance(manifest.get('environment'),dict) or not manifest['environment']:raise ValueError('Recorded environment required')
    request=Request.model_validate_json((folder/'request.json').read_text())
    result=json.loads((folder/'result.json').read_text())
    Contract.finite_tree(result)
    if not isinstance(result,dict) or result.get('schema_version')!=1 or result.get('line')!='R08':raise ValueError('Invalid historical result envelope')
    if recompute and json.loads((folder/'result.json').read_text())!=compare(request):raise ValueError('Curve comparison recomputation differs from artifact')
    for name,digest in hashes.items():
        if (folder/name).is_symlink() or sha256_file(folder/name)!=digest:raise ValueError('Curve comparison artifact changed during verification')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(json.loads(args.request.read_text()),args.output)


def read_verified(folder):
    manifest=verify(folder,recompute=False)
    expected={name:sha256_file((Path(__file__).parent/name)) for name in ('rope_annotations.py','rope_compare.py','rope_compare_run.py','../contracts.py')}
    current=manifest.get('code_hashes')==expected and manifest.get('environment')==environment()
    if current:verify(folder)
    return {**manifest,'read_verification':'recomputed' if current else 'historical_integrity_only'}
