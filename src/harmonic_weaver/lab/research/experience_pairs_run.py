"""Frozen R10 paired analyses; recomputation is not scientific validation."""
import json
import platform
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .experience_pairs import Input, calculate

Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
FILES = ('request.json', 'result.json', 'manifest.json')
CODE = ('experience_pairs_run.py', 'experience_pairs.py', 'experience_analysis.py', 'experience_protocol.py',
        'experience_response.py', 'experience_response_service.py', '../contracts.py')


class Manifest(Contract):
    schema_version: Literal[1]
    line: Literal['R10']
    kind: Literal['experience_paired_analysis']
    status: Literal['complete']
    input_hashes: dict[str, Digest]
    output: dict[str, str]
    code_hashes: dict[str, Digest] = Field(min_length=1, max_length=32)
    environment: dict[str, str] = Field(min_length=1, max_length=32)
    limits: list[str] = Field(max_length=16)


def environment():
    return {'python': platform.python_version(), 'metric': 'experience_pairs_v1'}


def code_hashes():
    return {name: sha256_file(Path(__file__).parent / name) for name in CODE}


def run(request, folder):
    frozen = Input.model_validate(request)
    result = calculate(frozen)
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder / 'request.json', frozen.model_dump())
    atomic_json(folder / 'result.json', result)
    manifest = Manifest(schema_version=1, line='R10', kind='experience_paired_analysis',
        status='complete', input_hashes={'request.json': sha256_file(folder / 'request.json')},
        output={'file': 'result.json', 'sha256': sha256_file(folder / 'result.json')},
        code_hashes=code_hashes(), environment=environment(), limits=result['limits'] + [
            'Frozen response snapshots rechecked; source manifests are references, not signed custody',
            'Recomputation verifies descriptive metrics, not exposure, independence or scientific validity',
            'Historical integrity reads are not current-code recomputation; hashes are not signed custody'])
    atomic_json(folder / 'manifest.json', manifest.model_dump())
    return manifest.model_dump()


def verify(folder, *, recompute=True):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Regular paired analysis directory required')
    for name in FILES:
        path = folder / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Regular paired analysis artifacts required')
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('Paired analysis artifact exceeds read budget')
    hashes = {name: sha256_file(folder / name) for name in FILES}
    manifest = Manifest.model_validate_json((folder / 'manifest.json').read_text()).model_dump()
    if manifest['input_hashes'] != {'request.json': hashes['request.json']} or manifest['output'] != {'file': 'result.json', 'sha256': hashes['result.json']}:
        raise ValueError('Paired analysis inventory/hash mismatch')
    frozen = Input.model_validate_json((folder / 'request.json').read_text())
    result = json.loads((folder / 'result.json').read_text())
    Contract.finite_tree(result)
    if not isinstance(result, dict) or result.get('schema_version') != 1 or result.get('line') != 'R10':
        raise ValueError('Invalid paired analysis result')
    if result.get('input') != frozen.model_dump():
        raise ValueError('Paired analysis frozen source binding mismatch')
    if recompute:
        if manifest['environment'] != environment() or manifest['code_hashes'] != code_hashes():
            raise ValueError('Recorded paired analysis implementation/environment differs')
        if result != calculate(frozen):
            raise ValueError('Paired analysis recomputation differs')
    for name, digest in hashes.items():
        if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
            raise ValueError('Paired analysis changed during verification')
    return manifest


def read_verified(folder):
    manifest = verify(folder, recompute=False)
    current = manifest['environment'] == environment() and manifest['code_hashes'] == code_hashes()
    if current:
        verify(folder)
    return {**manifest, 'read_verification': 'recomputed' if current else 'historical_integrity_only'}
