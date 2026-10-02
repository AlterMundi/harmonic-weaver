"""Frozen paired endpoint artifacts; recomputation does not authenticate inputs."""
import json
import platform
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
from pydantic import Field, model_validator

from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .rope_flow_paired import Request, compare as evaluate

Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Identifier = Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
FILES = ('request.json', 'result.json', 'manifest.json')
CODE = ('rope_flow_paired_run.py', 'rope_flow_paired.py', 'rope_flow_benchmark.py', 'rope_annotations.py',
        'rope_flow_contract.py', 'rope_flow_run.py', 'rope_flow.py', '../contracts.py')


class Source(Contract):
    id: Identifier
    manifest_sha256: Digest


class Input(Contract):
    benchmark: Request
    sources: dict[str, Source] = Field(min_length=2, max_length=16)

    @model_validator(mode='after')
    def source_labels(self):
        if set(self.sources) != set(self.benchmark.conditions):
            raise ValueError('Source provenance must match condition labels')
        return self


class Manifest(Contract):
    schema_version: Literal[1]
    line: Literal['R08']
    kind: Literal['paired_temporal_endpoint_comparison']
    status: Literal['complete']
    input_hashes: dict[str, Digest]
    output: dict[str, str]
    code_hashes: dict[str, Digest] = Field(min_length=1, max_length=32)
    environment: dict[str, str] = Field(min_length=1, max_length=32)
    limits: list[str] = Field(max_length=16)


def environment():
    return {'python': platform.python_version(), 'numpy': np.__version__,
            'metric': 'paired_temporal_endpoint_v1'}


def code_hashes():
    return {name: sha256_file(Path(__file__).parent / name) for name in CODE}


def run(request, folder):
    frozen = Input.model_validate(request)
    result = evaluate(frozen.benchmark)
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder / 'request.json', frozen.model_dump())
    atomic_json(folder / 'result.json', result)
    manifest = Manifest(schema_version=1, line='R08', kind='paired_temporal_endpoint_comparison',
        status='complete', input_hashes={'request.json': sha256_file(folder / 'request.json')},
        output={'file': 'result.json', 'sha256': sha256_file(folder / 'result.json')},
        code_hashes=code_hashes(), environment=environment(), limits=result['limits'] + [
            'Source IDs/hashes record caller-declared provenance; this runner does not authenticate original artifacts',
            'Frozen-input recomputation verifies the metric, not optical tracking against video or manual reference quality',
            'Historical integrity reads are not current-code recomputation; hashes are not signed custody'])
    atomic_json(folder / 'manifest.json', manifest.model_dump())
    return manifest.model_dump()


def verify(folder, *, recompute=True):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Regular benchmark directory required')
    for name in FILES:
        path = folder / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Regular benchmark artifacts required')
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('Benchmark artifact exceeds read budget')
    hashes = {name: sha256_file(folder / name) for name in FILES}
    manifest = Manifest.model_validate_json((folder / 'manifest.json').read_text()).model_dump()
    if manifest['input_hashes'] != {'request.json': hashes['request.json']} or manifest['output'] != {'file': 'result.json', 'sha256': hashes['result.json']}:
        raise ValueError('Benchmark inventory/hash mismatch')
    frozen = Input.model_validate_json((folder / 'request.json').read_text())
    result = json.loads((folder / 'result.json').read_text())
    Contract.finite_tree(result)
    if not isinstance(result, dict) or result.get('schema_version') != 1 or result.get('line') != 'R08' or result.get('request') != frozen.benchmark.model_dump():
        raise ValueError('Benchmark result/input binding mismatch')
    if recompute:
        if manifest['environment'] != environment() or manifest['code_hashes'] != code_hashes():
            raise ValueError('Recorded benchmark implementation/environment differs')
        if result != evaluate(frozen.benchmark):
            raise ValueError('Benchmark recomputation differs')
    for name, digest in hashes.items():
        if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
            raise ValueError('Benchmark changed during verification')
    return manifest


def read_verified(folder):
    manifest = verify(folder, recompute=False)
    current = manifest['environment'] == environment() and manifest['code_hashes'] == code_hashes()
    if current:
        verify(folder)
    return {**manifest, 'read_verification': 'recomputed' if current else 'historical_integrity_only'}
