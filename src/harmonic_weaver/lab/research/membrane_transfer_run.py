"""Reproducible finite R07 transfer bank, with same-environment recomputation."""
import argparse
import json
import platform
from pathlib import Path
import numpy as np
import scipy
from ..cache import atomic_json,sha256_file
from .membrane_transfer import Request,compare


def environment():
    return {'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}


def run(request,folder):
    request=Request.model_validate(request)
    result=compare(request)
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    atomic_json(folder/'request.json',request.model_dump())
    atomic_json(folder/'result.json',result)
    manifest={'schema_version':1,'line':'R07','kind':'modal_transfer_comparison','status':'complete',
        'input_hashes':{'request.json':sha256_file(folder/'request.json')},
        'output':{'file':'result.json','sha256':sha256_file(folder/'result.json')},
        'code_hashes':{name:sha256_file(Path(__file__).with_name(name)) for name in
            ('membrane.py','membrane_transfer.py','membrane_transfer_run.py')},
        'environment':environment(),'limits':result['limits']+[
            'Exact recomputation verifier requires the recorded Python/NumPy/SciPy versions',
            'Version matching alone does not prove identical numerical backend/build',
            'Local hashes and recomputation are not signed custody or physical validation']}
    atomic_json(folder/'manifest.json',manifest)
    return manifest


def verify(folder):
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular transfer directory required')
    names=('request.json','result.json','manifest.json')
    for name in names:
        if (folder/name).is_symlink() or not (folder/name).is_file():raise ValueError('Regular transfer artifacts required')
    hashes={name:sha256_file(folder/name) for name in names}
    manifest=json.loads((folder/'manifest.json').read_text())
    if (manifest.get('schema_version'),manifest.get('line'),manifest.get('kind'),manifest.get('status'))!=(1,'R07','modal_transfer_comparison','complete'):
        raise ValueError('Complete transfer manifest required')
    if manifest.get('input_hashes')!={'request.json':hashes['request.json']} or manifest.get('output')!={'file':'result.json','sha256':hashes['result.json']}:
        raise ValueError('Transfer inventory/hash mismatch')
    if manifest.get('environment')!=environment():raise ValueError('Recorded numerical environment differs; exact verification unavailable')
    expected={name:sha256_file(Path(__file__).with_name(name)) for name in ('membrane.py','membrane_transfer.py','membrane_transfer_run.py')}
    if manifest.get('code_hashes')!=expected:raise ValueError('Transfer implementation changed; exact verification unavailable')
    request=Request.model_validate_json((folder/'request.json').read_text())
    if json.loads((folder/'result.json').read_text())!=compare(request):raise ValueError('Transfer recomputation differs from artifact')
    for name,digest in hashes.items():
        if (folder/name).is_symlink() or sha256_file(folder/name)!=digest:raise ValueError('Transfer artifact changed during verification')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(json.loads(args.request.read_text()),args.output)
