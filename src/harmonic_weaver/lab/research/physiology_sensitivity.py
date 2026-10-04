"""Declared R12 clock perturbations, with exact support intersection and no offset fitting."""
from typing import Literal
from pydantic import Field,model_validator
from ..contracts import Contract
from .physiology import Request as Measurements,calculate as summarize,observation_intervals


class Request(Contract):
    schema_version: Literal[1] = 1
    measurements: Measurements
    offset_deltas_s: list[float] = Field(min_length=2,max_length=9)

    @model_validator(mode='after')
    def budget(self):
        if len(set(self.offset_deltas_s)) != len(self.offset_deltas_s) or 0. not in self.offset_deltas_s:
            raise ValueError('Unique offset deltas including zero are required')
        if any(abs(delta)>60 for delta in self.offset_deltas_s):
            raise ValueError('Offset deltas must stay within +/-60 common-clock seconds')
        if len(self.measurements.samples)*len(self.measurements.trials)*len(self.offset_deltas_s)>2000000:
            raise ValueError('R12 sensitivity exceeds 2 million sample/trial/condition budget')
        return self


def intersect(a,b):
    output=[];i=j=0
    while i<len(a) and j<len(b):
        left,right=max(a[i][0],b[j][0]),min(a[i][1],b[j][1])
        if left<right:output.append((left,right))
        if a[i][1]<b[j][1]:i+=1
        else:j+=1
    return output


def observed_support(measurements):
    output=[]
    for start,end,channels in observation_intervals(measurements):
        if any(channels[key]['cause'] is not None for key in measurements.common_channel_ids):continue
        if output and output[-1][1]==start:output[-1]=(output[-1][0],end)
        else:output.append((start,end))
    return output


def calculate(request):
    frozen=Request.model_validate(request)
    variants=[];common=None
    for delta in frozen.offset_deltas_s:
        raw=frozen.measurements.model_dump()
        raw['clock']['offset_s']+=delta
        measurements=Measurements.model_validate(raw)
        support=observed_support(measurements)
        common=support if common is None else intersect(common,support)
        variants.append((delta,measurements))
    conditions=[]
    for delta,measurements in variants:
        native=summarize(measurements)
        paired=summarize(measurements,support=common)
        conditions.append({'offset_delta_s':delta,'effective_offset_s':measurements.clock.offset_s,
            'native_trials':native['trials'],'paired_trials':paired['trials']})
    return {'schema_version':1,'line':'R12','kind':'clock_sensitivity','request':frozen.model_dump(),
        'common_support_intervals_s':[list(pair) for pair in common],
        'conditions':conditions,'estimator':native['estimator'],
        'limits':['Offset deltas are declared perturbations, not estimated synchronization or latency',
            'Offsets are in common-clock seconds; rate, raw timestamps, trials, values and exclusions remain frozen',
            'Paired support intersects all offsets and selected channels; extra channels still require their own valid pairs',
            'Native and paired summaries differ in coverage; no preferred offset or physiological ranking is selected',
            'Linear/trapezoidal estimator operates only inside supported adjacent pairs, with no gap filling or extrapolation',
            'Clock uncertainty is not a probability distribution or an automatically chosen delta grid',
            'No inference of calories, efficiency, HIT, causal effects or human acceptance']}
