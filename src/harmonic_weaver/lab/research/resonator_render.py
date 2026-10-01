"""Bounded-block R05 render on the frozen source clock, without audio devices."""
import math
from bisect import bisect_left
from typing import Literal
import numpy as np
from pydantic import Field
from ..contracts import Contract,Number
from .resonators import Resonators,Settings as ResonatorSettings
from .excitation import prepare


class Settings(Contract):
    block_size:int=Field(default=256,ge=16,le=8192)
    tail_s:Number=Field(default=.5,ge=0,le=10)
    missing_policy:Literal['ring','reset']='ring'


class Render:
    def __init__(self,document,resonators,excitation,settings=None):
        self.settings=Settings.model_validate(settings or {})
        self.resonators=ResonatorSettings.model_validate(resonators)
        self.excitation=prepare(document,excitation,sample_rate=self.resonators.sample_rate,voices=len(self.resonators.ratios))
        selection=self.excitation['selection'];sr=self.resonators.sample_rate
        self.segment_frames=math.ceil((selection['end_s']-selection['start_s'])*sr)
        self.tail_frames=math.ceil(self.settings.tail_s*sr)
        self.total_frames=self.segment_frames+self.tail_frames
        self.impulses={};excluded=0
        for event in self.excitation['events']:
            index=event['sample_index']
            if index>=self.segment_frames:excluded+=1;continue
            self.impulses.setdefault(index,np.zeros(len(self.resonators.ratios)))
            self.impulses[index]+=event['voice_impulses']
        self.resets=set()
        if self.settings.missing_policy=='reset':
            for reset in self.excitation['resets']:
                time=document['rows'][reset['index']]['time_s']
                index=math.ceil((time-selection['start_s'])*sr)
                if index<self.segment_frames:self.resets.add(index)
        self.impulse_indices=sorted(self.impulses);self.reset_indices=sorted(self.resets)
        self.manifest={'schema_version':1,'resonators':self.resonators.model_dump(),
            'render':self.settings.model_dump(),'excitation':self.excitation,
            'segment_frames':self.segment_frames,'tail_frames':self.tail_frames,'total_frames':self.total_frames,
            'excluded_events_at_crop_boundary':excluded,'reset_samples':sorted(self.resets),
            'limits':['Output is raw sum of model voices, no limiter or automatic level normalization',
                'Impulse precedes exact oscillator step; each output is the right edge of that sample step',
                'Tail includes autonomous model activity without new source observations',
                'Reset policy zeros oscillator state at observed invalid/gap detection time, not inferred physical onset',
                'Reset can be discontinuous; no click-free or perceptual equivalence claim',
                'Not the accepted Shaper synthesis; experimental renderer only']}

    def blocks(self):
        # Every traversal starts the same frozen run, no carried state across runs.
        model=Resonators(self.resonators);size=self.settings.block_size;n=len(self.resonators.ratios)
        for start in range(0,self.total_frames,size):
            end=min(start+size,self.total_frames)
            boundaries=sorted({start,end,*self.reset_indices[bisect_left(self.reset_indices,start):bisect_left(self.reset_indices,end)]})
            chunks=[]
            for a,b in zip(boundaries,boundaries[1:]):
                if a in self.resets:model.reset()
                impulses=np.zeros((b-a,n))
                for index in self.impulse_indices[bisect_left(self.impulse_indices,a):bisect_left(self.impulse_indices,b)]:
                    impulses[index-a]+=self.impulses[index]
                chunks.append(model.render(impulses))
            yield {'start_sample':start,'voices':np.concatenate([c['voices'] for c in chunks]),
                   'quadrature':np.concatenate([c['quadrature'] for c in chunks]),
                   'sum':np.concatenate([c['sum'] for c in chunks]),
                   'state_norm_squared':np.concatenate([c['state_norm_squared'] for c in chunks])}
