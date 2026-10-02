"""R08 manual image-plane rope evidence, explicitly incomplete under occlusion."""
from typing import Literal
from pydantic import Field,model_validator,model_serializer
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
    endpoints:dict[Literal['a','b'],Point]=Field(default_factory=dict,max_length=2)

    @model_serializer(mode='wrap')
    def serialize(self,handler):
        data=handler(self)
        if not self.endpoints:data.pop('endpoints',None)
        return data

    @model_validator(mode='after')
    def valid(self):
        if self.state in ('absent','unidentifiable') and self.endpoints:raise ValueError('No invented endpoints for absent/unidentifiable rope')
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
    result={'schema_version':1,'line':'R08','annotation':annotation.model_dump(),'rows':rows,
            'limits':['Manual annotations, not automatically verified tracking or participant identity',
                      'Image-plane projected visible length, not physical rope length',
                      'Disconnected segments are never joined through occlusion',
                      'A 2D crossing does not identify depth order, knot or 3D topology',
                      'Source hash and clocks declared; media binding verification remains separate']}

    if any(f.endpoints for f in annotation.frames):
        endpoint_rows=[];previous={}
        for frame in annotation.frames:
            current={}
            for label,point in frame.endpoints.items():
                xy=np.array([point.x*annotation.width_px,point.y*annotation.height_px])
                old=previous.get(label)
                valid=old is not None and old[0]==frame.frame_index-1
                delta=(xy-old[2])/(frame.time_s-old[1]) if valid else None
                endpoint_rows.append({'frame_index':frame.frame_index,'time_s':frame.time_s,'label':label,
                    'x_px':float(xy[0]),'y_px':float(xy[1]),
                    'velocity_x_px_s':float(delta[0]) if valid else None,
                    'velocity_y_px_s':float(delta[1]) if valid else None,
                    'speed_px_s':float(np.linalg.norm(delta)) if valid else None,
                    'velocity_valid':valid,'cause':None if valid else 'no_consecutive_labeled_endpoint'})
                current[label]=(frame.frame_index,frame.time_s,xy)
            previous=current
        result['endpoints']={'rows':endpoint_rows,'limits':[
            'Endpoint a/b correspondence is declared manually, never inferred from position',
            'Only consecutive decoded frame indices with the same visible label yield velocity',
            'Gaps or missing labels reset support; image-plane px/s, not physical propagation speed']}
    return result
