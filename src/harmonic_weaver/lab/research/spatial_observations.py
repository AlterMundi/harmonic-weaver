"""Explicit spatial observations and affine clocks; no inferred metric scale."""
from typing import Literal
from pydantic import Field,model_validator
from ..contracts import Contract


class Clock(Contract):
    source_clock:str=Field(min_length=1,max_length=80)
    common_clock:str=Field(min_length=1,max_length=80)
    offset_s:float
    rate:float=Field(gt=0,le=2)
    uncertainty_s:float=Field(ge=0)
    method:Literal['shared_hardware','measured_sync','declared_assumption']
    evidence_id:str|None=Field(default=None,min_length=1,max_length=160)

    @model_validator(mode='after')
    def evidence(self):
        if self.method!='declared_assumption' and self.evidence_id is None:
            raise ValueError('Measured synchronization requires evidence')
        return self

    def common_time(self,time_s):
        return self.offset_s+self.rate*time_s


class Point(Contract):
    label:str=Field(min_length=1,max_length=80)
    state:Literal['observed','inferred','held','missing']
    position:list[float]|None=None
    confidence:float|None=Field(default=None,ge=0,le=1)
    cause:str|None=Field(default=None,min_length=1,max_length=160)

    @model_validator(mode='after')
    def presence(self):
        if self.state=='missing':
            if self.position is not None or self.confidence is not None or self.cause is None:
                raise ValueError('Missing points require cause and no coordinates/confidence')
        elif self.position is None or self.cause is not None:
            raise ValueError('Supported points require coordinates, not missing cause')
        return self


class Stream(Contract):
    schema_version:Literal[1]=1
    line:Literal['R09']='R09'
    source_id:str=Field(min_length=1,max_length=80)
    subject_slot:str=Field(min_length=1,max_length=80)
    provider:Literal['image_pose','monocular_3d','calibrated_multiview','external_3d']
    dimensions:Literal[2,3]
    coordinate_frame:str=Field(min_length=1,max_length=80)
    units:Literal['image_normalized','frame_height','model_units','metres']
    calibration_id:str|None=Field(default=None,min_length=1,max_length=160)
    clock:Clock
    frames:list['Frame']=Field(min_length=1,max_length=14400)

    @model_validator(mode='after')
    def semantics(self):
        if self.provider=='image_pose' and (self.dimensions!=2 or self.units not in ('image_normalized','frame_height')):
            raise ValueError('Image pose requires explicit image-plane 2D units')
        if self.provider!='image_pose' and self.dimensions!=3:
            raise ValueError('Spatial providers require explicit 3D coordinates')
        if (self.units=='metres' or self.provider=='calibrated_multiview') and self.calibration_id is None:
            raise ValueError('Metric scale/multiview requires explicit calibration provenance')
        if self.dimensions==3 and self.units in ('image_normalized','frame_height'):raise ValueError('Image units do not establish depth')
        previous=None
        for frame in self.frames:
            if previous and (frame.index<=previous.index or frame.source_time_s<=previous.source_time_s):
                raise ValueError('Spatial frames require increasing source indices/times')
            previous=frame
            for point in frame.points:
                if point.position is not None and len(point.position)!=self.dimensions:raise ValueError('Coordinate dimension mismatch')
                if self.units=='image_normalized' and point.position is not None and any(x<0 or x>1 for x in point.position):raise ValueError('Image coordinates outside normalized domain')
                if self.provider=='monocular_3d' and point.state in ('observed','held'):raise ValueError('Monocular depth must remain inferred')
        return self


class Frame(Contract):
    index:int=Field(ge=0)
    source_time_s:float=Field(ge=0)
    points:list[Point]=Field(max_length=4096)

    @model_validator(mode='after')
    def unique(self):
        if len({p.label for p in self.points})!=len(self.points):raise ValueError('Duplicate spatial point labels')
        return self


Stream.model_rebuild()
