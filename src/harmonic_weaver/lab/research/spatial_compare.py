"""Causal clock-aligned comparison; no implicit calibration or best-fit alignment."""
from bisect import bisect_right
from math import dist
from pydantic import Field,model_validator
from ..contracts import Contract
from .spatial_observations import Stream


class Settings(Contract):
    labels:list[str]=Field(min_length=1,max_length=4096)
    max_age_s:float=Field(default=.05,ge=0,le=10)
    max_combined_clock_uncertainty_s:float=Field(default=.02,ge=0,le=10)
    allow_inferred:bool=False
    allow_held:bool=False

class Request(Settings):
    reference:Stream
    candidate:Stream

    @model_validator(mode='after')
    def compatible(self):
        a,b=self.reference,self.candidate
        if (a.dimensions,a.units,a.coordinate_frame)!=(b.dimensions,b.units,b.coordinate_frame):
            raise ValueError('Compare only equal dimensions, units and coordinate frame')
        if a.clock.common_clock!=b.clock.common_clock:raise ValueError('Streams require the same declared common clock')
        if len(set(self.labels))!=len(self.labels) or any(not label or len(label)>80 for label in self.labels):raise ValueError('Unique explicit point labels required')
        return self


def compare(request):
    request=Request.model_validate(request);a,b=request.reference,request.candidate
    times=[b.clock.common_time(f.source_time_s) for f in b.frames]
    Contract.finite_tree(times)
    uncertainty=a.clock.uncertainty_s+b.clock.uncertainty_s
    allowed={'observed'}|({'inferred'} if request.allow_inferred else set())|({'held'} if request.allow_held else set())
    rows=[];errors=[];eligible=0
    for frame in a.frames:
        time=a.clock.common_time(frame.source_time_s);Contract.finite_tree(time)
        index=bisect_right(times,time)-1
        age=time-times[index] if index>=0 else None
        reference={p.label:p for p in frame.points}
        candidate={p.label:p for p in b.frames[index].points} if index>=0 else {}
        for label in request.labels:
            ref=reference.get(label);point=candidate.get(label)
            is_eligible=ref is not None and ref.state in allowed and ref.position is not None
            if is_eligible:eligible+=1
            cause=('reference_not_supported' if not is_eligible else
                   'clock_uncertainty_exceeds_limit' if uncertainty>request.max_combined_clock_uncertainty_s else
                   'no_causal_candidate_frame' if index<0 else
                   'candidate_frame_too_old' if age>request.max_age_s else
                   'candidate_not_supported' if point is None or point.state not in allowed or point.position is None else None)
            error=dist(ref.position,point.position) if cause is None else None
            if error is not None:Contract.finite_tree(error);errors.append(error)
            rows.append({'reference_index':frame.index,'candidate_index':b.frames[index].index if index>=0 else None,
                'common_time_s':time,'candidate_age_s':age,'label':label,'eligible':is_eligible,
                'supported':cause is None,'cause':cause,'error_distance':error,
                'reference_state':ref.state if ref else None,'candidate_state':point.state if point else None})
    return {'schema_version':1,'line':'R09','request':request.model_dump(),'unit':a.units,
        'rows':rows,'coverage':{'eligible_points':eligible,'supported_points':len(errors),
        'supported_fraction':len(errors)/eligible if eligible else None},
        'mean_error_on_support':sum(errors)/len(errors) if errors else None,
        'max_error_on_support':max(errors) if errors else None,
        'limits':['Uses latest candidate at or before reference common time; never reads a future frame',
            'Clock mappings and coordinate frames are declared, not authenticated by comparison',
            'No best-fit scale, rotation, offset, temporal shift or label reassignment',
            'Error applies only on supported points; interpret coverage and clock uncertainty',
            'Inferred/held points require explicit opt-in; error is not ground-truth depth or physical accuracy']}
