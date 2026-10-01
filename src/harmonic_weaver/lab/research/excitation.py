"""Sparse causal excitations from a frozen single-signal selection, no live plucks."""
import math
from typing import Literal
from pydantic import Field,model_validator
from ..contracts import Contract,Number
from .candidate_input import CandidateRequest
from .coincidence import content_hash
from .event_candidates import extract_candidates


class Settings(Contract):
    mode:Literal['threshold_crossings','positive_delta']='threshold_crossings'
    high:Number=1
    low:Number=.2
    refractory_s:Number=Field(default=.2,ge=0,le=10)
    max_gap_s:Number=Field(default=.1,gt=0,le=5)
    reference_scale:Number=Field(default=1,gt=0,le=1000000)
    gain:Number=Field(default=1,ge=0,le=10)
    max_impulse:Number=Field(default=1,gt=0,le=10)
    positive_delta_min:Number=Field(default=0,ge=0,le=1000000)
    voice_weights:list[Number]=Field(default_factory=lambda:[1/6]*6,min_length=6,max_length=32)

    @model_validator(mode='after')
    def valid(self):
        if self.low>=self.high:raise ValueError('Low threshold must precede high')
        if any(v<0 or v>10 for v in self.voice_weights):raise ValueError('Voice weights in 0–10 required')
        return self


def prepare(document,settings,*,sample_rate,voices):
    settings=Settings.model_validate(settings);selection=CandidateRequest.model_validate(document['request'])
    if type(sample_rate) is not int or not 8000<=sample_rate<=96000 or type(voices) is not int or not 6<=voices<=32:
        raise ValueError('Explicit sample rate and 6–32 voices required')
    if len(settings.voice_weights)!=voices:raise ValueError('One explicit excitation weight per resonator required')
    if not isinstance(document.get('unit'),str) or not document['unit']:raise ValueError('Explicit input unit required')
    rows=document['rows']
    # Shared causal validation/crossing semantics; first high after a gap is not a crossing.
    candidates=extract_candidates(rows,high=settings.high,low=settings.low,
                                  refractory_s=settings.refractory_s,max_gap_s=settings.max_gap_s)
    if any(not selection.start_s<=row['time_s']<selection.end_s for row in rows):raise ValueError('Excitation observations outside selected segment')
    contributions=[]
    if settings.mode=='threshold_crossings':
        contributions=[{**event,'contribution':settings.reference_scale} for event in candidates['events']]
    else:
        previous=None;last_event=-math.inf
        for index,row in enumerate(rows):
            t=row['time_s'];value=row.get('value')
            if row.get('valid',True) is not True or type(value) not in (int,float) or not math.isfinite(value):
                previous=None;last_event=-math.inf;continue
            if previous is not None and t-previous[0]>settings.max_gap_s:previous=None;last_event=-math.inf
            if previous is not None:
                delta=value-previous[1]
                if delta>settings.positive_delta_min and t-last_event>=settings.refractory_s:
                    contributions.append({'index':index,'time_s':t,'value':value,'contribution':delta});last_event=t
            previous=(t,value) # consume every update, including refractory changes
    events=[]
    for event in contributions:
        strength=min(settings.max_impulse,settings.gain*event['contribution']/settings.reference_scale)
        events.append({**event,'sample_index':math.ceil((event['time_s']-selection.start_s)*sample_rate),
                       'strength':strength,'voice_impulses':[strength*w for w in settings.voice_weights]})
    return {'schema_version':1,'settings':settings.model_dump(),'selection':selection.model_dump(),
        'input_sha256':content_hash(document),'input_unit':document['unit'],
        'sample_rate':sample_rate,'voices':voices,'events':events,'resets':candidates['resets'],
        'provenance':document.get('provenance'),
        'limits':['Excitation is an explicit algorithm, not intention or physical force',
            'Threshold crossing uses fixed reference impulse; positive_delta uses raw positive difference, not acceleration',
            'reference_scale is declared in input units, not automatically fitted normalization',
            'Events quantized upward to sample clock; no earlier-than-observation excitation',
            'No initial/gap high impulse, delayed refractory impulse or repetition on held value',
            'Missingness clears detector history; resonator tail policy belongs to the renderer',
            'Sparse events only; no audio device, live routing, PCM or comparison level normalization']}
