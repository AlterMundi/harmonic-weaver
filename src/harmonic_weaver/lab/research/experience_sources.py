"""Resolve R10 stimuli through verified R05 PCM and frozen evaluation/video binding."""
import json
from typing import Literal
import soundfile as sf
from pydantic import Field,model_validator
from ..contracts import Contract
from ..cache import sha256_file
from .experience_protocol import Request,Stimulus
from .source_binding import source_binding


class Reference(Contract):
    id:str=Field(min_length=1,max_length=80)
    r05_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    arm:Literal['single','excited','mapped']='single'


class Selection(Request):
    stimuli:list[Reference]=Field(min_length=1,max_length=8)
    idempotency_key:str|None=Field(default=None,pattern=r'^[a-f0-9]{32}$')


class Source(Contract):
    stimulus_id:str=Field(min_length=1,max_length=80)
    r05_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    arm:Literal['single','excited','mapped']
    manifest_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    input_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    pcm_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    media_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    evaluation_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    run_index:int=Field(ge=0)
    source_index:int=Field(ge=0)
    person_id:str=Field(min_length=1,max_length=80)
    source_start_s:float=Field(ge=0)
    source_end_s:float=Field(gt=0)
    sample_rate:int=Field(gt=0)
    pcm_frames:int=Field(gt=0)

    @model_validator(mode='after')
    def interval(self):
        if not 0<self.source_end_s-self.source_start_s<=120:raise ValueError('R10 requires source crop at most 120s')
        if self.pcm_frames/self.sample_rate+1/self.sample_rate<self.source_end_s-self.source_start_s:raise ValueError('PCM shorter than video crop')
        return self

    def stimulus(self):
        return Stimulus(id=self.stimulus_id,reference=f'r05:{self.r05_id}:{self.arm}',start_s=self.source_start_s,end_s=self.source_end_s,nominal_audio_offset_s=0)


def resolve(resonators,evaluation,reference):
    if evaluation is None:raise ValueError('Evaluation source library required for audiovisual stimulus')
    reference=Reference.model_validate(reference)
    manifest=resonators.artifact(reference.r05_id,'manifest.json');manifest_digest=sha256_file(manifest)
    input_path=resonators.artifact(reference.r05_id,'input.json');document=json.loads(input_path.read_text())
    _,source=source_binding(evaluation,document)
    name='sum.wav' if reference.arm=='single' else f'{reference.arm}-sum.wav'
    pcm=resonators.artifact(reference.r05_id,name);info=sf.info(pcm)
    if info.channels!=1:raise ValueError('R10 stimulus requires mono R05 sum')
    result=Source(stimulus_id=reference.id,r05_id=reference.r05_id,arm=reference.arm,
        manifest_sha256=manifest_digest,input_sha256=sha256_file(input_path),pcm_sha256=sha256_file(pcm),
        media_sha256=source['media_sha256'],evaluation_id=source['evaluation_id'],run_index=source['run_index'],
        source_index=source['source_index'],person_id=source['person_id'],source_start_s=source['source_start_s'],
        source_end_s=source['source_end_s'],sample_rate=info.samplerate,pcm_frames=info.frames)
    if sha256_file(resonators.artifact(reference.r05_id,'manifest.json'))!=manifest_digest:raise ValueError('R05 changed during stimulus resolution')
    return result
