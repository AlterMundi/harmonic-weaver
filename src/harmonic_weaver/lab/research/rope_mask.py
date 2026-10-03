"""Configurable RGB-distance candidates; never automatic rope labels."""
import math
import numpy as np
from scipy import ndimage
from pydantic import Field,model_validator
from ..contracts import Contract,Number


class Settings(Contract):
    target_rgb:list[Number]=Field(default_factory=lambda:[255,255,255],min_length=3,max_length=3)
    distance_rgb:Number=Field(default=40,ge=0,le=442)
    roi:list[Number]=Field(default_factory=lambda:[0,0,1,1],min_length=4,max_length=4)
    min_component_px:int=Field(default=8,ge=1,le=4_000_000)
    max_components:int=Field(default=32,ge=1,le=64)
    max_runs:int=Field(default=10000,ge=1,le=100000)

    @model_validator(mode='after')
    def valid(self):
        if any(not 0<=v<=255 for v in self.target_rgb):raise ValueError('RGB target requires 0–255')
        x0,y0,x1,y1=self.roi
        if not (0<=x0<x1<=1 and 0<=y0<y1<=1):raise ValueError('Normalized nonempty ROI required')
        return self


def propose(rgb,settings):
    settings=Settings.model_validate(settings);image=np.asarray(rgb)
    if image.ndim!=3 or image.shape[2]!=3 or image.dtype!=np.uint8 or not image.size or image.shape[0]*image.shape[1]>4_000_000:
        raise ValueError('RGB uint8 image within four-million-pixel budget required')
    height,width=image.shape[:2];x0,y0,x1,y1=settings.roi
    left,right=math.ceil(x0*width),math.ceil(x1*width);top,bottom=math.ceil(y0*height),math.ceil(y1*height)
    mask=np.zeros((height,width),dtype=bool)
    delta=image[top:bottom,left:right].astype(float)-np.array(settings.target_rgb)
    mask[top:bottom,left:right]=np.sum(delta*delta,axis=2)<=settings.distance_rgb**2
    labels,count=ndimage.label(mask) # Explicit 4-connectivity; no gap closing/interpolation.
    sizes=np.bincount(labels.ravel());chosen=sorted((i for i in range(1,count+1) if sizes[i]>=settings.min_component_px),key=lambda i:(-sizes[i],i))[:settings.max_components]
    components=[];run_count=0
    for ident in chosen:
        runs=[]
        for y in range(height):
            xs=np.flatnonzero(labels[y]==ident)
            if not len(xs):continue
            starts=np.r_[0,np.flatnonzero(np.diff(xs)>1)+1];stops=np.r_[starts[1:]-1,len(xs)-1]
            for a,b in zip(starts,stops):
                run_count+=1
                if run_count>settings.max_runs:raise ValueError('Candidate mask exceeds run budget; narrow ROI or threshold')
                runs.append([y,int(xs[a]),int(xs[b])+1])
        components.append({'component_id':ident,'area_px':int(sizes[ident]),'runs_y_x_start_x_stop_exclusive':runs})
    return {'schema_version':1,'line':'R08','method':'rgb_distance_4_connected_candidates','settings':settings.model_dump(),
            'width_px':width,'height_px':height,'candidate_components':components,
            'components_detected':count,'components_returned':len(components),
            'limits':['Color-distance image candidates are not rope, body or endpoint identification',
                      'No morphology bridges occlusion; four-connected regions may fragment rope',
                      'Size/quantity filtering omits candidates explicitly; never full-rope coverage',
                      'RGB Euclidean threshold depends on lighting/encoding; not calibrated physical color',
                      'Manual review required before accepting curves; masks are not polyline annotations']}
