"""Causal, explicitly seeded image-point candidates; not physical rope identity."""
import cv2
import numpy as np
from pydantic import Field
from ..contracts import Contract, Number
from .rope_annotations import Point


class Settings(Contract):
    window_px:int=Field(default=21,ge=3,le=61)
    pyramid_levels:int=Field(default=3,ge=0,le=5)
    iterations:int=Field(default=30,ge=1,le=100)
    epsilon:Number=Field(default=.01,gt=0,le=1)
    min_eigenvalue:Number=Field(default=.0001,gt=0,le=1)
    max_forward_backward_error_px:Number=Field(default=1,gt=0,le=20)
    max_displacement_px:Number=Field(default=100,gt=0,le=4096)
    max_gap_s:Number=Field(default=.2,gt=0,le=10)
    max_points:int=Field(default=128,ge=1,le=4096)


class RopeFlow:
    """Each point keeps its seed index; rejected points never silently revive."""
    def __init__(self,settings=None):
        self.settings=Settings.model_validate(settings or {})
        self.reset()

    def reset(self):
        self.previous=None
        self.clock=None
        self.points={}

    def feed(self,image,frame_index,time_s,*,seeds=None):
        # Validate before mutation, including clocks and bounded decoded buffers.
        if not isinstance(image,np.ndarray) or image.dtype!=np.uint8 or image.ndim!=2:
            raise ValueError('Decoded uint8 grayscale image required')
        height,width=image.shape
        if min(height,width)<2 or height*width>4_000_000:raise ValueError('Image exceeds flow dimensions/budget')
        if type(frame_index)!=int or frame_index<0 or isinstance(time_s,bool) or not isinstance(time_s,(int,float)) or not np.isfinite(time_s) or time_s<0:
            raise ValueError('Finite nonnegative decoded frame clock required')
        parsed=None
        if seeds is not None:
            if not isinstance(seeds,list) or not 1<=len(seeds)<=self.settings.max_points:raise ValueError('Explicit seeds exceed point budget')
            parsed=[Point.model_validate(p) for p in seeds]
        gap=self.clock is not None and (frame_index!=self.clock[0]+1 or time_s<=self.clock[1] or time_s-self.clock[1]>self.settings.max_gap_s or image.shape!=self.previous.shape)
        if parsed is not None:
            self.points={i:np.array([min(p.x*width,width-1),min(p.y*height,height-1)],dtype=np.float32) for i,p in enumerate(parsed)}
            rows=[self._row(i,p,width,height,'seeded',None) for i,p in self.points.items()]
            status='seeded'
        elif gap:
            rows=[self._row(i,None,width,height,'unsupported','source_gap_or_dimensions_changed') for i in self.points]
            self.points={};status='reset'
        elif not self.points:
            rows=[];status='needs_explicit_seeds'
        else:
            ids=list(self.points)
            old=np.array([self.points[i] for i in ids],dtype=np.float32).reshape(-1,1,2)
            s=self.settings
            options={'winSize':(s.window_px,s.window_px),'maxLevel':s.pyramid_levels,
                     'criteria':(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,s.iterations,s.epsilon),
                     'minEigThreshold':s.min_eigenvalue}
            new,forward,_=cv2.calcOpticalFlowPyrLK(self.previous,image,old,None,**options)
            back,backward,_=cv2.calcOpticalFlowPyrLK(image,self.previous,new,None,**options)
            kept={};rows=[]
            for j,i in enumerate(ids):
                p=new[j,0];error=float(np.linalg.norm(back[j,0]-old[j,0]))
                displacement=float(np.linalg.norm(p-old[j,0]))
                cause=('optical_flow_failed' if not forward[j,0] or not backward[j,0] else
                       'nonfinite_flow' if not np.isfinite(p).all() or not np.isfinite(error) else
                       'outside_image' if not (0<=p[0]<=width-1 and 0<=p[1]<=height-1) else
                       'forward_backward_error' if error>s.max_forward_backward_error_px else
                       'displacement_limit' if displacement>s.max_displacement_px else None)
                if cause is None:kept[i]=p.copy()
                row=self._row(i,p if cause is None else None,width,height,'candidate' if cause is None else 'unsupported',cause)
                # Diagnostics are not confidence probabilities and may be unavailable.
                row['forward_backward_error_px']=error if np.isfinite(error) else None
                row['displacement_px']=displacement if np.isfinite(displacement) else None
                rows.append(row)
            self.points=kept;status='candidates' if kept else 'lost'
        self.previous=image.copy();self.clock=(frame_index,float(time_s))
        return {'schema_version':1,'line':'R08','frame_index':frame_index,'time_s':float(time_s),
                'status':status,'rows':rows,'settings':self.settings.model_dump(),
                'limits':['Seed indices are image-point correspondence, not physical endpoint identity',
                          'Normalized coordinates scale by image width/height; seeds at the far edge clamp to the last pixel',
                          'Flow candidates are not rope segmentation or calibrated uncertainty',
                          'No gap interpolation, reseeding, curve joining or inferred tension propagation']}

    @staticmethod
    def _row(index,point,width,height,state,cause):
        return {'seed_index':index,'state':state,'cause':cause,
                'point':{'x':float(point[0]/width),'y':float(point[1]/height)} if point is not None else None}
