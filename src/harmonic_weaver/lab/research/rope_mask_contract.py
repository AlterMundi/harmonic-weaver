"""Semantic bounds for stored R08 candidate runs; not source recomputation."""
import math
from typing import Literal
from pydantic import Field,model_validator
from ..contracts import Contract,Number
from .rope_mask import Settings


class Component(Contract):
    component_id:int=Field(ge=1)
    area_px:int=Field(ge=1,le=4_000_000)
    runs_y_x_start_x_stop_exclusive:list[list[int]]=Field(min_length=1,max_length=100000)


class Result(Contract):
    schema_version:Literal[1]
    line:Literal['R08']
    method:Literal['rgb_distance_4_connected_candidates']
    settings:Settings
    width_px:int=Field(ge=1,le=32768)
    height_px:int=Field(ge=1,le=32768)
    candidate_components:list[Component]=Field(max_length=64)
    components_detected:int=Field(ge=0,le=4_000_000)
    components_returned:int=Field(ge=0,le=64)
    media_sha256:str=Field(pattern='^[a-f0-9]{64}$')
    frame_index:int=Field(ge=0)
    time_s:Number=Field(ge=0)
    limits:list[str]=Field(max_length=64)

    @model_validator(mode='after')
    def validate_runs(self):
        if self.width_px*self.height_px>4_000_000:raise ValueError('Mask image budget exceeded')
        if self.components_returned!=len(self.candidate_components) or self.components_detected<self.components_returned or self.components_returned>self.settings.max_components:raise ValueError('Mask component inventory mismatch')
        identifiers=set();rows={};count=0;previous_rank=None
        x0,y0,x1,y1=self.settings.roi
        left,right=math.ceil(x0*self.width_px),math.ceil(x1*self.width_px)
        top,bottom=math.ceil(y0*self.height_px),math.ceil(y1*self.height_px)
        for component in self.candidate_components:
            rank=(-component.area_px,component.component_id)
            if component.component_id in identifiers or (previous_rank is not None and rank<=previous_rank):raise ValueError('Mask components must be unique and area-ranked')
            identifiers.add(component.component_id);previous_rank=rank
            area=0;previous=None
            for run in component.runs_y_x_start_x_stop_exclusive:
                if len(run)!=3:raise ValueError('Mask run requires y/start/stop')
                y,start,stop=run
                if not (top<=y<bottom and left<=start<stop<=right):raise ValueError('Mask run outside ROI/image')
                if previous is not None and (y,start)<=previous:raise ValueError('Mask runs require strict row order')
                previous=(y,start);area+=stop-start;rows.setdefault(y,[]).append((start,stop));count+=1
            if area!=component.area_px or area<self.settings.min_component_px:raise ValueError('Mask area differs from runs or filter')
        if count>self.settings.max_runs:raise ValueError('Mask run budget exceeded')
        for intervals in rows.values():
            ordered=sorted(intervals)
            if any(b[0]<a[1] for a,b in zip(ordered,ordered[1:])):raise ValueError('Mask runs overlap')
        return self
