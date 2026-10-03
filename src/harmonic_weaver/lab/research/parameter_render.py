"""Experimental causal amplitude/optional frequency mapping, not accepted Shaper."""
import math
import numpy as np
from pydantic import Field,model_validator
from ..contracts import Contract,Number
from .candidate_input import CandidateRequest
from .event_candidates import extract_candidates
from .resonators import Settings as CarrierSettings
from .resonator_render import Settings as RenderSettings


class FrequencyModulation(Contract):
    depth:Number=Field(default=.25,ge=0,lt=1)
    smoothing_s:Number=Field(default=.1,ge=0,le=10)


def validate_frequency(carriers,mapping):
    option=mapping.frequency_modulation
    if option is not None and carriers.fundamental_hz*max(carriers.ratios)*(1+option.depth)>=carriers.sample_rate/2:
        raise ValueError('Modulated carriers must remain below Nyquist')


class Settings(Contract):
    frequency_modulation:FrequencyModulation|None=None
    reference_scale:Number=Field(default=1,gt=0,le=1000000)
    gain:Number=Field(default=1,ge=0,le=10)
    max_amplitude:Number=Field(default=1,gt=0,le=10)
    attack_s:Number=Field(default=.02,ge=0,le=10)
    release_s:Number=Field(default=.08,ge=0,le=10)
    max_hold_s:Number=Field(default=.1,gt=0,le=5)
    voice_weights:list[Number]=Field(default_factory=lambda:[1/6]*6,min_length=6,max_length=32)

    @model_validator(mode='after')
    def weights(self):
        if any(v<0 or v>10 for v in self.voice_weights):
            raise ValueError('Voice weights in 0–10 required')
        return self


class Render:
    def __init__(self,document,carriers,mapping,render=None):
        self.carriers=CarrierSettings.model_validate(carriers)
        self.mapping=Settings.model_validate(mapping)
        validate_frequency(self.carriers,self.mapping)
        self.render=RenderSettings.model_validate(render or {})
        self.selection=CandidateRequest.model_validate(document['request'])
        if self.carriers.coupling_per_s!=0 or self.carriers.topology!='isolated':
            raise ValueError('Amplitude mapping requires isolated uncoupled carriers')
        if len(self.mapping.voice_weights)!=len(self.carriers.ratios):
            raise ValueError('One mapping weight per carrier required')
        if not isinstance(document.get('unit'),str) or not document['unit']:
            raise ValueError('Explicit input unit required')
        rows=document['rows']
        extract_candidates(rows,high=self.selection.high,low=self.selection.low,
            refractory_s=self.selection.refractory_s,max_gap_s=self.selection.max_gap_s)
        if any(not self.selection.start_s<=r['time_s']<self.selection.end_s for r in rows):
            raise ValueError('Mapping observations outside segment')
        sr=self.carriers.sample_rate
        self.segment_frames=math.ceil((self.selection.end_s-self.selection.start_s)*sr)
        self.total_frames=self.segment_frames+math.ceil(self.render.tail_s*sr)
        self.targets={0:0.,self.segment_frames:0.}
        self.frequency_targets={0:0.,self.segment_frames:0.}
        for index,row in enumerate(rows):
            start=math.ceil((row['time_s']-self.selection.start_s)*sr)
            if start>=self.segment_frames:continue
            observed=row.get('valid',True) is True and type(row.get('value')) in (int,float) and math.isfinite(row['value'])
            amplitude=min(self.mapping.max_amplitude,self.mapping.gain*max(0.,row['value'])/self.mapping.reference_scale) if observed else 0.
            self.targets[start]=amplitude
            self.frequency_targets[start]=max(-1.,min(1.,row['value']/self.mapping.reference_scale)) if observed else 0.
            if observed:
                stop=min(self.selection.end_s,row['time_s']+self.mapping.max_hold_s,
                         rows[index+1]['time_s'] if index+1<len(rows) else self.selection.end_s)
                expiry=min(self.segment_frames,math.ceil((stop-self.selection.start_s)*sr))
                self.targets[expiry]=0.
                self.frequency_targets[expiry]=0.
        self.indices=sorted(self.targets)
        self.manifest={'schema_version':1,'mechanism':'positive_amplitude_mapping',
            'carriers':self.carriers.model_dump(),'mapping':self.mapping.model_dump(exclude_none=True),
            'render':self.render.model_dump(),'selection':self.selection.model_dump(),
            'input_unit':document['unit'],'segment_frames':self.segment_frames,'total_frames':self.total_frames,
            'target_updates':[{'sample_index':i,'amplitude':self.targets[i]} for i in self.indices],
            'limits':['Not accepted Shaper synthesis; experimental amplitude-mapping comparison arm',
                'Negative input maps to zero; mapping scale declared in input units, not fitted',
                'Observed value held causally until next observation or max_hold_s, then released',
                'Missing input releases amplitude; no interpolation or phase reset',
                'Envelope uses one-pole attack/release; tail is instrument activity, not observed body',
                'Carrier phase uses elapsed sample clock, not measured body phase',
                'Carrier damping_per_s and render missing_policy unused in this mechanism',
                'Raw sum of all carriers, no automatic normalization or limiter']}

        if self.mapping.frequency_modulation is not None:
            self.manifest['limits'].remove('Carrier phase uses elapsed sample clock, not measured body phase')
            self.manifest['frequency_target_updates']=[{'sample_index':i,'normalized':self.frequency_targets[i]} for i in sorted(self.frequency_targets)]
            self.manifest['limits']+=['Optional common frequency multiplier 1+depth*smoothed normalized input; instantaneous carrier ratios preserved',
                'Frequency target clips signed input/reference_scale to [-1,1]; expiry/missing returns toward base carrier',
                'Phase accumulated causally without resets; not measured body phase or audification']

    def blocks(self):
        sr=self.carriers.sample_rate;weights=np.array(self.mapping.voice_weights)
        frequencies=self.carriers.fundamental_hz*np.array(self.carriers.ratios)
        attack=1. if self.mapping.attack_s==0 else -math.expm1(-1/(sr*self.mapping.attack_s))
        release=1. if self.mapping.release_s==0 else -math.expm1(-1/(sr*self.mapping.release_s))
        amplitude=target=0.
        modulation=self.mapping.frequency_modulation
        smooth=1. if modulation is None or modulation.smoothing_s==0 else -math.expm1(-1/(sr*modulation.smoothing_s))
        normalized=frequency_target=cycles=0.
        for start in range(0,self.total_frames,self.render.block_size):
            end=min(start+self.render.block_size,self.total_frames)
            envelope=np.empty(end-start)
            phases=np.empty(end-start) if modulation is not None else None
            for i in range(start,end):
                if i in self.targets:target=self.targets[i]
                amplitude+=(attack if target>amplitude else release)*(target-amplitude)
                envelope[i-start]=amplitude
                if modulation is not None:
                    if i in self.frequency_targets:frequency_target=self.frequency_targets[i]
                    normalized+=smooth*(frequency_target-normalized)
                    cycles+=self.carriers.fundamental_hz/sr*(1+modulation.depth*normalized)
                    phases[i-start]=2*np.pi*cycles
            time=(np.arange(start,end,dtype=float)+1)/sr
            angles=2*np.pi*time[:,None]*frequencies if phases is None else phases[:,None]*np.array(self.carriers.ratios)
            voices=np.sin(angles)*envelope[:,None]*weights
            quadrature=np.cos(angles)*envelope[:,None]*weights
            yield {'start_sample':start,'voices':voices,'quadrature':quadrature,'sum':voices.sum(axis=1),'amplitude':envelope}
