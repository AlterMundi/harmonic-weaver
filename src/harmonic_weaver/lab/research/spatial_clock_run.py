"""Frozen clock fits; recomputation does not authenticate synchronization."""
import json
import platform
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .spatial_clock_fit import Request, fit as evaluate

Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
FILES = ('request.json', 'result.json', 'manifest.json')
CODE = ('spatial_clock_run.py', 'spatial_clock_fit.py', 'spatial_observations.py', '../contracts.py')


class Input(Contract):
    fit:Request


def calculate(frozen):
    return evaluate(frozen.fit)


class Manifest(Contract):
    schema_version: Literal[1]
    line: Literal['R09']
    kind: Literal['spatial_clock_fit']
    status: Literal['complete']
    input_hashes: dict[str, Digest]
    output: dict[str, str]
    code_hashes: dict[str, Digest] = Field(min_length=1, max_length=32)
    environment: dict[str, str] = Field(min_length=1, max_length=32)
    limits: list[str] = Field(max_length=16)


def environment():
    return {'python': platform.python_version(), 'metric': 'spatial_clock_fit_v1'}


def code_hashes():
    return {name: sha256_file(Path(__file__).parent / name) for name in CODE}


def run(request, folder):
    frozen = Input.model_validate(request)
    result = calculate(frozen)
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder / 'request.json', frozen.model_dump())
    atomic_json(folder / 'result.json', result)
    manifest = Manifest(schema_version=1, line='R09', kind='spatial_clock_fit',
        status='complete', input_hashes={'request.json': sha256_file(folder / 'request.json')},
        output={'file': 'result.json', 'sha256': sha256_file(folder / 'result.json')},
        code_hashes=code_hashes(), environment=environment(), limits=result['limits'] + [
            'Clock anchors/evidence are caller-declared, not authenticated measurements',
            'Frozen-input recomputation verifies arithmetic, not physical synchronization',
            'Historical integrity reads are not current-code recomputation; hashes are not signed custody'])
    atomic_json(folder / 'manifest.json', manifest.model_dump())
    return manifest.model_dump()


def verify(folder, *, recompute=True):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Regular clock fit directory required')
    for name in FILES:
        path = folder / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Regular clock fit artifacts required')
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('Spatial clock fit artifact exceeds read budget')
    hashes = {name: sha256_file(folder / name) for name in FILES}
    manifest = Manifest.model_validate_json((folder / 'manifest.json').read_text()).model_dump()
    if manifest['input_hashes'] != {'request.json': hashes['request.json']} or manifest['output'] != {'file': 'result.json', 'sha256': hashes['result.json']}:
        raise ValueError('Spatial clock fit inventory/hash mismatch')
    frozen = Input.model_validate_json((folder / 'request.json').read_text())
    result = json.loads((folder / 'result.json').read_text())
    Contract.finite_tree(result)
    if not isinstance(result, dict) or result.get('schema_version') != 1 or result.get('line') != 'R09' or result.get('request') != frozen.fit.model_dump():
        raise ValueError('Spatial clock fit result/input binding mismatch')
    if recompute:
        if manifest['environment'] != environment() or manifest['code_hashes'] != code_hashes():
            raise ValueError('Recorded clock fit implementation/environment differs')
        if result != calculate(frozen):
            raise ValueError('Spatial clock fit recomputation differs')
    for name, digest in hashes.items():
        if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
            raise ValueError('Spatial clock fit changed during verification')
    return manifest


def read_verified(folder):
    manifest = verify(folder, recompute=False)
    current = manifest['environment'] == environment() and manifest['code_hashes'] == code_hashes()
    if current:
        verify(folder)
    return {**manifest, 'read_verification': 'recomputed' if current else 'historical_integrity_only'}
