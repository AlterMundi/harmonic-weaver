"""Explicit seed-to-label evaluation on manual, shared image-plane support."""
from typing import Literal
import numpy as np
from pydantic import Field,model_validator
from ..contracts import Contract
from .rope_annotations import Annotation
from .rope_flow_run import Request as FlowRequest
from .rope_flow_contract import Frame,validate_frames


class Snapshot(Contract):
    schema_version:Literal[1]
    line:Literal['R08']
    request:FlowRequest
    frames:list[Frame]=Field(min_length=2,max_length=120)
    limits:list[str]=Field(max_length=16)

    @model_validator(mode='after')
    def valid(self):
        validate_frames([f.model_dump() for f in self.frames],self.request)
        return self


class Request(Contract):
    reference:Annotation
    flow:Snapshot
    endpoint_seeds:dict[Literal['a','b'],int]=Field(min_length=1,max_length=2)

    @model_validator(mode='after')
    def valid(self):
        indices=list(self.endpoint_seeds.values())
        if len(set(indices))!=len(indices) or any(i<0 or i>=len(self.flow.request.seeds) for i in indices):raise ValueError('Distinct explicitly selected seed indices required')
        source=self.flow.request
        if (source.media_sha256,source.width_px,source.height_px)!=(self.reference.media_sha256,self.reference.width_px,self.reference.height_px):raise ValueError('Benchmark requires identical source and image dimensions')
        return self


def evaluate(request):
    request=Request.model_validate(request);source=request.flow.request
    frames={f.frame_index:f for f in request.flow.frames};rows=[]
    counts={'reference_endpoints':0,'eligible_endpoints':0,'supported_endpoints':0,
            'outside_window_endpoints':0,'seed_input_endpoints':0,'unselected_label_endpoints':0}
    errors=[]
    for reference in request.reference.frames:
        frame=frames.get(reference.frame_index)
        if frame is not None and abs(frame.time_s-reference.time_s)>1e-6:raise ValueError('Benchmark source clocks differ on shared frame')
        for label,point in reference.endpoints.items():
            counts['reference_endpoints']+=1
            seed=request.endpoint_seeds.get(label)
            exclusion=('outside_window' if frame is None else 'seed_input' if frame.frame_index==source.start_frame_index else 'label_not_selected' if seed is None else None)
            if exclusion:
                counts[{'outside_window':'outside_window_endpoints','seed_input':'seed_input_endpoints','label_not_selected':'unselected_label_endpoints'}[exclusion]]+=1
            else:counts['eligible_endpoints']+=1
            candidate=next((r for r in frame.rows if r.seed_index==seed),None) if frame is not None and seed is not None else None
            supported=exclusion is None and candidate is not None and candidate.state=='candidate' and candidate.point is not None
            dx=(candidate.point.x-point.x)*source.width_px if supported else None
            dy=(candidate.point.y-point.y)*source.height_px if supported else None
            error=float(np.hypot(dx,dy)) if supported else None
            if supported:counts['supported_endpoints']+=1;errors.append(error)
            rows.append({'frame_index':reference.frame_index,'time_s':reference.time_s,'label':label,
                         'seed_index':seed,'eligible':exclusion is None,'supported':supported,
                         'cause':exclusion or (None if supported else 'seed_has_no_candidate'),
                         'tracking_cause':candidate.cause if candidate is not None and not supported and exclusion is None else None,
                         'error_x_px':dx,'error_y_px':dy,'error_distance_px':error})
    counts['unsupported_eligible_endpoints']=counts['eligible_endpoints']-counts['supported_endpoints']
    counts['supported_fraction_of_eligible']=counts['supported_endpoints']/counts['eligible_endpoints'] if counts['eligible_endpoints'] else None
    return {'schema_version':1,'line':'R08','request':request.model_dump(),'rows':rows,'coverage':counts,
            'summary':{'mean_error_distance_px_on_supported':float(np.mean(errors)) if errors else None,
                       'max_error_distance_px_on_supported':max(errors) if errors else None},
            'limits':['Seed input frame is excluded from tracking error; it is supplied data, not prediction',
                      'Endpoint labels map to seeds only by explicit declaration; no nearest-point or label-swap optimization',
                      'Evaluate only annotated selected endpoints inside the frozen window; missing candidates are not zero errors',
                      'Mean/max apply to supported endpoints only; interpret together with eligible coverage',
                      'Optical tracking observes current images; these metrics do not measure forecasting or prove physical identity',
                      'Manual reference quality, source integrity and scientific human acceptance require independent evidence']}
