"""Offline two-camera DLT; explicitly paired undistorted pixels, declared calibration."""
import math
from typing import Literal
import numpy as np
from pydantic import Field, model_validator
from ..contracts import Contract
from .spatial_observations import Clock, Point, Stream


class Camera(Contract):
    id: str = Field(min_length=1, max_length=80)
    intrinsics: list[list[float]]
    world_to_camera_rotation: list[list[float]]
    world_to_camera_translation_m: list[float]

    @model_validator(mode='after')
    def matrices(self):
        k=np.asarray(self.intrinsics);r=np.asarray(self.world_to_camera_rotation)
        if k.shape!=(3,3) or r.shape!=(3,3) or len(self.world_to_camera_translation_m)!=3:
            raise ValueError('Camera requires 3x3 K/R and translation in metres with three coordinates')
        if np.max(np.abs(k))>1e9 or np.max(np.abs(self.world_to_camera_translation_m))>1e6:
            raise ValueError('Bounded intrinsics (1e9) and translation metres (1e6) required')
        if not np.allclose(k[2],[0,0,1],atol=1e-10,rtol=0) or abs(k[1,0])>1e-10 or k[0,0]<=0 or k[1,1]<=0:
            raise ValueError('Pinhole intrinsics require positive focal lengths and canonical bottom row')
        if not np.allclose(r@r.T,np.eye(3),atol=1e-8,rtol=0) or abs(np.linalg.det(r)-1)>1e-8:
            raise ValueError('World-to-camera R must be a proper orthonormal rotation')
        return self

    def projection(self):
        return np.asarray(self.intrinsics)@np.column_stack([self.world_to_camera_rotation,self.world_to_camera_translation_m])

    def center(self):
        return -np.asarray(self.world_to_camera_rotation).T@self.world_to_camera_translation_m


class Settings(Contract):
    max_time_difference_s: float = Field(default=.01, ge=0, le=1)
    max_clock_uncertainty_s: float = Field(default=.01, ge=0, le=1)
    min_ray_angle_deg: float = Field(default=1, gt=0, le=90)
    max_reprojection_error_px: float = Field(default=2, gt=0, le=100)


class Pair(Contract):
    index: int = Field(ge=0)
    left_time_s: float = Field(ge=0)
    right_time_s: float = Field(ge=0)
    left: list[Point] = Field(max_length=64)
    right: list[Point] = Field(max_length=64)

    @model_validator(mode='after')
    def points(self):
        for points in (self.left,self.right):
            if len({p.label for p in points})!=len(points):raise ValueError('Duplicate point label in camera view')
            if any(p.position is not None and (len(p.position)!=2 or max(abs(x) for x in p.position)>1e9) for p in points):raise ValueError('Two undistorted pixel coordinates required')
        return self


class Request(Contract):
    schema_version: Literal[1] = 1
    source_id: str = Field(min_length=1,max_length=80)
    subject_slot: str = Field(min_length=1,max_length=80)
    coordinate_frame: str = Field(min_length=1,max_length=80)
    calibration_id: str = Field(min_length=1,max_length=160)
    calibration_kind: Literal['synthetic','declared_import']
    calibration_evidence: str = Field(min_length=1,max_length=240)
    image_coordinates: Literal['undistorted_pixels']
    left_camera: Camera
    right_camera: Camera
    left_clock: Clock
    right_clock: Clock
    labels: list[str] = Field(min_length=1,max_length=64)
    frames: list[Pair] = Field(min_length=1,max_length=14400)
    settings: Settings = Field(default_factory=Settings)

    @model_validator(mode='after')
    def pairing(self):
        if self.left_camera.id==self.right_camera.id:raise ValueError('Distinct camera IDs required')
        if np.linalg.norm(self.left_camera.center()-self.right_camera.center())<1e-9:raise ValueError('Nonzero declared camera baseline required')
        if self.left_clock.common_clock!=self.right_clock.common_clock:raise ValueError('Both views must declare the same common clock')
        if len(self.frames)*len(self.labels)>48000:raise ValueError('Maximum 48000 selected point pairs per request')
        if len(set(self.labels))!=len(self.labels) or any(not 1<=len(label)<=80 for label in self.labels):raise ValueError('Unique bounded selected labels required')
        previous=None
        for frame in self.frames:
            if previous and (frame.index<=previous.index or frame.left_time_s<=previous.left_time_s or frame.right_time_s<=previous.right_time_s):raise ValueError('Paired indices and both source clocks must increase')
            common=(self.left_clock.common_time(frame.left_time_s)+self.right_clock.common_time(frame.right_time_s))/2
            if not math.isfinite(common) or common<0:raise ValueError('Finite nonnegative paired common time required')
            previous=frame
        return self


def calculate(request):
    request=Request.model_validate(request)
    cameras=[request.left_camera,request.right_camera]
    projections=[c.projection() for c in cameras]
    centers=[c.center() for c in cameras]
    frames=[];diagnostics=[]
    clock_uncertainty=request.left_clock.uncertainty_s+request.right_clock.uncertainty_s
    maximum_uncertainty=0
    for frame in request.frames:
        times=[request.left_clock.common_time(frame.left_time_s),request.right_clock.common_time(frame.right_time_s)]
        dt=abs(times[0]-times[1]);mean=sum(times)/2
        if not math.isfinite(dt) or not math.isfinite(clock_uncertainty):raise ValueError('Finite clock difference/uncertainty required')
        maximum_uncertainty=max(maximum_uncertainty,(dt+clock_uncertainty)/2)
        views=[{p.label:p for p in points} for points in (frame.left,frame.right)]
        points=[]
        for label in request.labels:
            row={'index':frame.index,'label':label,'common_time_difference_s':dt,'ray_angle_deg':None,'reprojection_error_px':None}
            cause=None;position=None
            observations=[view.get(label) for view in views]
            row['input_states']=[p.state if p else 'absent' for p in observations]
            row['input_causes']=[p.cause if p else 'absent_label' for p in observations]
            if dt>request.settings.max_time_difference_s:cause='paired_time_difference'
            elif clock_uncertainty>request.settings.max_clock_uncertainty_s:cause='declared_clock_uncertainty'
            elif any(p is None or p.state!='observed' for p in observations):cause='requires_two_observed_pixels'
            else:
                a=np.stack([coordinate*projection[2]-projection[i] for observation,projection in zip(observations,projections) for i,coordinate in enumerate(observation.position)])
                _,_,v=np.linalg.svd(a)
                h=v[-1]
                if abs(h[3])<1e-12:cause='point_at_infinity_or_degenerate'
                else:
                    x=h[:3]/h[3]
                    depths=[(np.asarray(c.world_to_camera_rotation)@x+np.asarray(c.world_to_camera_translation_m))[2] for c in cameras]
                    if not np.all(np.isfinite(x)):cause='nonfinite_reconstruction'
                    elif min(depths)<=1e-9:cause='behind_or_on_camera_plane'
                    else:
                        rays=[x-center for center in centers]
                        cosine=float(np.dot(*rays)/(np.linalg.norm(rays[0])*np.linalg.norm(rays[1])))
                        angle=math.degrees(math.acos(min(1,max(-1,abs(cosine)))))
                        row['ray_angle_deg']=angle
                        errors=[]
                        for projection,observation in zip(projections,observations):
                            projected=projection@np.append(x,1)
                            errors.append(float(np.linalg.norm(projected[:2]/projected[2]-observation.position)))
                        row['reprojection_error_px']=errors
                        if angle<request.settings.min_ray_angle_deg:cause='insufficient_parallax'
                        elif max(errors)>request.settings.max_reprojection_error_px:cause='reprojection_error'
                        else:position=x.tolist()
            row['cause']=cause;diagnostics.append(row)
            points.append({'label':label,'state':'missing' if cause else 'inferred','position':position,'cause':cause})
        frames.append({'index':frame.index,'source_time_s':mean,'points':points})
    stream=Stream.model_validate({'source_id':request.source_id,'subject_slot':request.subject_slot,
        'provider':'calibrated_multiview','dimensions':3,'coordinate_frame':request.coordinate_frame,
        'units':'metres','calibration_id':request.calibration_id,'frames':frames,
        'clock':{'source_clock':'multiview_paired_common','common_clock':request.left_clock.common_clock,
                 'offset_s':0,'rate':1,'uncertainty_s':maximum_uncertainty,'method':'declared_assumption'}})
    result={'schema_version':1,'line':'R09','input_kind':'paired_multiview_dlt','request':request.model_dump(),
        'stream':stream.model_dump(),'common_times_s':[f.source_time_s for f in stream.frames],
        'coverage':{state:sum(p.state==state for f in stream.frames for p in f.points) for state in ('observed','held','inferred','missing')},
        'diagnostics':diagnostics,'limits':[
            'Offline paired reconstruction; correspondences, calibration/scale and clocks are caller-declared, not authenticated',
            'Undistorted pinhole pixels only; no lens correction, matching, resampling or monocular depth inference',
            'Output time is the mean of paired common times; source times and clocks remain in request; no causal availability asserted',
            'All reconstructed points are inferred; low reprojection error does not establish physical depth accuracy',
            'Clock uncertainty is derived from declarations and pair separation, not a measured synchronization bound']}
    Contract.finite_tree(result)
    return result


def synthetic_request():
    clock={'source_clock':'synthetic_source','common_clock':'synthetic_common','offset_s':0,'rate':1,'uncertainty_s':0,'method':'declared_assumption'}
    left={'id':'synthetic-left','intrinsics':[[500,0,320],[0,500,240],[0,0,1]],'world_to_camera_rotation':np.eye(3).tolist(),'world_to_camera_translation_m':[0,0,0]}
    import copy
    right={**copy.deepcopy(left),'id':'synthetic-right','world_to_camera_translation_m':[-1,0,0]}
    frames=[]
    for i in range(5):
        x=np.array([i*.02,.2,4+i*.05,1]);views=[]
        for camera in (left,right):
            pixels=Camera.model_validate(camera).projection()@x
            views.append([{'label':'marker','state':'observed','position':(pixels[:2]/pixels[2]).tolist()}])
        frames.append({'index':i,'left_time_s':i*.1,'right_time_s':i*.1,'left':views[0],'right':views[1]})
    return {'source_id':'synthetic-multiview','subject_slot':'synthetic-slot','coordinate_frame':'synthetic-world',
        'calibration_id':'synthetic-baseline-1m','calibration_kind':'synthetic','calibration_evidence':'Known generated cameras, not hardware',
        'image_coordinates':'undistorted_pixels','left_camera':left,'right_camera':right,'left_clock':dict(clock),'right_clock':dict(clock),
        'labels':['marker'],'frames':frames,'settings':Settings().model_dump()}


if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    request=synthetic_request();result=calculate(request)
    with args.output.open('x') as output:json.dump(result,output,indent=2,allow_nan=False)
