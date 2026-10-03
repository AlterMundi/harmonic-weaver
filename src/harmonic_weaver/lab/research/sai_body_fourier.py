"""Explicit private frozen-source consumer of Oliva's offline body bridge."""
from dataclasses import asdict
import fcntl
import importlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Contract, Number, Preset, MotionFrame
from ..cache import atomic_json, sha256_file
from .sai_fourier import bridge
from .coincidence_service import CoincidenceService


def body_bridge():
    return importlib.import_module(bridge().__package__+'.body_fourier')


class Settings(Contract):
    schema_version: Literal[1] = 1
    channels: list[list[int]] = Field(min_length=1,max_length=34)
    sample_hz: Number = Field(gt=0,le=240)
    scale: Number = Field(gt=0)
    scale_unit: Literal['frame_height','meter']
    scale_provenance: str = Field(min_length=1,max_length=500)
    min_samples: int = Field(default=64,ge=4,le=4800)
    absolute_tolerance_s: Number = Field(default=.00001,ge=0,le=.01)
    relative_tolerance: Number = Field(default=.000001,ge=0,le=.01)
    max_gap_s: Number = Field(default=.25,gt=0,le=5)
    minimum_confidence: Number = Field(default=.5,ge=0,le=1)
    seeds: list[int] = Field(default_factory=lambda:[7,19,41],min_length=1,max_length=4)
    preset: Preset

    @model_validator(mode='after')
    def valid(self):
        body_bridge().BodyConfig('validation',**self.config())
        if len(set(self.seeds))!=len(self.seeds) or any(not 0<=s<=2147483647 for s in self.seeds):
            raise ValueError('Distinct bounded nonnegative seeds required')
        if self.preset.algorithm.id=='baseline' or self.preset.response.pluck_enabled:
            raise ValueError('Choose a descriptive non-baseline preset with plucks disabled')
        if self.max_gap_s>self.preset.algorithm.max_gap_s:
            raise ValueError('Preparation gap exceeds preset model gap')
        return self

    def config(self):
        return self.model_dump(exclude={'schema_version','seeds','preset'})


class SourceRequest(Contract):
    job_id: str = Field(min_length=1,max_length=80)
    person_id: str = Field(min_length=1,max_length=80)
    start_s: Number = Field(ge=0)
    end_s: Number = Field(gt=0)
    settings: Settings


def freeze(library, request):
    request=SourceRequest.model_validate(request)
    frames,provenance=library.spatial_segment(request.job_id,request.start_s,request.end_s)
    if len(frames)>4800 or len(frames)*len(request.settings.seeds)>14400:
        raise ValueError('Choose at most 4800 frames and 14400 frames × seeds')
    config=body_bridge().BodyConfig(request.person_id,**request.settings.config())
    blocks,support=body_bridge().prepare_blocks(frames,config,provenance=provenance)
    document={'frames':[f.model_dump() for f in frames],'provenance':provenance}
    return request,document,support


def calculate(request,document):
    request=SourceRequest.model_validate(request)
    if len(document['frames'])>4800 or len(document['frames'])*len(request.settings.seeds)>14400:
        raise ValueError('Frozen body computation exceeds frame budget')
    frames=[MotionFrame.model_validate(f) for f in document['frames']]
    config=body_bridge().BodyConfig(request.person_id,**request.settings.config())
    blocks,support=body_bridge().prepare_blocks(frames,config,provenance=document['provenance'])
    return {'schema_version':1,'kind':'sai_body_fourier','request':request.model_dump(),
            'preparation':support,'comparison':body_bridge().compare_blocks(blocks,
                seeds=request.settings.seeds,preset=request.settings.preset),
            'effective_modules':body_bridge().effective_modules(),
            'limits':['Private frozen in-memory generation; disk cache/video not reverified',
                      'Offline whole-block controls, not causal live processing',
                      'Explicit scale is a declaration, not measured or transferred calibration',
                      'Spectral preservation does not imply articulated geometry preservation',
                      'No HIT, causal coupling, efficiency or perceptual validation']}


def verify(folder):
    folder=Path(folder)
    if folder.is_symlink():raise ValueError('Body Fourier directory unavailable')
    report=json.loads((folder/'manifest.json').read_text())
    if report.get('status')!='complete' or report.get('line')!='SAI-BODY-FOURIER':raise ValueError('Body Fourier run incomplete')
    for name,expected in {**report['input_hashes'],'result.json':report['output']['sha256']}.items():
        if name not in ('request.json','input.json','result.json'):raise ValueError('Unknown frozen artifact')
        path=folder/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>128*1024*1024 or sha256_file(path)!=expected:
            raise ValueError('Body Fourier artifact changed or unavailable')
    request=SourceRequest.model_validate_json((folder/'request.json').read_text())
    result=json.loads((folder/'result.json').read_text());Contract.finite_tree(result)
    if result.get('kind')!='sai_body_fourier' or result.get('request')!=request.model_dump():raise ValueError('Frozen request differs')
    document=json.loads((folder/'input.json').read_text())
    if len(document['frames'])>4800 or len(document['frames'])*len(request.settings.seeds)>14400:raise ValueError('Frozen body budget differs')
    support=result['preparation']
    if support['input_frames']!=len(document['frames']):raise ValueError('Frozen frame count differs')
    if support['input_frames']!=support['retained_frames']+support['excluded_frames']:raise ValueError('Body support differs')
    expected={(i,seed) for i in range(len(support['blocks'])) for seed in request.settings.seeds}
    rows=result['comparison']['results']
    if len(rows)!=len(expected) or {(r['block_index'],r['seed']) for r in rows}!=expected:raise ValueError('Body block/seed inventory differs')
    expected_config=json.loads(json.dumps(asdict(body_bridge().BodyConfig(request.person_id,**request.settings.config()))))
    for row in rows:
        if row['person_id']!=request.person_id or row['config']!=expected_config:
            raise ValueError('Frozen body selection differs')
        for descriptor in row['descriptors'].values():
            common=descriptor['common_observed']
            if not 0<=common<=row['samples'] or descriptor['total']!=row['samples']:raise ValueError('Descriptor support differs')
            if set(descriptor['conditions'])!={'original','shared','independent'}:raise ValueError('Descriptor conditions differ')
    return report


def run_frozen(folder):
    folder=Path(folder)
    if folder.is_symlink() or any((folder/n).is_symlink() for n in ('request.json','input.json','worker.lock')):
        raise ValueError('Frozen body input unavailable')
    with (folder/'worker.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (folder/'manifest.json').exists() or (folder/'result.json').exists():raise ValueError('Body job already published')
        hashes={n:sha256_file(folder/n) for n in ('request.json','input.json')}
        if (folder/'job.json').exists():
            job=json.loads((folder/'job.json').read_text())
            if job.get('input_hashes')!=hashes:raise ValueError('Queued frozen body inputs changed')
        report={'schema_version':1,'line':'SAI-BODY-FOURIER','status':'running','input_hashes':hashes}
        atomic_json(folder/'manifest.json',report)
        try:
            request=json.loads((folder/'request.json').read_text());document=json.loads((folder/'input.json').read_text())
            result=calculate(request,document)
            if any((folder/n).is_symlink() or sha256_file(folder/n)!=h for n,h in hashes.items()):raise ValueError('Body input changed during calculation')
            atomic_json(folder/'result.json',result)
            report.update(status='complete',output={'file':'result.json','sha256':sha256_file(folder/'result.json')},
                          retained_frames=result['preparation']['retained_frames'],excluded_frames=result['preparation']['excluded_frames'])
            atomic_json(folder/'manifest.json',report);return verify(folder)
        except Exception as exc:
            report.update(status='failed',error_type=type(exc).__name__);report.pop('output',None)
            atomic_json(folder/'manifest.json',report);raise


class BodyFourierService(CoincidenceService):
    line='SAI-BODY-FOURIER'
    module='harmonic_weaver.lab.research.sai_body_fourier'
    artifacts=('request.json','input.json','result.json','manifest.json')

    def start(self,library,request):
        request,document,support=freeze(library,request)
        return self._start({'request.json':request.model_dump(),'input.json':document})

    def artifact(self,ident,name):
        path=super().artifact(ident,name)
        if name!='manifest.json':verify(self.folder(ident))
        return path


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--folder',type=Path,required=True)
    run_frozen(parser.parse_args().folder)
