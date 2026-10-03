"""Frozen spatial conversions; recomputation does not authenticate observations."""
import json
import hashlib
import platform
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .spatial_adapter import Request, convert as evaluate
from .spatial_observations import Stream
from .spatial_clock_binding import Application,transformed

Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
FILES = ('request.json', 'result.json', 'manifest.json')
CODE = ('spatial_run.py', 'spatial_adapter.py', 'spatial_observations.py', 'spatial_clock_binding.py', 'spatial_clock_fit.py', '../contracts.py')


class Provenance(Contract):
    job_id:str=Field(min_length=1,max_length=80)
    media_id:str|None=None
    cache_key:str=Field(min_length=1,max_length=160)
    generation:str=Field(min_length=1,max_length=160)
    effective_device:str=Field(min_length=1,max_length=80)
    start_s:float=Field(ge=0)
    end_s:float=Field(gt=0)
    verification:Literal['completed_in_memory_generation']


def stream_digest(stream):
    return hashlib.sha256(json.dumps(Stream.model_validate(stream).model_dump(),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class MultiviewOrigin(Contract):
    run_id:Annotated[str,Field(pattern=r'^[a-f0-9]{32}$')]
    manifest_sha256:Digest
    request_sha256:Digest
    result_sha256:Digest
    stream_sha256:Digest
    verification:Literal['local_artifact_integrity']


class Input(Contract):
    conversion: Request|None=None
    stream:Stream|None=None
    clock_application:Application|None=None
    tracking_provenance:Provenance|None=None
    multiview_origin:MultiviewOrigin|None=None

    @model_validator(mode='after')
    def segment(self):
        if (self.conversion is None)==(self.stream is None):raise ValueError('Choose exactly one conversion or declared stream')
        if self.clock_application is not None and self.stream is None:raise ValueError('Clock application requires declared stream')
        if self.multiview_origin is not None:
            if self.stream is None or self.clock_application is not None:raise ValueError('Multiview origin requires its original stream')
            if self.multiview_origin.stream_sha256!=stream_digest(self.stream):raise ValueError('Multiview origin stream binding mismatch')
            if self.stream.provider!='calibrated_multiview' or self.stream.dimensions!=3 or any(p.state not in ('inferred','missing') for f in self.stream.frames for p in f.points):raise ValueError('Multiview origin requires inferred/missing 3D')
        p=self.tracking_provenance
        if p is not None and self.conversion is None:raise ValueError('Tracking provenance only belongs to resolved MotionFrames')
        if p is not None:
            if not 0<p.end_s-p.start_s<=120 or any(not p.start_s<=f.source_time_s<=p.end_s for f in self.conversion.frames):
                raise ValueError('Frozen observations outside provenance segment')
        return self


def calculate(frozen):
    if frozen.clock_application is not None and frozen.stream.model_dump()!=transformed(frozen.clock_application).model_dump():raise ValueError('Frozen clock application differs from stream')
    if frozen.stream is not None:
        stream=frozen.stream
        result={'schema_version':1,'line':'R09','input_kind':'external_stream','request':stream.model_dump(),'stream':stream.model_dump(),
            'common_times_s':[stream.clock.common_time(f.source_time_s) for f in stream.frames],
            'coverage':{state:sum(p.state==state for f in stream.frames for p in f.points) for state in ('observed','held','inferred','missing')},
            'limits':['External stream is caller-declared; persistence validates contract, not depth, calibration or synchronization',
                      'Coordinates, units, support states and source timestamps are preserved without interpolation']}
        Contract.finite_tree(result)
    else:result=evaluate(frozen.conversion)
    if frozen.tracking_provenance is not None:
        result['tracking_provenance']=frozen.tracking_provenance.model_dump()
        result['limits'].append('Recorded completed in-memory generation, not current disk/video integrity or signed custody')
    if frozen.clock_application is not None:
        result['clock_application']=frozen.clock_application.model_dump()
        result['limits'].append('Application freezes verified local source IDs/hashes; source declarations remain unauthenticated physically')
    if frozen.multiview_origin is not None:
        result['multiview_origin']=frozen.multiview_origin.model_dump()
        result['limits'].append('Multiview origin binds verified local calculation artifacts at publication; camera calibration, pairing and timing remain declared')
    return result


class Manifest(Contract):
    schema_version: Literal[1]
    line: Literal['R09']
    kind: Literal['spatial_conversion']
    status: Literal['complete']
    input_hashes: dict[str, Digest]
    output: dict[str, str]
    code_hashes: dict[str, Digest] = Field(min_length=1, max_length=32)
    environment: dict[str, str] = Field(min_length=1, max_length=32)
    limits: list[str] = Field(max_length=16)


def environment():
    return {'python': platform.python_version(), 'metric': 'spatial_conversion_v1'}


def code_hashes():
    return {name: sha256_file(Path(__file__).parent / name) for name in CODE}


def run(request, folder):
    frozen = Input.model_validate(request)
    result = calculate(frozen)
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder / 'request.json', frozen.model_dump())
    atomic_json(folder / 'result.json', result)
    manifest = Manifest(schema_version=1, line='R09', kind='spatial_conversion',
        status='complete', input_hashes={'request.json': sha256_file(folder / 'request.json')},
        output={'file': 'result.json', 'sha256': sha256_file(folder / 'result.json')},
        code_hashes=code_hashes(), environment=environment(), limits=result['limits'] + [
            'Frozen observations are caller-declared; this runner does not authenticate original tracking artifacts',
            'Frozen-input recomputation verifies conversion, not tracking quality, depth, calibration or synchronization',
            'Historical integrity reads are not current-code recomputation; hashes are not signed custody'])
    atomic_json(folder / 'manifest.json', manifest.model_dump())
    return manifest.model_dump()


def verify(folder, *, recompute=True):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Regular conversion directory required')
    for name in FILES:
        path = folder / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Regular conversion artifacts required')
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('Spatial conversion artifact exceeds read budget')
    hashes = {name: sha256_file(folder / name) for name in FILES}
    manifest = Manifest.model_validate_json((folder / 'manifest.json').read_text()).model_dump()
    if manifest['input_hashes'] != {'request.json': hashes['request.json']} or manifest['output'] != {'file': 'result.json', 'sha256': hashes['result.json']}:
        raise ValueError('Spatial conversion inventory/hash mismatch')
    frozen = Input.model_validate_json((folder / 'request.json').read_text())
    result = json.loads((folder / 'result.json').read_text())
    Contract.finite_tree(result)
    if not isinstance(result, dict) or result.get('schema_version') != 1 or result.get('line') != 'R09' or result.get('request') != (frozen.stream or frozen.conversion).model_dump():
        raise ValueError('Spatial conversion result/input binding mismatch')
    if frozen.stream is not None and (result.get('stream')!=frozen.stream.model_dump() or result.get('input_kind')!='external_stream'):raise ValueError('External stream result/input binding mismatch')
    if result.get('tracking_provenance') != (frozen.tracking_provenance.model_dump() if frozen.tracking_provenance else None):raise ValueError('Spatial conversion provenance binding mismatch')
    if result.get('clock_application')!=(frozen.clock_application.model_dump() if frozen.clock_application else None):raise ValueError('Clock application provenance binding mismatch')
    if result.get('multiview_origin')!=(frozen.multiview_origin.model_dump() if frozen.multiview_origin else None):raise ValueError('Multiview origin result/input binding mismatch')
    if recompute:
        if manifest['environment'] != environment() or manifest['code_hashes'] != code_hashes():
            raise ValueError('Recorded conversion implementation/environment differs')
        if result != calculate(frozen):
            raise ValueError('Spatial conversion recomputation differs')
    for name, digest in hashes.items():
        if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
            raise ValueError('Spatial conversion changed during verification')
    return manifest


def read_verified(folder):
    manifest = verify(folder, recompute=False)
    current = manifest['environment'] == environment() and manifest['code_hashes'] == code_hashes()
    if current:
        verify(folder)
    return {**manifest, 'read_verification': 'recomputed' if current else 'historical_integrity_only'}
