"""R08 manual image-plane rope evidence, explicitly incomplete under occlusion."""
from typing import Literal
from pydantic import Field,model_validator
import numpy as np
from ..contracts import Contract,Number


class Point(Contract):
    x:Number=Field(ge=0,le=1)
    y:Number=Field(ge=0,le=1)


class Frame(Contract):
    frame_index:int=Field(ge=0)
    time_s:Number=Field(ge=0)
    state:Literal['observed','partial','unidentifiable','absent']
    visible_segments:list[list[Point]]=Field(default_factory=list,max_length=64)
    causes:list[Literal['blur','occlusion','crossing_ambiguity','out_of_frame']]=Field(default_factory=list,max_length=4)
    note:str=Field(default='',max_length=2000)

    @model_validator(mode='after')
    def valid(self):
        if any(len(s)<2 or len(s)>4096 for s in self.visible_segments):raise ValueError('Each visible polyline requires 2–4096 points')
        if self.state in ('absent','unidentifiable') and self.visible_segments:raise ValueError('No invented curve for absent/unidentifiable rope')
        if self.state in ('observed','partial') and not self.visible_segments:raise ValueError('Observed/partial rope requires visible segments')
        if self.state=='observed' and (len(self.visible_segments)!=1 or self.causes):raise ValueError('Full observation requires one unambiguous visible curve')
        if self.state in ('partial','unidentifiable') and not self.causes:raise ValueError('Incompleteness requires a declared cause')
        if len(set(self.causes))!=len(self.causes):raise ValueError('Duplicate quality causes')
        if sum(len(s) for s in self.visible_segments)>8192:raise ValueError('Frame exceeds point budget')
        return self


class Annotation(Contract):
    schema_version:Literal[1]=1
    media_sha256:str=Field(pattern='^[a-f0-9]{64}$')
    width_px:int=Field(ge=1,le=32768)
    height_px:int=Field(ge=1,le=32768)
    method:Literal['manual']='manual'
    coordinate_frame:Literal['image_normalized']='image_normalized'
    frames:list[Frame]=Field(default_factory=list,max_length=14400)

    @model_validator(mode='after')
    def valid(self):
        if any(b.frame_index<=a.frame_index or b.time_s<=a.time_s for a,b in zip(self.frames,self.frames[1:])):raise ValueError('Strictly increasing frame and source-time clocks required')
        if sum(len(s) for f in self.frames for s in f.visible_segments)>144000:raise ValueError('Annotation exceeds point budget')
        return self


def report(annotation):
    annotation=Annotation.model_validate(annotation)
    rows=[]
    for frame in annotation.frames:
        length=0.
        for segment in frame.visible_segments:
            points=np.array([[p.x*annotation.width_px,p.y*annotation.height_px] for p in segment])
            length+=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum())
        rows.append({'frame_index':frame.frame_index,'time_s':frame.time_s,'state':frame.state,
                     'visible_projected_length_px':length if frame.visible_segments else None,
                     'causes':frame.causes})
    return {'schema_version':1,'line':'R08','annotation':annotation.model_dump(),'rows':rows,
            'limits':['Manual annotations, not automatically verified tracking or participant identity',
                      'Image-plane projected visible length, not physical rope length',
                      'Disconnected segments are never joined through occlusion',
                      'A 2D crossing does not identify depth order, knot or 3D topology',
                      'Source hash and clocks declared; media binding verification remains separate']}
