"""Affine clock fit from explicit paired anchors; no physical synchronization claim."""
import math
from pydantic import Field,model_validator
from ..contracts import Contract
from .spatial_observations import Clock


class Anchor(Contract):
    source_time_s:float=Field(ge=0)
    common_time_s:float


class Request(Contract):
    source_clock:str=Field(min_length=1,max_length=80)
    common_clock:str=Field(min_length=1,max_length=80)
    evidence_id:str=Field(min_length=1,max_length=160)
    anchor_uncertainty_s:float=Field(ge=0)
    anchors:list[Anchor]=Field(min_length=3,max_length=4096)

    @model_validator(mode='after')
    def ordered(self):
        if any(b.source_time_s<=a.source_time_s or b.common_time_s<=a.common_time_s for a,b in zip(self.anchors,self.anchors[1:])):
            raise ValueError('Clock anchors must increase strictly in both clocks')
        return self


def fit(request):
    request=Request.model_validate(request)
    x=[a.source_time_s for a in request.anchors];y=[a.common_time_s for a in request.anchors]
    # Shift first to avoid squaring large epoch timestamps.
    dx=[v-x[0] for v in x];dy=[v-y[0] for v in y]
    Contract.finite_tree([dx,dy])
    if max(abs(v) for v in dx+dy)>1e150:raise ValueError('Clock span exceeds numeric fit budget')
    mx=math.fsum(dx)/len(dx);my=math.fsum(dy)/len(dy)
    denominator=math.fsum((v-mx)**2 for v in dx)
    if not denominator or not math.isfinite(denominator):raise ValueError('Clock anchors have insufficient finite span')
    rate=math.fsum((a-mx)*(b-my) for a,b in zip(dx,dy))/denominator
    offset=y[0]+my-rate*(x[0]+mx)
    residuals=[b-(offset+rate*a) for a,b in zip(x,y)]
    maximum=max(abs(r) for r in residuals)
    clock=Clock(source_clock=request.source_clock,common_clock=request.common_clock,offset_s=offset,rate=rate,
        uncertainty_s=maximum+request.anchor_uncertainty_s,method='measured_sync',evidence_id=request.evidence_id)
    result={'schema_version':1,'line':'R09','request':request.model_dump(),'clock':clock.model_dump(),
        'residuals_s':residuals,'max_abs_residual_s':maximum,'rms_residual_s':math.sqrt(math.fsum(r*r for r in residuals)/len(residuals)),
        'source_interval_s':[x[0],x[-1]],'limits':[
            'Anchor pairs and evidence ID are caller declarations, not authenticated measurements',
            'Fit uses all anchors; residuals are in-sample, not held-out accuracy',
            'Clock uncertainty is empirical maximum residual plus declared anchor uncertainty, not a statistical bound',
            'Outside anchor interval extrapolation is unvalidated; no automatic application to streams or live clocks']}
    Contract.finite_tree(result)
    return result
