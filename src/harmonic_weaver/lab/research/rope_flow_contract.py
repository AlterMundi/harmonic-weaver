"""Structural temporal support validation, not optical accuracy verification."""
from typing import Literal
from pydantic import Field,model_validator
from ..contracts import Contract,Number
from .rope_annotations import Point
from .rope_flow import Settings


class Row(Contract):
    seed_index:int=Field(ge=0,le=4095)
    state:Literal['seeded','candidate','unsupported']
    cause:Literal['source_gap_or_dimensions_changed','optical_flow_failed','nonfinite_flow',
                  'outside_image','forward_backward_error','displacement_limit']|None
    point:Point|None
    forward_backward_error_px:Number|None=Field(default=None,ge=0)
    displacement_px:Number|None=Field(default=None,ge=0)

    @model_validator(mode='after')
    def valid(self):
        if self.state=='unsupported':
            if self.point is not None or self.cause is None:raise ValueError('Unsupported flow row requires cause and no invented point')
        elif self.point is None or self.cause is not None:raise ValueError('Supported flow row requires point and no invalidity cause')
        return self


class Frame(Contract):
    schema_version:Literal[1]
    line:Literal['R08']
    frame_index:int=Field(ge=0)
    time_s:Number=Field(ge=0)
    status:Literal['seeded','reset','needs_explicit_seeds','candidates','lost']
    rows:list[Row]=Field(max_length=4096)
    settings:Settings
    limits:list[str]=Field(max_length=16)

    @model_validator(mode='after')
    def valid(self):
        ids=[r.seed_index for r in self.rows]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate flow seed index')
        if self.status=='seeded' and (not self.rows or any(r.state!='seeded' for r in self.rows)):raise ValueError('Seeded frame requires explicit seeds')
        if self.status=='candidates' and (not any(r.state=='candidate' for r in self.rows) or any(r.state=='seeded' for r in self.rows)):raise ValueError('Candidate frame requires surviving candidates')
        if self.status in ('lost','reset') and any(r.state!='unsupported' for r in self.rows):raise ValueError('Lost/reset frame cannot retain points')
        if self.status=='lost' and not self.rows:raise ValueError('Lost frame requires rejected point evidence')
        if self.status=='reset' and any(r.cause!='source_gap_or_dimensions_changed' for r in self.rows):raise ValueError('Reset requires gap cause')
        if self.status=='needs_explicit_seeds' and self.rows:raise ValueError('Unseeded frame cannot invent correspondence')
        for row in self.rows:
            if row.state=='candidate' and (row.forward_backward_error_px is None or row.displacement_px is None or row.forward_backward_error_px>self.settings.max_forward_backward_error_px or row.displacement_px>self.settings.max_displacement_px):raise ValueError('Candidate diagnostics must meet effective flow limits')
        return self


def validate_frames(frames,request):
    if not isinstance(frames,list) or len(frames)!=len(request.frame_times_s):raise ValueError('Flow frame inventory mismatch')
    previous=set(range(len(request.seeds)))
    for offset,raw in enumerate(frames):
        frame=Frame.model_validate(raw)
        if frame.frame_index!=request.start_frame_index+offset or frame.time_s!=request.frame_times_s[offset] or frame.settings!=request.settings:raise ValueError('Flow frame clock/settings mismatch')
        ids={r.seed_index for r in frame.rows}
        if any(r.point is not None and (r.point.x>(request.width_px-1)/request.width_px+1e-7 or r.point.y>(request.height_px-1)/request.height_px+1e-7) for r in frame.rows):raise ValueError('Flow point outside decoded pixel bounds')
        if ids!=previous:raise ValueError('Flow seed correspondence missing or revived without explicit reseeding')
        if (offset==0)!=(frame.status=='seeded'):raise ValueError('Only initial frame can seed this run')
        if offset and ((frame.time_s-request.frame_times_s[offset-1]>request.settings.max_gap_s)!=(frame.status=='reset')):raise ValueError('Flow reset must match source-time gap')
        if offset==0:
            for row in frame.rows:
                seed=request.seeds[row.seed_index]
                x=min(seed.x*request.width_px,request.width_px-1)/request.width_px
                y=min(seed.y*request.height_px,request.height_px-1)/request.height_px
                if abs(row.point.x-x)>1e-6 or abs(row.point.y-y)>1e-6:raise ValueError('Initial flow point differs from declared seed')
        previous={r.seed_index for r in frame.rows if r.point is not None}
